from Task import Task
import os.path
import yaml
import time
import name_constructor

class DynamoDump(Task):
  """Dump a table to yaml"""
  known_params = {
    'name': 'name of the table to be dumped',
    'dest': 'full name of a target file'
  }
  required_params = ('name', 'dest')
  required_configs = ('user', 'branch')
  task_name = 'dynamo-dump'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return "Dump a table '%s' to '%s'" % (self.params['name'], os.path.abspath(self.params['dest']))

  def run(self, clients, cache):
    client = clients.get('dynamodb')
    table_name = name_constructor.table_name(self.params['name'], self.config)
    try:
      table_def = client.describe_table(TableName=table_name)['Table']
      retry = 60
      while table_def['TableStatus'] != 'ACTIVE':
        time.sleep(1)
        table_def = client.describe_table(TableName=table_name)['Table']
        retry -= 1
        if retry < 1:
          return (False, "Table is in state '%s' too long." % table_def['TableStatus'])
    except  Exception as e:
      return (False, str(e))
    struct = yaml.safe_dump(table_def)
    result = self.CREATED
    if os.path.exists(self.params['dest']):
      result = self.CHANGED
      old_struct = open(self.params['dest']).read()
      if old_struct == struct:
        result = ''
    open(self.params['dest'], 'w').write(struct)
    return (True, result)
