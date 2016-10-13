def get_api_if_exists(client, name):
  apis = client.get_rest_apis(limit=500)
  for api in apis['items']:
    if api['name'] == name:
      return api
  return None


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
  
