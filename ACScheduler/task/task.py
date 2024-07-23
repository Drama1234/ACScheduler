from env.platform import *

class Task:
    def __init__(self, task_id, name, runtime,inputs, outputs):
        self.task_id = task_id
        self.name = name
        self.runtime = runtime
        self.inputs = inputs
        self.outputs = outputs
        self.parents = []
        self.children = []

    def get_info(self):
        return [self.runtime, len(self.inputs), len(self.outputs)]
    
