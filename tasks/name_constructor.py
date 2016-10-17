def lambda_name(name, user, branch):
  return '%s_%s_%s' % (branch, user, name)

def api_name(name, user, branch):
  return '%s_%s_%s' % (name, branch, user)

def table_name(name, user, branch):
  return '%s_%s_%s' % (branch, user, name)
