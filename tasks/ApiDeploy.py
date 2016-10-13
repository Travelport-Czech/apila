from Task import Task
import bototools

class ApiDeploy(Task):
  """Deploy api to given stage"""
  known_params = {
    'api': 'name of api to deploy',
    'stage_name': 'target stage'
  }
  required_params = ('api', 'stage_name')
  required_configs = ('user', 'branch')
  task_name = 'api-deploy'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Deploy api %s to stage %s' % (self.params['api'], self.params['stage_name'])

  def run(self, clients, cache):
    api_name = '%s_%s_%s' % (self.params['api'], self.config['branch'], self.config['user'])
    client = clients.get('apigateway')
    api_id = cache.get('api', api_name)
    if api_id is None:
      api = bototools.get_api_if_exists(client, api_name)
      if api is None:
        return (False, "Api '%s' not found" % api_name)
      api_id = api['id']
      cache.put('api', api_name, api_id)
    response = client.get_deployments(restApiId=api_id)
    response = client.create_deployment(restApiId=api_id, stageName=self.params['stage_name'])
    return (True, '')
