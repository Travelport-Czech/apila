from Task import Task
import os.path
import yaml
import botocore
import name_constructor
import time
import sys

class DynamoTable(Task):
  """Create table by yaml definition file"""
  known_params = {
    'name': 'name of table to create',
    'source': 'full name of file with definition (see demo/sample_reservation.yml)'
  }
  required_params = ( 'name', 'source' )
  required_configs = ('user', 'branch')
  task_name = 'dynamo-table'

  def __str__(self):
    if self.name:
      return self.name
    else:
      return "Create table '%s' from '%s'" % (self.params['name'], os.path.abspath(self.params['source']))

  def run(self, clients, cache):
    client = clients.get('dynamodb')
    try:
      new_def = yaml.load(open(self.params['source']).read())
    except Exception as e:
      return (False, str(e))
    table_name = name_constructor.table_name(self.params['name'], self.config)
    try:
      table_def = client.describe_table(TableName=table_name)['Table']
    except botocore.exceptions.ClientError as e:
      return self.create(client, table_name, new_def)
    request = self.build_update_request(table_def, new_def)
    if not request:
      return (True, '')
    self.process_update_request(client, request, table_name)
    return (True, self.CHANGED)

  def process_update_request(self, client, request, table_name):
    if 'GlobalSecondaryIndexUpdates' in request:
      for index_request in request['GlobalSecondaryIndexUpdates']:
        new_request = { 'TableName': table_name, 'AttributeDefinitions': request['AttributeDefinitions'], 'GlobalSecondaryIndexUpdates': [index_request]}
        self.modify_table(client, new_request, table_name)
    if 'ProvisionedThroughput' in request:
      new_request = { 'TableName': table_name, 'ProvisionedThroughput': request['ProvisionedThroughput'] }
      self.modify_table(client, new_request, table_name)

  def modify_table(self, client, request, table_name):
    def rotate(t):
#      animation = ('|', '\\', '-', '/')
      animation = (':.. ', '.:. ', '..: ', '.:. ')
      sys.stdout.write('\b'*len(animation)+animation[t % len(animation)])
      sys.stdout.flush()

    retry = 600
    sys.stdout.write('\r')
    while True:
      table_def = client.describe_table(TableName=table_name)['Table']
      busy_reason = self.table_busy_reason(table_def)
      if busy_reason == '':
        break
      retry -= 1
      if retry < 1:
        raise Exception("%s too long." % busy_reason)
      rotate(retry)
      time.sleep(1)
    client.update_table(**request)

  def table_busy_reason(self, table_def):
    if table_def['TableStatus'] != 'ACTIVE':
      return 'Table is in state %s' % table_def['TableStatus']
    if 'GlobalSecondaryIndexes' in table_def:
      for index in table_def['GlobalSecondaryIndexes']:
        if index['IndexStatus'] != 'ACTIVE':
          return 'Index %s is in state %s' % (index['IndexName'], index['IndexStatus'])
    return ''

  def build_update_request(self, table_def, new_def):
    request = {}
    old_indexes = self.get_indexes_by_name(self.construct_secondary_indexes(table_def['GlobalSecondaryIndexes']))
    new_indexes = self.get_indexes_by_name(self.construct_secondary_indexes(new_def['GlobalSecondaryIndexes']))
    updates = []
    for index_name in old_indexes:
      if index_name not in new_indexes:
        updates.append({ 'Delete': { 'IndexName': index_name }})
    for (index_name, index) in new_indexes.iteritems():
      if index_name in old_indexes:
        if index != old_indexes[index_name]:
          updates.append({ 'Delete': { 'IndexName': index_name }})
          updates.append({ 'Create': index})
      else:
        updates.append({ 'Create': index})
    if updates:
      request['GlobalSecondaryIndexUpdates'] = updates
      request['AttributeDefinitions'] = new_def['AttributeDefinitions']
    old_provisioning = self.construct_provisioned_throughput(table_def['ProvisionedThroughput'])
    new_provisioning = self.construct_provisioned_throughput(new_def['ProvisionedThroughput'])
    if old_provisioning != new_provisioning:
      request['ProvisionedThroughput'] = new_provisioning
    return request
          

  def get_indexes_by_name(self, indexes):
    out = {}
    for index in indexes:
      out[index['IndexName']] = index
    return out

  def construct_provisioned_throughput(self, idef):
    return {
        'ReadCapacityUnits': idef['ReadCapacityUnits'],
        'WriteCapacityUnits': idef['WriteCapacityUnits']
    }

  def construct_secondary_indexes(self, idefs):
    outs = []
    for idef in idefs:
      out = {
          'IndexName': idef['IndexName'],
          'KeySchema': idef['KeySchema'],
          'Projection': idef['Projection']
      }
      if 'ProvisionedThroughput' in idef:
        out['ProvisionedThroughput'] = self.construct_provisioned_throughput(idef['ProvisionedThroughput'])
      outs.append(out)
    return outs

  def create(self, client, table_name, new_def):
    params = {
        'AttributeDefinitions': new_def['AttributeDefinitions'],
        'TableName': table_name,
        'KeySchema': new_def['KeySchema'] if 'KeySchema' in new_def else [],
        'ProvisionedThroughput': self.construct_provisioned_throughput(new_def['ProvisionedThroughput'])
    }
    if 'LocalSecondaryIndexes' in new_def:
      params['LocalSecondaryIndexes'] = self.construct_secondary_indexes(new_def['LocalSecondaryIndexes'])
    if 'GlobalSecondaryIndexes' in new_def:
      params['GlobalSecondaryIndexes'] = self.construct_secondary_indexes(new_def['GlobalSecondaryIndexes'])
    if 'StreamSpecification' in new_def:
      params['StreamSpecification'] = new_def['StreamSpecification']
    try:
      client.create_table(**params)
    except  botocore.exceptions.ClientError as e:
      return (False, str(e))
    return (True, self.CREATED)
