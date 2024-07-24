from collections import deque

class CloudEdgeEnv:
    def __init__(self,cloud_masters,edge_masters,tasks,dependencies):
        self.cloud_masters = cloud_masters
        self.edge_masters = edge_masters
        self.tasks = tasks
        self.dependencies = dependencies
        self.completed_tasks = set()
        self.pending_tasks = deque(tasks.values())
        self.time = 0
        self.state = self.get_initial_state()
    def get_initial_state(self):
        state = {
            'task_status':{task.task_id:{'completed':False,'progress':0.0,'estimated_completion':None} for task in self.tasks.values()},
            'resource_state': self.get_resource_state(),
            'workflow_dependencies':self.dependencies,
            'schedulable_tasks':[task for task in self.tasks.values() if self.can_schedule(task)],
            'current_time':self.time,
            'task_times': {task.task_id: {'start': None, 'end': None} for task in self.tasks.values()},
            'task_history': deque(maxlen=100)  # 存储最近100个任务的执行记录
        }
        return state

    def get_resource_state(self):
        resource_state = []
        for master in self.cloud_masters +self.edge_masters:
            resource_state.append({
                'cpu': master.host.cpu, 
                'ram': master.host.ram,
                'storage': master.host.storage,
                'load':master.host.get_resource_utilization()
                })
            for worker in master.workers:
                resource_state.append({
                'cpu':worker.host.cpu, 
                'ram':worker.host.ram, 
                'storage':worker.host.storage,
                'load':worker.host.get_resource_utilization()})
        return resource_state
    
    def can_schedule(self,task):
        # 检查该任务的所有parent是否已经完成
        for parent_id in task.parents:
            if parent_id not in self.completed_tasks:
                return False
        # 检查任务的输入文件是否都已到达
        for input_file in task.inputs:
            if input_file.host_id is None:
                return False
        return True
    
    def get_state(self):
        return{
            'task_status': self.state['task_status'],
            'resource_state': self.get_resource_state(),
            'workflow_dependencies': self.dependencies,
            'schedulable_tasks': [task for task in self.tasks.values() if self.can_schedule(task)],
            'current_time': self.time,
            'task_times': self.state['task_times'],
            'task_history': self.state['task_history']
        }

    def step(self, actions):
        # 执行动作并返回新的状态、奖励、是否结束、额外信息
        rewards = 0
        for action in actions:
            task, docker, node = action
            allocated = node.allocate_resources(docker)
            if allocated:
                self.pending_tasks.remove(task)
                self.completed_tasks.add(task.task_id)
                self.state['task_status'][task.task_id]['completed'] = True
                self.state['task_history'].append((task.task_id, docker.container_id, node.node_id))
                rewards += -self.calculate_tasktime(task, node)
            else:
                rewards = -100  # 分配失败，给予大惩罚

        self.time += 1
        next_state = self.get_state()
        done = len(self.pending_tasks) == 0
        return next_state, rewards, done
    def calculate_tasktime(self, task, node):
        # 计算任务的完工时间
        input_time = sum([input_file.size / node.host.get_bandwidth(input_file.host_id) for input_file in task.inputs])
        output_time = sum([output_file.size / node.host.get_bandwidth(output_file.host_id) for output_file in task.outputs])
        execution_time = task.runtime
        return input_time + output_time + execution_time
    def calculate_resource_utilization(self):
        utilization = []
        for master in self.cloud_masters + self.edge_masters:
            utilization.append(master.host.get_resource_utilization())
            for worker in master.workers:
                utilization.append(worker.host.get_resource_utilization())
        return utilization
    def reset(self):
        self.completed_tasks.clear()
        self.pending_tasks = deque(self.tasks.values())
        self.time = 0
        self.state = self.get_initial_state()
        return self.get_state()

