from Task import Task
import bototools
import name_constructor
import uuid

class ApiAuthorizer(Task):
  """Create an authorizer for given api"""
  known_params = {
    'api': 'name of the api to deploy',
    'name': 'name of the authorizer',
    'lambda': 'name of the "gatekeeper" lambda function',
    'cache_ttl': 'cache results of authorization for given number of seconds (default is no cache)'
  }
  required_params = ('api', 'name', 'lambda')
  required_configs = ('user', 'branch')
  task_name = 'api-authorizer'

  def __str__(self):
      if self.name:
        return self.name
      else:
        return 'Create an authorizer %s for api %s via %s' % (self.params['name'], self.params['api'], self.params['lambda'])

  def run(self, clients, cache):
      api_name = name_constructor.api_name(self.params['api'], self.config['user'], self.config['branch'])
      lambda_name = name_constructor.lambda_name(self.params['lambda'], self.config['user'], self.config['branch'])
      authorizer_name = self.params['name']
      cache_ttl = int(self.params['cache_ttl']) if 'cache_ttl' in self.params else 0
      client = clients.get('apigateway')
      lambda_client = clients.get('lambda')
      api_id = bototools.get_cached_api_id_if_exists(client, cache, api_name)
      if api_id is None:
        return (False, "Api '%s' not found" % api_name)
      lambda_params = bototools.get_lambda_params(clients.get('lambda'), cache, lambda_name, '', '')
      if not lambda_params:
        return (False, "Lambda function '%s' not found" % lambda_name)
      lambda_arn = bototools.get_lambda_arn(lambda_params)
      authorizer = bototools.get_authorizer_by_name(client, api_id, authorizer_name)
      if not authorizer:
        self.create(client, api_id, authorizer_name, lambda_arn, cache_ttl)
        permissions_arn = self.get_permission_arn(api_id, lambda_params)
        self.add_permission(lambda_client, lambda_name, permissions_arn, uuid.uuid4().hex)
        return (True, self.CREATED)
      patch = []
      if authorizer['authorizerResultTtlInSeconds'] != cache_ttl:
        patch.append({'op': 'replace', 'path': '/authorizerResultTtlInSeconds', 'value': str(cache_ttl)})
      if authorizer['type'].lower() != 'token':
        patch.append({'op': 'replace', 'path': '/type', 'value': 'TOKEN'})
      if authorizer['authorizerUri'] != lambda_arn:
        patch.append({'op': 'replace', 'path': '/authorizerUri', 'value': lambda_arn})
      if patch:
        client.update_authorizer(restApiId=api_id, authorizerId=authorizer['id'], patchOperations=patch)
        return (True, self.CHANGED)
      return (True, '')

  def create(self, client, api_id, authorizer_name, lambda_arn, cache_ttl):
    client.create_authorizer(restApiId=api_id, name=authorizer_name, type='TOKEN', authorizerUri=lambda_arn, identitySource='method.request.header.Authorization',  authorizerResultTtlInSeconds=cache_ttl)

  def get_permission_arn(self, api_id, lambda_params):
    lambda_params['api_id'] = api_id
    return 'arn:aws:execute-api:%(region)s:%(acct_id)s:%(api_id)s/*' % lambda_params

  def add_permission(self, client, lambda_name, permissions_arn, uuid):
    result = client.add_permission(FunctionName=lambda_name, StatementId=uuid, Action="lambda:InvokeFunction", Principal="apigateway.amazonaws.com", SourceArn=permissions_arn)
