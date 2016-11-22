from Task import Task
import bototools
import botocore
import name_constructor
import uuid

class ApiResource(Task):
  """Create a resource and a method on Api Gateway"""
  known_params = {
    'api': 'name of the api',
    'path': 'name of the resource (path part of an url)',
    'method': 'supported HTTP method',
    'lambda': 'name of a function called to handle this endpoint',
    'authorizer': 'name of an authorizer (created by api-authorizer)'
  }
  required_params = ('api', 'path', 'method', 'lambda')
  required_configs = ('user', 'branch')
  task_name = 'api-resource'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Create a resource %s:%s method %s' % (self.params['api'], self.params['path'], self.params['method'])

  def run(self, clients, cache):
    api_name = name_constructor.api_name(self.params['api'], self.config['user'], self.config['branch'])
    lambda_name = name_constructor.lambda_name(self.params['lambda'], self.config['user'], self.config['branch'])
    lambda_params = bototools.get_lambda_params(clients.get('lambda'), cache, lambda_name, self.params['path'], self.params['method'])
    if lambda_params is None:
      return (False, "Lambda function '%s' not found" % lambda_name)
    lambda_arn = bototools.get_lambda_arn(lambda_params)
    path = self.params['path']
    client = clients.get('apigateway')
    api_id = bototools.get_cached_api_id_if_exists(client, cache, api_name)
    if api_id is None:
      return (False, "Api '%s' not found" % api_name)
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
    if method_integration['type'] != 'AWS_PROXY':
      return (False, "Method integration request must be of type 'AWS_PROXY', not '%s'" % method_integration['type'])
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
    patch = []
    if 'authorizer' in self.params:
      if method_info['authorizationType'] != 'CUSTOM':
        patch.append({'op': 'replace', 'path': '/authorizationType', 'value': 'CUSTOM'})
      authorizer = bototools.get_authorizer_by_name(client, api_id, self.params['authorizer']) 
      if 'authorizerId' not in method_info or method_info['authorizerId'] != authorizer['id']:
        patch.append({'op': 'replace', 'path': '/authorizerId', 'value': authorizer['id']})
    else:
      if method_info['authorizationType'] != 'NONE':
        patch.append({'op': 'replace', 'path': '/authorizationType', 'value': 'NONE'})
    if patch:
      client.update_method(restApiId=api_id, resourceId=path_id, httpMethod=self.params['method'], patchOperations=patch)
      result = self.CHANGED
    return (True, result)

  def get_permission_arn(self, api_id, lambda_params):
# "arn:aws:execute-api:{aws-region}:{aws-acct-id}:{aws-api-id}/*/POST/{lambda-function-name}"
    lambda_params['api_id'] = api_id
    return 'arn:aws:execute-api:%(region)s:%(acct_id)s:%(api_id)s/*/%(method)s%(path)s' % lambda_params

  def create_method(self, client, api_id, path_id, lambda_arn):
    if 'authorizer' in self.params:
      authorizer = bototools.get_authorizer_by_name(client, api_id, self.params['authorizer'])
      authorizer_id = authorizer['id']
      client.put_method(restApiId=api_id, resourceId=path_id, httpMethod=self.params['method'], authorizationType='CUSTOM', authorizerId=authorizer_id)
    else:
      client.put_method(restApiId=api_id, resourceId=path_id, httpMethod=self.params['method'], authorizationType='NONE')
    self.create_integration(client, api_id, path_id, lambda_arn)

  def create_integration(self, client, api_id, path_id, lambda_arn):
    client.put_integration(restApiId=api_id, resourceId=path_id, httpMethod=self.params['method'], type='AWS_PROXY', uri=lambda_arn, integrationHttpMethod=self.params['method'])
    
  def add_permission(self, client, lambda_name, permissions_arn, uuid):
    result = client.add_permission(FunctionName=lambda_name, StatementId=uuid, Action="lambda:InvokeFunction", Principal="apigateway.amazonaws.com", SourceArn=permissions_arn)
