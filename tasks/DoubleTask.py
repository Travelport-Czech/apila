from Task import Task

class DoubleTask(Task):

  def __init__(self, params, double_task, unknown_attributes):
    self.params = params
    self.double_task = double_task
    self.unknown_attributes = unknown_attributes

  def validate(self, errors):
    errors.append('Double command (%s) in def %s.' % (', '.join(self.double_task), str(self.params)))

  def __str__(self):
    return 'Double command in def %s.' % str(self.params)

