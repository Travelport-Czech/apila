class Task:
  CHANGED = 'changed'
  CREATED = 'created'
  def __init__(self, name, params, config):
    self.name = name
    self.params = params
    self.config = config

  def validate(self, errors):
    for param in self.required_params:
      if param not in self.params:
        errors.append( "In task '%(name)s' %(context)s missing param '%(name)s.%(param)s'" % { 'name': self.task_name, 'param': param, 'context': str({'name': self.name, self.task_name: self.params}) })
    for conf in self.required_configs:
      if conf not in self.config:
        errors.append( "Task '%(name)s' need field '%(conf)s' in config.yml" % { 'name': self.task_name, 'conf': conf})
