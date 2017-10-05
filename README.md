Apila
=====

This tool executes sequence of AWS tasks. The sequence is loaded from a file in a given path. Default filename is tasks.yml.

You can find sample script in demo/tasks.yml.

One task can look like this:

    - name: Create something for any reason
      <task>:
        task_param: 'some value'
      tags:
        - tagname
      register:
        - thrown event
      when:
        - needed event
or you can use json syntax (it is compatible with yaml):

    [
        {
            "name": "Create something for any reason",
            "<task>": {
                "task_param": "some value"
            },
            "register": [
                "thrown event"
            ],
            "when": [
                "needed event"
            ],
            "tags": [
                "tagname"
            ]
        }
    ]
- attribute name can be used for description of goals and reasons for given task. It's optional. When missing, task will create the message.
- attribute <task> defines action what to do. Tasks can accept his own parameters (see list of known tasks bellow).
- attribute register is a list of events to emit if the task ends with result "created" or "changed"
- attribute when is a list of events for which the task is listening.
- attribute tags is a list of custom tags, you can set some tag at command line, only tasks containing this tag will be executed

Known tasks
-----------

api: Create an api on API gateway

| parameter       |required|description
|-----------------|--------|-----------
| description     | no     | short human readable description of the api
| name            | yes    | name of the api (will be concatenated with fields branch and user from config.yml)


api-authorizer: Create an authorizer for given api

| parameter       |required|description
|-----------------|--------|-----------
| api             | yes    | name of the api to deploy
| cache_ttl       | no     | cache results of authorization for given number of seconds (default is no cache)
| lambda          | yes    | name of the "gatekeeper" lambda function
| name            | yes    | name of the authorizer


api-deploy: Deploy an api to given stage

| parameter       |required|description
|-----------------|--------|-----------
| api             | yes    | name of the api to deploy
| stage_name      | yes    | name of the stage


api-resource: Create a resource and a method on Api Gateway

| parameter       |required|description
|-----------------|--------|-----------
| api             | yes    | name of the api
| authorizer      | no     | name of an authorizer (created by api-authorizer)
| lambda          | yes    | name of a function called to handle this endpoint
| method          | yes    | supported HTTP method
| path            | yes    | name of the resource (path part of an url)


api-test: Test an api by simple request

| parameter       |required|description
|-----------------|--------|-----------
| api             | yes    | name of the api
| authorization   | no     | an authorization token (if request must be authorized)
| method          | yes    | used HTTP method
| path            | yes    | the path part of url on the api
| placeholders    | no     | values for placeholders to be replaced in path
| query           | no     | query parameters to be added to url
| request         | yes    | sample of payload to be send
| response        | yes    | expected part of the response
| stage_name      | yes    | name of the stage


dynamo-dump: Dump a table to yaml

| parameter       |required|description
|-----------------|--------|-----------
| dest            | yes    | full name of a target file
| name            | yes    | name of the table to be dumped


dynamo-table: Create or remove a table by yaml definition file

| parameter       |required|description
|-----------------|--------|-----------
| name            | yes    | name of the table to be created or removed
| source          | yes    | full name of the file with the definition (see demo/sample_reservation.yml)
| state           | no     | table can be in two states: present (it is the default state) or absent


include: Include tasks from a given tasklist file

| parameter       |required|description
|-----------------|--------|-----------
| source          | yes    | filename of the tasklist


json-write: Write data into a JSON encoded file

| parameter       |required|description
|-----------------|--------|-----------
| content         | yes    | structure to be written into the file
| dest            | yes    | full name of the target file


lambda: Create a lambda function and upload the code from given folder

| parameter       |required|description
|-----------------|--------|-----------
| babelize        | no     | flag if the source must be converted by babel (default True)
| babelize_skip   | no     | list of modules to be skipped by babel
| code            | yes    | path to the folder with function's source code
| description     | no     | short description of the function
| handler         | yes    | entrypoint to the function code
| memory_size     | no     | amount of memory reserved for the execution of the function
| name            | yes    | function name
| publish         | no     | I'm not sure, give always True ;-)
| role            | yes    | name of a role for the execution of the function
| runtime         | yes    | name and a version of interpret for the execution i.e.: 'nodejs4.3'
| timeout         | no     | maximal time for the execution of the function


Functions in tasks
------------------
Value of any attribute can be simple function call (all attribute, not part). I.e.:'

    - name: !function function_parameter

known functions are:

 - !api_name: create an api name from given base name and config.yml
 - !config: return config value for given key
 - !lambda_name: create a lambda name from given base name and config.yml
 - !table_name: create a table name from given base name and config.yml
    (uses fields user and branch from dict dynamodb if present, else from root config)
 - !template: use given string as a template for rendering config.yml
    i.e.: "-name !template Super task for an user {user} on a branch {branch}"
    Don't use this to compose a lambda name, an api name etc - use defined functions for this!!!

Interpret usage
---------------
    usage: play [-h] [-V] [--doc] [--debug] [--syntax-check] [-r EVENT] [-u EVENT] [-t TAG] [-e file.yml] [-c file.yml] path
    
    Setup AWS services according to set sequence of tasks.
    
    positional arguments:
      path                  path to a folder with a AWS service setup file
    
    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         show program's version number and exit
      --doc                 show known commands and exit
      --debug               on crash show backtrace
      --syntax-check        perform a syntax check on the playbook, but don't execute it
      -r EVENT, --register EVENT
                            explicitly register an event for an execution (can be used more times)
      -u EVENT, --unregister EVENT
                            explicitly unregister an event from an actual execution. Actual execution is stored in todo.yml. (can be used more times)
      -t TAG, --tag TAG     execute only tasks with specified tag (can be used more times)
      -e file.yml, --exec file.yml
                            use an alternative filename to task.yml
      -c file.yml, --conf file.yml
                            use an alternative filename to config.yml
Dependencies
------------
 - python 2.7
 - python module yaml  ( apt-get install python-yaml )
 - python module boto3 ( apt-get install python-pip; pip install boto3 )
