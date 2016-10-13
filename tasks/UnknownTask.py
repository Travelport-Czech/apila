from Task import Task

class UnknownTask(Task):
  def validate(self, errors):
    errors.append('Unknown command in def %s.' % str(self.params))

  def __str__(self):
    return 'Unknown command in def %s.' % str(self.params)

