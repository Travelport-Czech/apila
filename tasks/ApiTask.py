from Task import Task
import bototools

class ApiTask(Task):
  """Create api on API gateway"""
  known_params = {
    'name': 'name of api (will be concatenate with branch and user from config.yml)',
    'description': 'short human readable description of api'
  }
  required_params = ('name',)
  required_configs = ('user', 'branch')
  task_name = 'api'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Create api %s' % (self.params['description'] if 'description' in self.params else self.params['name'])

  def run(self, clients, cache):
    client = clients.get('apigateway')
    api_name = '%s_%s_%s' % (self.params['name'], self.config['branch'], self.config['user'])
    api_description = self.params['description'] if 'description' in self.params else None
    api = bototools.get_api_if_exists(client, api_name)
    result = ''
    if api is None:
      api = client.create_rest_api(name=api_name, description=api_description)
      result = self.CREATED
    elif api['description'] != api_description:
      client.update_rest_api(restApiId=api['id'], patchOperations=[{'op': 'replace', 'path': '/description', 'value': api_description}])
      result = self.CHANGED
    cache.put('api', api['name'], api['id'])
    return (True, result)

