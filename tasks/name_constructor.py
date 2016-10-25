def lambda_name(name, user, branch):
  return '%s_%s_%s' % (branch, user, name)

def api_name(name, user, branch):
  return '%s_%s_%s' % (name, branch, user)

def table_name(name, config):
  branch = config['dynamodb']['branch'] if 'dynamodb' in config and 'branch' in config['dynamodb'] else config['branch']
  user = config['dynamodb']['user'] if 'dynamodb' in config and 'user' in config['dynamodb'] else config['user']
  return '%s_%s_%s' % (branch, user, name)
