#!/usr/bin/env python

import yaml
import tasks
import sys
import argparse
import os

class color:
  PURPLE = '\033[95m'
  CYAN = '\033[96m'
  DARKCYAN = '\033[36m'
  BLUE = '\033[94m'
  GREEN = '\033[92m'
  YELLOW = '\033[93m'
  RED = '\033[91m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'
  END = '\033[0m'

def clear_todo():
  if os.path.exists('todo.yml'):
    os.unlink('todo.yml')

parser = argparse.ArgumentParser(description='Setup AWS services by settings given by sequence of tasks.')
parser.add_argument('-d', '--doc', help='show known commands and exit.', action='store_true')
parser.add_argument('--syntax-check', help='perform a syntax check on the playbook, but do not execute it', action='store_true')
parser.add_argument('-r', '--register', help='explicitly register events to do (can be used more times)', action='append')
parser.add_argument('path', help='path to folder with settings.')
args = parser.parse_args()

if args.doc:
  tasks.print_doc()
  sys.exit(0)

os.chdir(args.path)

print "Processing content of %s ..." % os.getcwd()
config = yaml.load(open('config.yml').read())
receipt = yaml.load(open('tasks.yml').read())

if os.path.exists('todo.yml'):
  todo = set(yaml.load(open('todo.yml').read()))
else:
  todo = set()

if args.register:
  todo.update(args.register)

task_list = [tasks.create_task(task_def, config) for task_def in receipt]

errors = []
for task in task_list:
  task.validate(errors)

if len(errors) > 0:
  print 'Script contains some error:\n  %s' % '\n  '.join(errors)
  sys.exit(1)

if args.syntax_check:
  print 'Syntax of %d tasks ok.' % len(task_list)
  sys.exit(0)

cache = tasks.Cache()
clients = tasks.Clients()
registered = todo

for task in task_list:
  print '...', ' '*15, str(task), ' ',
  if not task.when or task.when.intersection(registered):
    (ok, message) = task.run(clients, cache)
    if ok:
      if message:
        if task.register:
          registered.update(task.register)
        print '\r%ssuccess (%s)%s' % (color.BLUE + color.BOLD, message, color.END)
      else:
        print '\r%ssuccess%s' % (color.GREEN + color.BOLD, color.END)
    else:
      print '\r%sfailed\njob failed with message "%s"!%s' % (color.RED + color.BOLD, message, color.END)
      if registered:
        open('todo.yml', 'w').write('# registered events after last fail\n'+yaml.dump(list(registered)))
      else:
        clear_todo()
      sys.exit(1)
  else:
    print '\r%sskiped%s' % (color.YELLOW + color.BOLD, color.END)

clear_todo()
