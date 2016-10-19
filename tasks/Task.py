class Task(object):
  CHANGED = 'changed'
  CREATED = 'created'
  def __init__(self, name, params, config, register, when, tags, unknown_attributes):
    self.name = name
    self.params = params
    self.config = config
    self.unknown_attributes = unknown_attributes
    self.register = register
    self.when = when
    self.tags = tags

  def validate(self, errors):
    for param in self.unknown_attributes:
      errors.append( "In task '%(name)s' %(context)s unknown param %(param)s'" % { 'name': self.task_name, 'param': param, 'context': str({'name': self.name, self.task_name: self.params}) })

    for param in self.params:
      if param not in self.known_params:
        errors.append( "In task '%(name)s' %(context)s unknown param '%(name)s.%(param)s'" % { 'name': self.task_name, 'param': param, 'context': str({'name': self.name, self.task_name: self.params}) })

    for param in self.required_params:
      if param not in self.params:
        errors.append( "In task '%(name)s' %(context)s missing param '%(name)s.%(param)s'" % { 'name': self.task_name, 'param': param, 'context': str({'name': self.name, self.task_name: self.params}) })

    for conf in self.required_configs:
      if conf not in self.config:
        errors.append( "Task '%(name)s' need field '%(conf)s' in config.yml" % { 'name': self.task_name, 'conf': conf})

  def need_context(self):
    return False
