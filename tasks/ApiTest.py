from Task import Task
import bototools
import name_constructor
import requests
import json

class ApiTest(Task):
  """Test api by simple request"""

  known_params = {
    'api': 'name of api',
    'path': 'path part of url on api',
    'method': 'HTTP method',
    'stage_name': 'api deploy stage',
    'request': 'sample payload for send to api',
    'response': 'expected part of response'
  }

  required_params = ('api', 'path', 'method', 'stage_name', 'request', 'response')
  required_configs = ('user', 'branch')
  task_name = 'api-test'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Test resource %s:%s method %s' % (self.params['api'], self.params['path'], self.params['method'])

  def run(self, clients, cache):
    api_name = name_constructor.api_name(self.params['api'], self.config['user'], self.config['branch'])
    path = self.params['path']
    method = self.params['method']
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
      'path': path
    }
    if method == 'POST':
      r = requests.post(url_to_test, data=self.params['request'])
    elif method == 'GET':
      r = requests.get(url_to_test, params=self.params['request'])
    else:
      return (False, 'Tested method must be POST or GET')
    response = r.json()
    match = self.dictMatch(self.params['response'], response)
    if match:
      return (True, '')
    else:
      return (False, 'Response %s not contain expected %s' % (str(response), self.params['response']))

  def dictMatch(self, patn, real):
    """does real dict match pattern?"""
    try:
        for pkey, pvalue in patn.iteritems():
            if type(pvalue) is dict:
                result = dictMatch(pvalue, real[pkey])
            else:
                assert real[pkey] == pvalue
                result = True
    except (AssertionError, KeyError):
        result = False
    return result
