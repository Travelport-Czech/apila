#!/usr/bin/env python

import yaml
import tasks
import sys
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

if '--help' in sys.argv or 'help' in sys.argv:
  tasks.print_doc()
  sys.exit(0)

if 'run' not in sys.argv:
  print 'Je treba spoustet s parametrem run nebo help, jinak to nic nedela!'
  sys.exit(1)

config = yaml.load(open('config.yml').read())
receipt = yaml.load(open('tasks.yml').read())

task_list = [tasks.create_task(task_def, config) for task_def in receipt]

errors = []
for task in task_list:
  task.validate(errors)

if len(errors) > 0:
  print 'Script contains some error:\n  %s' % '\n  '.join(errors)
  sys.exit(1)

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


