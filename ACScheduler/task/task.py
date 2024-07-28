from env.platform import *

class Task:
    def __init__(self, task_id, name, runtime, inputs, outputs,cpu_demand, ram_demand, storage_demand, bandwidth_demand):
        self.task_id = task_id
        self.name = name
        self.runtime = runtime
        self.inputs = inputs  # 输入文件，列表形式[(文件名, 数据量, 文件所在位置)]
        self.outputs = outputs  # 输出文件，列表形式[(文件名, 数据量, 文件所在位置)]
        self.parents = []
        self.children = []
        self.cpu_demand = cpu_demand
        self.ram_demand = ram_demand
        self.storage_demand = storage_demand
        self.bandwidth_demand = bandwidth_demand
        self.assigned_node_id = None  # 初始化时指定默认值为 None
        self.input_files_transferred = {input_file['filename']: False for input_file in inputs}
        self.output_files_transferred = {output_file['filename']: False for output_file in outputs}

    def assign_to_node(self, node_id):
        self.assigned_node_id = node_id

