import botocore

def is_api_request_available(client):
  try:
    client.get_rest_apis(limit = 1)
    return True
  except Exception:
    return False

def get_api_if_exists(client, name):
  apis = client.get_rest_apis(limit=500)
  for api in apis['items']:
    if api['name'] == name:
      return api
  return None

def get_cached_api_id_if_exists(client, cache, api_name):
  api_id = cache.get('api', api_name)
  if api_id is None:
    api = get_api_if_exists(client, api_name)
    if not api:
      return None
    api_id = api['id']
    cache.put('api', api_name, api_id)
  return api_id

def get_resources_by_path(client, api_id):
  response = client.get_resources(restApiId=api_id)
  resources_by_path = { resource['path']: resource for resource in response['items'] }
  return resources_by_path

def create_resource_id_by_path(client, api_id, path, resources_by_path):
  path_parts = path.split('/')
  curr_path = ''
  for path_part in path_parts[1:]:
    last_path = curr_path
    curr_path += '/' + path_part
    if curr_path not in resources_by_path:
      parent = resources_by_path[last_path if last_path != '' else '/']
      new_resource = client.create_resource(restApiId=api_id, parentId=parent['id'], pathPart=path_part)
      resources_by_path[new_resource['path']] = new_resource
  return resources_by_path[path]['id']

def get_role_arn(client, role_name):
  roles = client.list_roles(MaxItems=500)['Roles']
  for role in roles:
    if role['RoleName'] == role_name:
      return role['Arn']
  return None
  
def get_lambda_params(client_lambda, cache, lambda_name, path, method):
  lambda_arn = cache.get('lambda', lambda_name)
  if lambda_arn is None:
    try:
      function_conf = client_lambda.get_function_configuration(FunctionName=lambda_name)
    except botocore.exceptions.ClientError:
      return None
    lambda_arn = function_conf['FunctionArn']
    cache.put('lambda', lambda_name, lambda_arn)
  parts = lambda_arn.split(':')
  return {
    'region': parts[3],
    'acct_id': parts[4],
    'version': client_lambda.meta.service_model.api_version,
    'lambda_arn': lambda_arn,
    'path': path,
    'method': method
  }

def get_lambda_arn(lambda_params):
# arn:aws:apigateway:eu-central-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-central-1:860303221267:function:main_srbt_afd_attemptEvaluate/invocations
# arn:aws:lambda:eu-central-1:860303221267:function:main_srbt_afd_attemptEvaluate
  lambda_uri = 'arn:aws:apigateway:%(region)s:lambda:path/%(version)s/functions/%(lambda_arn)s/invocations' % lambda_params
  return lambda_uri

def get_authorizer_by_name(client, api_id, authorizer_name):
  authorizers = filter(lambda item: item['name'] == authorizer_name, client.get_authorizers(restApiId=api_id)['items'])
  if authorizers:
    return authorizers[0]
  else:
    return None

def get_session(client, serial_number, token_code):
  return client.get_session_token(
    SerialNumber = serial_number,
    TokenCode = token_code
  )
