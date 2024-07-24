from env.platform import *

class Task:
    def __init__(self, task_id, name, runtime, inputs, outputs):
        self.task_id = task_id
        self.name = name
        self.runtime = runtime
        self.inputs = inputs  # list of File objects
        self.outputs = outputs  # list of File objects
        self.parents = []
        self.children = []
    
