from lxml import etree
import os
from task.task import *

        
class WorkflowParser:
    def __init__(self, dax_file):
        if not os.path.isfile(dax_file):
            raise FileNotFoundError(f"File {dax_file} does not exist.")
        self.dax_file = dax_file
        self.tasks = {}
        self.dependencies = []

    def parse_dax_file(self):
        try:
            with open(self.dax_file, 'rb') as file:
                file_content = file.read()

            tree = etree.fromstring(file_content)

            # Print the root tag to ensure the file is parsed correctly
            print(f"Root tag: {tree.tag}")

            for job in tree.findall('job'):
                task_id = job.get('id')
                name = job.get('name')
                runtime = float(job.get('runtime'))
                
                inputs = [{'filename': file.get('file'), 'size': int(file.get('size')), 'source_host_id': None, 'target_host_id': None} for file in job.findall('uses[@link="input"]')]
                outputs = [{'filename': file.get('file'), 'size': int(file.get('size')), 'source_host_id': None, 'target_host_id': None} for file in job.findall('uses[@link="output"]')]

                self.tasks[task_id] = Task(task_id, name, runtime, inputs, outputs)

                # Debug: Print task details
                #print(f"Parsed task: {task_id}, {name}, {runtime}, inputs: {[f.file_name for f in inputs]}, outputs: {[f.file_name for f in outputs]}")

            for child in tree.findall('child'):
                child_id = child.get('ref')
                for parent in child.findall('parent'):
                    parent_id = parent.get('ref')
                    self.dependencies.append((parent_id, child_id))
                    self.tasks[parent_id].children.append(child_id)
                    self.tasks[child_id].parents.append(parent_id)

                #Debug: Print dependency details
                print(f"Parsed dependency: parent={parent_id}, child={child_id}")

        except etree.XMLSyntaxError as e:
            raise ValueError(f"Error parsing the DAX file: {e}")
    def get_tasks(self):
        return self.tasks
    def get_dependencies(self):
        return self.dependencies


dax_file = '/home/drama/code/ACScheduler/workflows/MONTAGE.n.100.0.dax'
parser = WorkflowParser(dax_file)
parser.parse_dax_file()

tasks = parser.get_tasks()
dependencies = parser.get_dependencies()

# Print parsed tasks and dependencies for verification
for task_id, task in tasks.items():
    print(f'Task ID: {task.task_id}, Name: {task.name}, Runtime: {task.runtime}')
    for inp in task.inputs:
        print(f'  Input: FileName:{inp.file_name}, Size: {inp.size}')
    for out in task.outputs:
        print(f'  Output: FileName:{out.file_name}, Size: {out.size}')

print('Dependencies:')
for parent, child in dependencies:
    print(f'  {parent} -> {child}')



