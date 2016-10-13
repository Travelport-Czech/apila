import ApiTask
import ApiResource
import ApiDeploy
import Lambda
import UnknownTask
import boto3

known_tasks = {
  'api': ApiTask.ApiTask,
  'api-resource': ApiResource.ApiResource,
  'api-deploy': ApiDeploy.ApiDeploy,
  'lambda': Lambda.Lambda
}

def create_task(task_def, config):
  name = None
  task = None
  for attr, value in task_def.iteritems():
    if attr == 'name':
      name = value
    elif attr in known_tasks:
      task = attr
  if not task:
    return UnknownTask.UnknownTask(name, task_def, config)
  return known_tasks[task](name, task_def[task], config)

def print_doc():
  print "Known tasks:"
  for name, cls in known_tasks.iteritems():
    print '  %s: %s' % (name, cls.__doc__)
    for param, desc in cls.known_params.iteritems():
      print '   %s %-15s %s' % ('*' if param in cls.required_params else ' ', param+':', desc)
    print

class Clients:
  def __init__(self):
    self.cache = {}

  def get(self, name):
    if name not in self.cache:
      self.cache[name] = boto3.client(name)
    return self.cache[name]

class Cache:
  def __init__(self):
    self.cache = {}

  def put(self, section, id, value):
    if section not in self.cache:
      self.cache[section] = {}
    self.cache[section][id] = value

  def get(self, section, id):
    if section not in self.cache or id not in self.cache[section]:
      return None
    return self.cache[section][id]
