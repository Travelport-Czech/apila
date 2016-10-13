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

parser = argparse.ArgumentParser(description='Setup AWS services by settings given by sequence of tasks.')
parser.add_argument('-d', '--doc', help='show known commands and exit.', action='store_true')
parser.add_argument('--syntax-check', help='perform a syntax check on the playbook, but do not execute it', action='store_true')
parser.add_argument('path', help='path to folder with settings.', default=os.getcwd(), nargs='?')
args = parser.parse_args()

if args.doc:
  tasks.print_doc()
  sys.exit(0)

os.chdir(args.path)

print "Processing content of %s ..." % os.getcwd()
config = yaml.load(open('config.yml').read())
receipt = yaml.load(open('tasks.yml').read())

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

for task in task_list:
  print '...', ' '*15, str(task), ' ',
  (ok, message) = task.run(clients, cache)
  if ok:
    if message:
      print '\r%ssuccess (%s)%s' % (color.BLUE + color.BOLD, message, color.END)
    else:
      print '\r%ssuccess%s' % (color.GREEN + color.BOLD, color.END)
  else:
    print '\r%sfailed\njob failed with message "%s"!%s' % (color.RED + color.BOLD, message, color.END)
    sys.exit(1)


