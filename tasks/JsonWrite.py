from Task import Task
import os.path
import json

class JsonWrite(Task):
  """Write data into JSON encoded file"""
  known_params = {
    'content': 'structure to write into file',
    'dest': 'full name of target file'
  }
  required_params = ('content', 'dest')
  required_configs = ('user', 'branch')
  task_name = 'json-write'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return "Write given data to '%s'" % os.path.abspath(self.params['dest'])

  def run(self, clients, cache):
    content = self.params['content']
    data = json.dumps(content, sort_keys=True, indent=4, separators=(',', ': '))
    result = self.CREATED
    if os.path.exists(self.params['dest']):
      result = self.CHANGED
      old_data = open(self.params['dest']).read()
      if old_data == data:
        result = ''
    try:
      open(self.params['dest'], 'w').write(data)
    except Exception as e:
      return (False, str(e))
    return (True, result)