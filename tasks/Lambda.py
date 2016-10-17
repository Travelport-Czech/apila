from Task import Task
import bototools
import zipfile
import tempfile
import os
import os.path
import hashlib
import base64
import botocore
import json
import name_constructor

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
    'publish': "I'm not sure, give always True ;-)"
  }
  required_params = ('name', 'code', 'role', 'runtime', 'handler')
  required_configs = ('user', 'branch')
  task_name = 'lambda'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Create lambda function %s' % (self.params['description'] if 'description' in self.params else self.params['name'])

  def get_files(self, path):
    out = []
    for root, dirs, files in os.walk(path):
      rel_root = root[len(path):].lstrip('/')
      for filename in files:
        out.append((os.path.join(root, filename), os.path.join(rel_root, filename)))
    return sorted(out)

  def create_zip(self, files):
    zip_name = tempfile.mkstemp(suffix='.zip', prefix='lambda_')[1]
    with zipfile.ZipFile(zip_name, 'w') as myzip:
      for filedef in files:
        myzip.write(filedef[0], filedef[1])
    zip_data = open(zip_name, 'rb').read()
    os.unlink(zip_name)
    return zip_data

  def get_project_files(self, base_path):
    files = self.get_files(os.path.join(base_path, 'app'))
    package_conf = json.loads(open(os.path.join(base_path, 'package.json')).read())
    for dependency in sorted(package_conf['dependencies'].keys()):
      dep_path = os.path.join('node_modules', dependency)
      this_dep_files = map(lambda x: (x[0], os.path.join(dep_path, x[1])), self.get_files(os.path.join(base_path, dep_path)))
      files.extend(this_dep_files)
    return files

  def run(self, clients, cache):
    client = clients.get('lambda')
    iam_client = clients.get('iam')
    function_name = name_constructor.lambda_name(self.params['name'], self.config['user'], self.config['branch'])
    role_arn = bototools.get_role_arn(iam_client, self.params['role'])
    try:
      zip_data = self.create_zip(self.get_project_files(self.params['code']))
    except Exception as e:
      return (False, str(e))
    if role_arn is None:
      return (False, "Required role '%s' not found" % self.params['role'])
    try:
      function_conf = client.get_function_configuration(FunctionName=function_name)
    except botocore.exceptions.ClientError:
      return self.create(client, cache, function_name, role_arn, zip_data)
    if role_arn == function_conf['Role'] and \
      self.params['runtime'] == function_conf['Runtime'] and \
      self.params['handler'] == function_conf['Handler'] and \
      ('description' not in self.params or self.params['description'] == function_conf['Description']) and \
      ('timeout' not in self.params or self.params['timeout'] == function_conf['Timeout']) and \
      ('memory_size' not in self.params or self.params['memory_size'] == function_conf['MemorySize']):
        result = ''
    else:
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

  def create(self, client, cache, function_name, role_arn, zip_data):
    response = client.create_function(
      FunctionName=function_name,
      Runtime=self.params['runtime'],
      Role=role_arn,
      Handler=self.params['handler'],
      Code={ 'ZipFile': zip_data },
      Description=self.params['description'] if 'description' in self.params else None,
      Timeout=self.params['timeout'] if 'timeout' in self.params else None,
      MemorySize=self.params['memory_size'] if 'memory_size' in self.params else None,
      Publish=self.params['publish'] if 'publish' in self.params else None
    )
    cache.put('lambda', function_name, response['FunctionArn'])
    return (True, self.CREATED)
