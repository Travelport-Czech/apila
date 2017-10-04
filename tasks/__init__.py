import boto3
import AwsSession
from task_factory import known_tasks, get_yaml_tags_constructors, create_task

def print_doc():
  print "Known tasks"
  print "-----------"
  for name, cls in sorted(known_tasks.iteritems()):
    print '\n%s: %s' % (name, cls.__doc__)
    print '\n| %-15s |required|description' % ('parameter',)
    print   '|%s|--------|-----------' % (17*'-',)
    for param, desc in sorted(cls.known_params.iteritems()):
      print '| %-15s | %s    | %s' % (param, 'yes' if param in cls.required_params else 'no ', desc)
    print
  print """
Functions in tasks
------------------
Value of any attribute can be simple function call (all attribute, not part). I.e.:'

    - name: !function function_parameter

known functions are:
"""
  for tag_name, (tag_fce, tag_desc) in sorted(get_yaml_tags_constructors({}).iteritems()):
    print ' - %s: %s' % (tag_name, tag_desc)
  print

class Clients:
  def __init__(self, aws_session):
    self.cache = {}
    self.aws_session = aws_session

  def get(self, name):
    if name not in self.cache:
      if self.aws_session.is_timed_session():
        self.cache[name] = boto3.client(name, 
                                        aws_access_key_id = self.aws_session.access_key_id,
                                        aws_secret_access_key = self.aws_session.secret_access_key,
                                        aws_session_token = self.aws_session.session_token)
      else:
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
