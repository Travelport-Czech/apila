from Task import Task
import os.path
import yaml

class DynamoDump(Task):
  """Dump table to yaml"""
  known_params = {
    'table_name': 'name of table to dump',
    'dest': 'full name of target file'
  }
  required_params = ('table_name', 'dest')
  required_configs = tuple()
  task_name = 'dynamo-dump'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return "Dump table '%s' to '%s'" % (self.params['table_name'], os.path.abspath(self.params['dest']))

  def run(self, clients, cache):
    client = clients.get('dynamodb')
    struct = yaml.safe_dump(client.describe_table(TableName=self.params['table_name'])['Table'])
    result = self.CREATED
    if os.path.exists(self.params['dest']):
      result = self.CHANGED
      old_struct = open(self.params['dest']).read()
      if old_struct == struct:
        result = ''
    open(self.params['dest'], 'w').write(struct)
    return (True, result)
