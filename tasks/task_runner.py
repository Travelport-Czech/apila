import sys
import os
import yaml

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

def task_run(task, clients, cache):
  try:
    out = task.run(clients, cache)
  except Exception as e:
    logging.exception(str(e))
    out = (False, str(e))
  return out

def sync_print(*args):
  sys.stdout.write(' '.join(map(str, args)))
  sys.stdout.flush()

def print_task_label(task):
    sync_print('...', ' '*15, unicode(task).encode('utf8'), '  ')

def run_tasks(task_list, clients, cache, registered, tags):
  for task in task_list:
    print_task_label(task)
    if (not task.when or task.when.intersection(registered)) and (not tags or (task.tags and task.tags.intersection(tags))):
      if task.need_context():
        task.set_context(registered, tags)
      (ok, message) = task_run(task, clients, cache)
      if ok:
        if message:
          if task.register:
            registered.update(task.register)
          sync_print('\r%ssuccess (%s)%s\n' % (color.BLUE + color.BOLD, message, color.END))
        else:
          sync_print('\r%ssuccess%s\n' % (color.GREEN + color.BOLD, color.END))
      else:
        sync_print('\r%sfailed\njob failed with message "%s"!%s\n' % (color.RED + color.BOLD, message, color.END))
        if registered:
          open('todo.yml', 'w').write('# registered events after last fail\n'+yaml.dump(list(registered)))
        else:
          clear_todo()
        sys.exit(1)
    else:
      sync_print('\r%sskipped%s\n' % (color.YELLOW + color.BOLD, color.END))

def clear_todo():
  if os.path.exists('todo.yml'):
    os.unlink('todo.yml')

