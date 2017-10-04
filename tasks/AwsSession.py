import bototools
import boto3
import sys

class AwsSession(object):
  def __init__(self, serial_number, secret_access_key, session_token, access_key_id):
    self.serial_number = serial_number
    self.secret_access_key = secret_access_key
    self.session_token = session_token
    self.access_key_id = access_key_id

  def validate(self):
    print "Trying connection to aws"
    if self.is_timed_session():
      apiclient = boto3.client('apigateway',
                               aws_access_key_id = self.access_key_id,
                               aws_secret_access_key = self.secret_access_key,
                               aws_session_token = self.session_token)
    else:
      apiclient = boto3.client('apigateway')
    if not bototools.is_api_request_available(apiclient):
      print "No active session"
      if not self.serial_number:
        self.serial_number = raw_input("Insert serial number: ")
      token_code = raw_input("Insert token code: ")
      client = boto3.client('sts')
      try:
        session_data = bototools.get_session(client, self.serial_number, token_code)
        self.secret_access_key = session_data["Credentials"]["SecretAccessKey"]
        self.session_token = session_data["Credentials"]["SessionToken"]
        self.access_key_id = session_data["Credentials"]["AccessKeyId"]
      except Exception:
        print "Session can't be established"
        sys.exit(2)

  def is_timed_session(self):
    return self.secret_access_key and self.session_token and self.access_key_id

  def get_data_dict(self):
    return {'serial_number': self.serial_number, 
            'secret_access_key': self.secret_access_key, 
            'session_token': self.session_token, 
            'access_key_id': self.access_key_id}
