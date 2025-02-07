#!/usr/bin/env python3

import click

   @click.command()
   @click.option('--add', help='Add a new task')
   @click.option('--list', help='List all tasks')
   @click.option('--remove', help='Remove a task')
   @click.option('--task', help='Task to add or remove')

   def main(add, list, remove, task):
       if add:
           with open('tasks.txt', 'a') as f:
               f.write(f'{task}\n')
           click.echo(f'Task added: {task}')
       elif list:
           with open('tasks.txt', 'r') as f:
               tasks = f.readlines()
           for i, task in enumerate(tasks, start=1):
               click.echo(f'{i}. {task.strip()}')
       elif remove:
           with open('tasks.txt', 'r') as f:
               tasks = f.readlines()
           task_index = int(task) - 1
           if 0 <= task_index < len(tasks):
               del tasks[task_index]
               with open('tasks.txt', 'w') as f:
                   f.writelines(tasks)
               click.echo(f'Task removed: {tasks[task_index].strip()}')
           else:
               click.echo('Invalid task number')
       else:
           click.echo('Nothing to do. Use --help for more information.')

   if __name__ == '__main__':
       main()
