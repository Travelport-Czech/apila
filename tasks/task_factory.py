import ApiTask
import ApiResource
import ApiDeploy
import Lambda
import UnknownTask
import DoubleTask
import DynamoDump
import DynamoTable
import JsonWrite
import ApiTest
import Include
import name_constructor

known_tasks = {
  'api': ApiTask.ApiTask,
  'api-resource': ApiResource.ApiResource,
  'api-deploy': ApiDeploy.ApiDeploy,
  'lambda': Lambda.Lambda,
  'dynamo-dump': DynamoDump.DynamoDump,
  'dynamo-table': DynamoTable.DynamoTable,
  'json-write':  JsonWrite.JsonWrite,
  'api-test': ApiTest.ApiTest,
  'include': Include.Include
}

def get_yaml_tags_constructors(config):
  return {
       '!table_name': lambda loader, node: name_constructor.table_name(loader.construct_scalar(node), config['user'], config['branch']),
       '!api_name': lambda loader, node: name_constructor.api_name(loader.construct_scalar(node), config['user'], config['branch']),
       '!lambda_name': lambda loader, node: name_constructor.lambda_name(loader.construct_scalar(node), config['user'], config['branch'])
  }

def create_task(task_def, config):
  name = None
  task = None
  register = None
  when = None
  tags = None
  double_task = []
  unknown_attributes = []
  for attr, value in task_def.iteritems():
    if attr == 'name':
      name = value
    elif attr == 'register':
      if value:
        register = set(value)
    elif attr == 'when':
      if value:
        when = set(value)
    elif attr == 'tags':
      if value:
        tags = set(value)
    elif attr in known_tasks:
      if task:
        if not double_task:
          double_task.append(task)
        double_task.append(attr)
      task = attr
    else:
      unknown_attributes.append(attr)
  if len(double_task):
    return DoubleTask.DoubleTask(task_def, double_task, unknown_attributes)
  if not task:
    return UnknownTask.UnknownTask(task_def, unknown_attributes)
  return known_tasks[task](name, task_def[task], config, register, when, tags, unknown_attributes)


