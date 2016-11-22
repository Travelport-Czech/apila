from Task import Task
import os.path
import json

class JsonWrite(Task):
  """Write data into a JSON encoded file"""
  known_params = {
    'content': 'structure to be written into the file',
    'dest': 'full name of the target file'
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
      with open(self.params['dest']) as f:
        old_data = f.read()
      if old_data == data:
        return (True, '')
    try:
      open(self.params['dest'], 'w').write(data)
    except Exception as e:
      return (False, str(e))
    return (True, result)
