from collections import deque

class SimulatedClock:
    def __init__(self,start_time):
        self.current_time = start_time

    def now(self):
        return self.current_time

    def advance(self, timedelta):
        self.current_time += timedelta


class CloudEdgeEnv:
    def __init__(self,cloud_masters,edge_masters,tasks,dependencies,start_time):
        self.cloud_masters = cloud_masters
        self.edge_masters = edge_masters
        self.tasks = tasks
        self.dependencies = dependencies
        self.completed_tasks = set()
        self.pending_tasks = deque(tasks.values())
        self.simulated_time = SimulatedClock(start_time)
        self.time_slice = 10 # 初始时间片大小
        self.state = self.get_initial_state()
        self.resource_utilization_history = deque(maxlen=10) # 存储最近10个时间片的资源利用率
        self.task_failure_history = deque(maxlen=100) # 存储最近100个任务的失败记录
        self.task_history = deque(maxlen=100) # 存储最近100个任务的执行记录

    def get_initial_state(self):
        state = {
            'task_status':{
                task.task_id:{
                    'completed': False,'progress': 0.0,'estimated_completion': None,
                    'cpu_demand':task.cpu_demand,'memory_demand':task.memory_demand,
                    'storage_demand': task.storage_demand,'bandwidth_demand':task.bandwidth_demand
                } for task in self.tasks.values()},
            'resource_state': self.get_resource_state(),
            'workflow_dependencies':self.dependencies,
            'schedulable_tasks':[task for task in self.tasks.values() if self.can_schedule(task)],
            'current_time': self.simulated_time.now(),
            'task_times': {task.task_id: {'start': None, 'end': None} for task in self.tasks.values()},
            'task_history': self.task_history,  # 存储最近100个任务的执行记录
            'task_failure_history': self.task_failure_history,  # 存储最近100个任务的失败记录'
            'resource_utilization_history': self.resource_utilization_history,
            'system_load': self.calculate_system_load(),
            'network_bandwidth_usage': self.calculate_network_bandwidth_usage(),
            'task_queue_length': len(self.pending_tasks),
            'task_data_location': {task.task_id: [(file.name, file.size, file.host_id) for file in task.inputs] for task in self.tasks.values()}
        }
        return state
    
    # 任务开始时刻：start_time
    # 输入文件传输完成：确保任务能够在执行时拥有所有所需的输入文件。这样可以确保任务开始执行时不缺少必要的数据。
    # 执行准备就绪：在所有必要的输入文件传输完成后，并且资源已分配完毕，可以开始任务的实际执行
    def start_task(self,task):
        self.state['task_times'][task.task_id]['start'] = self.simulated_time.now()
        self.state['task_status'][task.task_id]['progress'] = 0.0

    # 任务完成时刻：end_time
    # 任务执行完成：任务的计算部分已经完成
    # 输出文件传输完成：确保任务产生的所有输出文件也已经成功传输到目标位置
    def end_task(self,task):
        self.state['task_times'][task.task_id]['end'] = self.simulated_time.now()
        self.state['task_status'][task.task_id]['progress'] = 1.0
        self.state['task_status'][task.task_id]['completed'] = True
        self.state['task_history'].append((task.task_id, task.assigned_node_id))
        self.completed_tasks.add(task.task_id)

        # 确定输出文件的目标主机
        for output_file in task.outputs:
            for child_task_id in task.children:
                child_task = self.tasks[child_task_id]
                for input_file in child_task.inputs:
                    if input_file['filename'] == output_file['filename']:
                        input_file['source_host_id'] = task.assigned_node_id
                        input_file['target_host_id'] = child_task.assigned_node_id
                        child_task.input_files_transferred[input_file['filename']] = True


    def advance_time(self, timedelta):
        self.simulated_time.advance(timedelta)
        self.state['current_time'] = self.simulated_time.now()

    def check_input_files_transferred(self,task):
        # 检查任务的所有输入文件是否已传输
        return all(task.input_files_transferred.values())
    
    def check_output_files_transferred(self,task):
        # 检查任务的所有输出文件是否已传输
        return all(task.output_files_transferred.values())
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
            if not self.state['task_status'][parent_id]['completed']:
                return False
        # 检查任务的输入文件是否都已到达
        if not self.check_input_files_transferred(task):
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
            try:
                # 检查任务是否可以调度以及节点是否能够分配资源
                if self.can_schedule(task) and node.can_allocate(docker):
                    # 分配资源
                    allocated = node.allocate_resources(docker)
                    if allocated:
                        # 动态确定每个输入文件的源主机和每个输出文件的目标主机
                        self.assign_file_hosts(task, node)
                        
                        # 启动任务
                        self.start_task(task)
                        self.pending_tasks.remove(task)

                        # 模拟任务执行
                        actual_time = self.calculated_actual_runtime(task,node)

                        if self.check_output_files_transferred(task):
                            # 结束任务
                            self.end_task(task)
                            reward = -self.calculate_cost(task, node)
                        else:
                            reward = 0
                    else:
                        reward = -100 # 分配资源失败，给予大惩罚
                else:
                    reward = 0 # 根据需要调整
            except Exception as e:
                # 记录异常并处理（例如回滚操作），这里简单返回作为演示
                print(f"Error processing action: {e}")
                reward = -100


            # 调整时间片大小
            #task_time = self.calculate_tasktime(task, node)
            #if task_time > self.time_slice:
            #    self.time_slice = task_time
            #else:
            #    self.time_slice = max(1, self.time_slice // 2)
    
        next_state = self.get_state()
        done = len(self.pending_tasks) == 0
        return next_state, rewards, done
    
    def assign_file_hosts(self, task, node):
        for input_file in task.inputs:
            if not input_file.get('source_host_id'):
                if not task.parents:
                    input_file['source_host_id'] = "terminal"
                else:
                    parent_task = self.get_task_producing_file(input_file['filename'])
                    input_file['source_host_id'] = parent_task.assigned_node_id if parent_task else "unknown"
            input_file['target_host_id'] = node.node_id
            # 模拟文件传输完成
            task.input_files_transferred[input_file['filename']] = True

        for output_file in task.outputs:
            output_file['source_host_id'] = node.node_id
            output_file['target_host_id'] = "terminal" if not task.children else None  # 设置为None，等到依赖任务确定
            # 模拟文件传输完成
            if not task.children:
                task.output_files_transferred[output_file['filename']] = True

    def get_task_producing_file(self,file_name):
        for task in self.tasks.values():
            for output_file in task.outputs:
                if output_file['filename'] == file_name:
                    return task
        return None
    def calculate_actual_runtime(self, task, node):
        # 计算实际运行时间
        input_time = sum([input_file['size'] / node.host.get_bandwidth(input_file['source_host_id']) for input_file in task.inputs])
        output_time = sum([output_file['size'] / node.host.get_bandwidth(output_file['target_host_id']) for output_file in task.outputs if output_file.get('target_host_id')])
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

