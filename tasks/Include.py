from Task import Task
import yaml
import task_factory
import task_runner

class Include(Task):
  """Include tasks from a given tasklist file"""
  known_params = {
    'source': 'filename of the tasklist'
  }
  required_params = ('source',)
  required_configs = tuple()
  task_name = 'include'

  def __init__(self, name, params, config, register, when, tags, unknown_attributes):
    super(Include, self).__init__(name, params, config, register, when, tags, unknown_attributes)
    self.tasks = None

  def validate(self, errors):
    super(Include, self).validate(errors)
    if 'source' in self.params:
      self.load_tasks(self.params['source'])
    if self.tasks:
      for task in self.tasks:
        task.validate(errors)

  def __str__(self):
    if self.name:
      return self.name
    else:
      return 'Processing of %s' % self.params['source']

  def need_context(self):
    return True

  def set_context(self, registered, tags):
    self.ctx_registered = registered
    self.ctx_tags = tags

  def  run(self, clients, cache):
    self.load_tasks(self.params['source'])
    task_runner.sync_print('\r%sinclude (begin)%s\n' % (task_runner.color.CYAN + task_runner.color.BOLD, task_runner.color.END))
    task_runner.run_tasks(self.tasks, clients, cache, self.ctx_registered, self.ctx_tags)
    task_runner.print_task_label(self)
    task_runner.sync_print('\r%ssuccess (end)%s' % (task_runner.color.CYAN + task_runner.color.BOLD, task_runner.color.END))
    return ('True', '')

  def load_tasks(self, filename):
    if self.tasks is None:
      self.tasks = []
      for task_def in yaml.load(open(filename).read()):
        self.tasks.append(task_factory.create_task(task_def, self.config))

