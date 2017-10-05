from Task import Task
import bototools
import name_constructor
import requests
import json

class ApiTest(Task):
  """Test an api by simple request"""

  known_params = {
    'api': 'name of the api',
    'path': 'the path part of url on the api',
    'placeholders': 'placeholders in path',
    'method': 'used HTTP method',
    'stage_name': 'name of the stage',
    'request': 'sample of payload to be send',
    'authorization': 'an authorization token (if request must be authorized)',
    'response': 'expected part of the response'
  }

  required_params = ('api', 'path', 'method', 'stage_name', 'request', 'response')
  required_configs = ('user', 'branch')
  task_name = 'api-test'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Test a resource %s:%s method %s' % (self.params['api'], self.params['path'], self.params['method'])

  def run(self, clients, cache):
    api_name = name_constructor.api_name(self.params['api'], self.config['user'], self.config['branch'])
    path = self.params['path']
    method = self.params['method']
    placeholders = self.params.get('placeholders', {})
    client = clients.get('apigateway')
    api_id = bototools.get_cached_api_id_if_exists(client, cache, api_name)
    if api_id is None:
      return (False, "Api '%s' not found" % api_name)
    resources_by_path = bototools.get_resources_by_path(client, api_id)
    if path not in resources_by_path:
      return (False, "Path '%s' not found in api %s" % (path, api_name))
    path_id = resources_by_path[path]['id']
    method_info = client.get_method(restApiId=api_id, resourceId=path_id, httpMethod=method)
# arn:aws:apigateway:eu-central-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-central-1:860303221267:function:main_srb_afd_attemptEvaluate/invocations
    method_uri = method_info['methodIntegration']['uri']
    region = method_uri.split(':')[3]
    url_to_test = 'https://%(api_id)s.execute-api.%(region)s.amazonaws.com/%(stage)s%(path)s' % {
      'api_id': api_id,
      'region': region,
      'stage': self.params['stage_name'],
      'path': path.format(**placeholders)
    }
    headers = {}
    if 'authorization' in self.params:
      headers['Authorization'] = self.params['authorization']
    if method == 'POST':
      r = requests.post(url_to_test, data=self.params['request'], headers=headers)
    elif method == 'GET':
      r = requests.get(url_to_test, params=self.params['request'], headers=headers)
    else:
      return (False, 'Tested method must be POST or GET')
    response = r.json()
    match = self.anyMatch(self.params['response'], response)
    if match:
      return (True, '')
    else:
      return (False, 'Response %s not contain expected %s' % (str(response), self.params['response']))

  def anyMatch(self, patn, real):
    if type(patn) == dict and type(real) == dict:
        return self.dictMatch(patn, real)
    elif type(patn) == list and type(real) == list:
        return self.listMatch(patn, real)
    else:
        return str(patn) == str(real)

  def listMatch(self, patn, real):
    for patn_item in patn:
        found = False
        for real_item in real:
            if self.anyMatch(patn_item, real_item):
                found = True
        if not found:
            return False
    return True

  def dictMatch(self, patn, real):
    for pkey, pvalue in patn.iteritems():
        if pkey not in real or not self.anyMatch(pvalue, real[pkey]):
            return False
    return True
