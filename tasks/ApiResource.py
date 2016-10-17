from Task import Task
import bototools
import botocore
import name_constructor
import uuid

class ApiResource(Task):
  """Create resource and method on Api Gateway"""
  known_params = {
    'api': 'name of api',
    'path': 'path part of url on api',
    'method': 'HTTP method',
    'lambda': 'name of function called by acces to path on api'
  }
  required_params = ('api', 'path', 'method', 'lambda')
  required_configs = ('user', 'branch')
  task_name = 'api-resource'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Create resource %s:%s' % (self.params['api'], self.params['path'])

  def run(self, clients, cache):
    api_name = name_constructor.api_name(self.params['api'], self.config['user'], self.config['branch'])
    lambda_name = name_constructor.lambda_name(self.params['lambda'], self.config['user'], self.config['branch'])
    lambda_params = self.get_lambda_params(clients.get('lambda'), cache, lambda_name, self.params['path'], self.params['method'])
    lambda_arn = self.get_lambda_arn(lambda_params)
    if lambda_arn is None:
      return (False, "Lambda function '%s' not found" % lambda_name)
    path = self.params['path']
    client = clients.get('apigateway')
    api_id = cache.get('api', api_name)
    if api_id is None:
      api = bototools.get_api_if_exists(client, api_name)
      if api is None:
        return (False, "Api '%s' not found" % api_name)
      api_id = api['id']
      cache.put('api', api_name, api_id)
    result = ''
    resources_by_path = bototools.get_resources_by_path(client, api_id)
    if path in resources_by_path:
      path_id = resources_by_path[path]['id']
    else:
      path_id = bototools.create_resource_id_by_path(client, api_id, path, resources_by_path)
      result = self.CREATED
    cache.put('resource', api_name+':'+path, path_id)
    try:
      method_info = client.get_method(restApiId=api_id, resourceId=path_id, httpMethod=self.params['method'])
#{u'apiKeyRequired': False, u'httpMethod': u'POST', u'methodIntegration': {u'integrationResponses': {u'200': {u'responseTemplates': {u'application/json': None}, u'statusCode': u'200'}}, u'passthroughBehavior': u'WHEN_NO_MATCH', u'cacheKeyParameters': [], u'uri': u'arn:aws:apigateway:eu-central-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-central-1:860303221267:function:main_srbt_afd_attemptEvaluate/invocations', u'httpMethod': u'POST', u'cacheNamespace': u'ez205t', u'type': u'AWS'}, u'requestParameters': {}, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '7b577a6b-913a-11e6-afe9-53022ccbd313', 'HTTPHeaders': {'x-amzn-requestid': '7b577a6b-913a-11e6-afe9-53022ccbd313', 'date': 'Thu, 13 Oct 2016 11:45:04 GMT', 'content-length': '594', 'content-type': 'application/json'}}, u'methodResponses': {u'200': {u'responseModels': {u'application/json': u'Empty'}, u'statusCode': u'200'}}, u'authorizationType': u'NONE'}
    except botocore.exceptions.ClientError:
      permissions_arn = self.get_permission_arn(api_id, lambda_params)
      self.create_method(client, api_id, path_id, lambda_arn)
      self.add_permission(clients.get('lambda'), lambda_name, permissions_arn, uuid.uuid4().hex)
      return (True, self.CREATED)
    if 'methodIntegration' not in method_info:
      self.create_integration(client, api_id, path_id, lambda_arn)
      method_info['methodIntegration'] = client.get_integration(restApiId=api_id, resourceId=path_id, httpMethod=self.params['method'])
      result = self.CHANGED
    method_integration = method_info['methodIntegration']
    if method_integration['type'] != 'AWS':
      return (False, "Method integration request must be of type 'AWS', not '%s'" % method_integration['type'])
    if method_integration['uri'] != lambda_arn:
      client.update_integration(
        restApiId=api_id,
        resourceId=path_id,
        httpMethod=self.params['method'],
        patchOperations=[
          { 'op': 'replace', 'path': '/uri', 'value': lambda_arn }
        ]
      )
      result = self.CHANGED
    return (True, result)

  def get_lambda_params(self, client, cache, lambda_name, path, method):
    lambda_arn = cache.get('lambda', lambda_name)
    if lambda_arn is None:
      try:
        function_conf = client.get_function_configuration(FunctionName=lambda_name)
      except botocore.exceptions.ClientError:
        return None
      lambda_arn = function_conf['FunctionArn']
      cache.put('lambda', lambda_name, lambda_arn)
    parts = lambda_arn.split(':')
    return {
      'region': parts[3],
      'acct_id': parts[4],
      'version': client.meta.service_model.api_version,
      'lambda_arn': lambda_arn,
      'path': path,
      'method': method
    }

  def get_lambda_arn(self, lambda_params):
# arn:aws:apigateway:eu-central-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-central-1:860303221267:function:main_srbt_afd_attemptEvaluate/invocations
# arn:aws:lambda:eu-central-1:860303221267:function:main_srbt_afd_attemptEvaluate
    lambda_uri = 'arn:aws:apigateway:%(region)s:lambda:path/%(version)s/functions/%(lambda_arn)s/invocations' % lambda_params
    return lambda_uri

  def get_permission_arn(self, api_id, lambda_params):
# "arn:aws:execute-api:{aws-region}:{aws-acct-id}:{aws-api-id}/*/POST/{lambda-function-name}"
    lambda_params['api_id'] = api_id
    return 'arn:aws:execute-api:%(region)s:%(acct_id)s:%(api_id)s/*/%(method)s%(path)s' % lambda_params

  def create_method(self, client, api_id, path_id, lambda_arn):
    client.put_method(restApiId=api_id, resourceId=path_id, httpMethod=self.params['method'], authorizationType='NONE')
    self.create_integration(client, api_id, path_id, lambda_arn)

  def create_integration(self, client, api_id, path_id, lambda_arn):
    client.put_integration(restApiId=api_id, resourceId=path_id, httpMethod=self.params['method'], type='AWS', uri=lambda_arn, integrationHttpMethod=self.params['method'])
    
  def add_permission(self, client, lambda_name, permissions_arn, uuid):
    result = client.add_permission(FunctionName=lambda_name, StatementId=uuid, Action="lambda:InvokeFunction", Principal="apigateway.amazonaws.com", SourceArn=permissions_arn)
