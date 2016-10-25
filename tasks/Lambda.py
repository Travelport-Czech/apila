from Task import Task
import bototools
import zipfile
import tempfile
import shutil
import os
import os.path
import hashlib
import base64
import botocore
import json
import name_constructor
import logging
import subprocess
import re

class Lambda(Task):
  """Create lambda function a upload code from given folder"""
  known_params = {
    'name': 'function name',
    'code': "path to folder with function's source code",
    'role': 'name of role for run of function',
    'runtime': "name and version of interpret for run i.e.: 'nodejs4.3'",
    'handler': 'entrypoint to function code',
    'description': 'short description about function',
    'timeout': 'max time to run code',
    'memory_size': 'amount memory reserved for run',
    'publish': "I'm not sure, give always True ;-)",
    'babelize': "source must be convert by babel (default True)",
    'babelize_skip': "list of modules to skip by babel"
  }
  required_params = ('name', 'code', 'role', 'runtime', 'handler')
  required_configs = ('user', 'branch')
  task_name = 'lambda'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Create lambda function %s' % (self.params['description'] if 'description' in self.params else self.params['name'])

  def get_files(self, path, rel_part):
    out = []
    for root, dirs, files in os.walk(os.path.join(path, rel_part)):
      rel_root = root[len(path):].lstrip('/')
      for filename in files:
        out.append((os.path.join(root, filename), os.path.join(rel_root, filename)))
    return sorted(out)

  def create_zip(self, files):
    zip_name = tempfile.mkstemp(suffix='.zip', prefix='lambda_')[1]
    with zipfile.ZipFile(zip_name, 'w') as myzip:
      for filedef in files:
        os.utime(filedef[0], (946681200, 946681200)) # date '+%s' -d '2000-01-01'
        myzip.write(filedef[0], filedef[1])
    zip_data = open(zip_name, 'rb').read()
    os.unlink(zip_name)
    return zip_data

  def run_npm_install(self, path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
      npm_out = subprocess.check_output(['npm', 'install', '--production'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
      logging.error(e.output)
      raise e
    finally:
      os.chdir(cwd)

  def babelize(self, base_path, clean_dir, babelized_dir):
    cwd = os.getcwd()
    if os.path.exists('../node_modules/.bin/babel'):
      os.chdir('..')
    if not os.path.exists('node_modules/.bin/babel'):
      os.chdir(base_path)
    preset_base = os.getcwd()
    try:
      babel_out = subprocess.check_output(' '.join(['node_modules/.bin/babel', '--presets', os.path.join(preset_base, 'node_modules', 'babel-preset-es2015-node4'), '--copy-files', '--out-dir', babelized_dir, clean_dir]), stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
      logging.error(e.output)
      raise e
    finally:
      os.chdir(cwd)

  def clean_packages(self, files, path_to_remove):
    r_shasum = re.compile(r'"_shasum"[^,]+,')
    for filename, rel in files:
      if filename.endswith('package.json'):
        with open(filename) as fin:
          text = fin.read()
        new_text = r_shasum.sub('', text.replace(path_to_remove, '/tmp'))
        with open(filename, 'w') as fout:
          fout.write(new_text)

  def prepare_zipped_code(self, code_path, babelize):
    excluded_mods = self.params['babelize_skip'] if 'babelize_skip' in self.params else set()
    work_dir = tempfile.mkdtemp(prefix='lambda_')
    clean_dir = os.path.join(work_dir, 'clean')
    os.mkdir(clean_dir)
    shutil.copytree(os.path.join(code_path, 'app'), os.path.join(clean_dir, 'app'))
    shutil.copy(os.path.join(code_path, 'package.json'), os.path.join(clean_dir, 'package.json'))
    self.run_npm_install(clean_dir)
    if babelize:
      babelized_dir = os.path.join(work_dir, 'babelized')
      babelized_app_dir = os.path.join(babelized_dir, 'app')
      babelized_mod_dir = os.path.join(babelized_dir, 'node_modules')
      clean_mod_dir = os.path.join(clean_dir, 'node_modules')
      os.mkdir(babelized_dir)
      os.mkdir(babelized_app_dir)
      os.mkdir(babelized_mod_dir)
      self.babelize(code_path, os.path.join(clean_dir, 'app'), babelized_app_dir)
      for module_name in os.listdir(clean_mod_dir):
        src = os.path.join(clean_mod_dir, module_name)
        dest = os.path.join(babelized_mod_dir, module_name)
        if module_name in excluded_mods:
          shutil.copytree(src, dest)
        else:
          os.mkdir(dest)
          self.babelize(code_path, src, dest)
      files = self.get_files(babelized_app_dir, '') + self.get_files(babelized_dir, 'node_modules')
    else:
      files = self.get_files(os.path.join(clean_dir, 'app'), '') + self.get_files(clean_dir, 'node_modules')
    self.clean_packages(files, work_dir)
    zip_data = self.create_zip(files)
    shutil.rmtree(work_dir)
    return zip_data

  def run(self, clients, cache):
    client = clients.get('lambda')
    iam_client = clients.get('iam')
    function_name = name_constructor.lambda_name(self.params['name'], self.config['user'], self.config['branch'])
    role_arn = bototools.get_role_arn(iam_client, self.params['role'])
    description = (self.params['description'] if 'description' in self.params else '') + self.get_version_description()
    try:
      zip_data = self.prepare_zipped_code(self.params['code'], True if 'babelize' not in self.params else self.params['babelize'])
    except Exception as e:
      logging.exception(str(e))
      return (False, str(e))
    if role_arn is None:
      return (False, "Required role '%s' not found" % self.params['role'])
    try:
      function_conf = client.get_function_configuration(FunctionName=function_name)
    except botocore.exceptions.ClientError:
      return self.create(client, cache, function_name, role_arn, zip_data, description)
    if role_arn == function_conf['Role'] and \
      self.params['runtime'] == function_conf['Runtime'] and \
      self.params['handler'] == function_conf['Handler'] and \
      (description == function_conf['Description']) and \
      ('timeout' not in self.params or self.params['timeout'] == function_conf['Timeout']) and \
      ('memory_size' not in self.params or self.params['memory_size'] == function_conf['MemorySize']):
        result = ''
    else:
      self.update(client, function_name, role_arn, description)
      result = self.CHANGED
    sha256_sumator = hashlib.sha256()
    sha256_sumator.update(zip_data)
    sha256_sum = sha256_sumator.digest()
    sha256_sum_encoded = base64.b64encode(sha256_sum)
    if sha256_sum_encoded != function_conf['CodeSha256']:
      client.update_function_code(FunctionName=function_name, ZipFile=zip_data, Publish=self.params['publish'] if 'publish' in self.params else None)
      result = self.CHANGED
    cache.put('lambda', function_name, function_conf['FunctionArn'])
    return (True, result)

  def update(self, client, function_name, role_arn, description):
    lambda_def = {
      'FunctionName': function_name,
      'Runtime': self.params['runtime'],
      'Role': role_arn,
      'Handler': self.params['handler']
    }
    lambda_def['Description'] = description
    if 'timeout' in self.params:
      lambda_def['Timeout'] = self.params['timeout']
    if 'memory_size' in self.params:
      lambda_def['MemorySize'] = self.params['memory_size']
    client.update_function_configuration(**lambda_def)

  def create(self, client, cache, function_name, role_arn, zip_data, description):
    lambda_def = {
      'FunctionName': function_name,
      'Runtime': self.params['runtime'],
      'Role': role_arn,
      'Handler': self.params['handler'],
      'Code': { 'ZipFile': zip_data }
    }
    lambda_def['Description'] = description
    if 'timeout' in self.params:
      lambda_def['Timeout'] = self.params['timeout']
    if 'memory_size' in self.params:
      lambda_def['MemorySize'] = self.params['memory_size']
    if 'publish' in self.params:
      lambda_def['Publish'] = self.params['publish']
    response = client.create_function(**lambda_def)
    cache.put('lambda', function_name, response['FunctionArn'])
    return (True, self.CREATED)

  def get_version_description(self):
    manifest_path = os.path.join(self.params['code'], 'package.json')
    if os.path.exists(manifest_path):
      manifest = json.load(open(manifest_path))
      if 'version' in manifest:
        return ' (v%s)' % manifest['version']
    return ''
