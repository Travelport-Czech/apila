from Task import Task
import bototools
import name_constructor

class ApiDeploy(Task):
  """Deploy an api to given stage"""
  known_params = {
    'api': 'name of the api to deploy',
    'stage_name': 'name of the stage'
  }
  required_params = ('api', 'stage_name')
  required_configs = ('user', 'branch')
  task_name = 'api-deploy'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Deploy an api %s to stage %s' % (self.params['api'], self.params['stage_name'])

  def run(self, clients, cache):
    api_name = name_constructor.api_name(self.params['api'], self.config['user'], self.config['branch'])
    client = clients.get('apigateway')
    api_id = bototools.get_cached_api_id_if_exists(client, cache, api_name)
    if api_id is None:
      return (False, "Api '%s' not found" % api_name)
    response = client.get_deployments(restApiId=api_id)
    response = client.create_deployment(restApiId=api_id, stageName=self.params['stage_name'])
    return (True, '')
