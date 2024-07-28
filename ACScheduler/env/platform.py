class Host:
    def __init__(self, host_id, cpu, ram, storage):
        self.host_id = host_id
        self.cpu = cpu
        self.ram = ram
        self.storage = storage
        self.total_cpu = cpu
        self.total_ram = ram
        self.total_storage = storage
        self.bandwidth = {} # 字典用于存储与其他主机的带宽连接信息
    def add_bandwidth(self, target_host_id, bandwidth):
        self.bandwidth[target_host_id] = bandwidth
    def get_bandwidth(self, target_host_id):
        return self.bandwidth.get(target_host_id, 0)  # 如果没有定义带宽，则默认为 0
    def get_resource_utilization(self):
        cpu_utilization = (self.total_cpu - self.cpu) / self.total_cpu
        ram_utilization = (self.total_ram - self.ram) / self.total_ram
        storage_utilization = (self.total_storage - self.storage) / self.total_storage
        return cpu_utilization, ram_utilization, storage_utilization
    def __str__(self):
        return f"Host ID: {self.host_id}, CPU: {self.cpu} cores, RAM: {self.ram} GB, Storage: {self.storage} GB, Bandwidth: {self.bandwidth}"

class Docker:
    def __init__(self, container_id, cpu, ram, storage):
        self.container_id = container_id
        self.cpu = cpu
        self.ram = ram
        self.storage = storage
    def __str__(self):
        return f"Container ID: {self.container_id}, CPU: {self.cpu} cores, RAM: {self.ram} GB, Storage: {self.storage} GB"
    
class Pod:
    def __init__(self, pod_id):
        self.pod_id = pod_id
        self.containers = []

    def add_container(self, container):
        self.containers.append(container)
    def __str__(self):
        return f"Pod ID: {self.pod_id}, Containers: {len(self.containers)}"
    
class Service:
    def __init__(self, service_id):
        self.service_id = service_id
        self.pods = []
    def add_pod(self, pod):
        self.pods.append(pod)

    def __str__(self):
        return f"Service ID: {self.service_id}, Pods: {len(self.pods)}"
    
class Node:
    def __init__(self, node_id, host):
        self.node_id = node_id
        self.host = host 
        self.containers = []  # Containers running on this node
        self.pods = []
        
    def allocate_resources(self, container):
        if self.can_allocate(container):
            self.host.cpu -= container.cpu
            self.host.ram -= container.ram
            self.host.storage -= container.storage
            self.containers.append(container)
            return True
        return False
    
    def can_allocate(self, container):
        return (self.host.cpu >= container.cpu and
                self.host.ram >= container.ram and
                self.host.storage >= container.storage)
    
    def release_resources(self, container):
        self.host.cpu += container.cpu
        self.host.ram += container.ram
        self.host.storage += container.storage
        self.containers.remove(container)
    def add_pod(self,pod):
        self.pods.append(pod)

    def __str__(self):
        return f"Node ID: {self.node_id}, Host: {self.host}"

class Master(Node):
    def __init__(self,node_id,host):
        super.__init__(node_id,host)
        self.type = 'master'
        self.workers = []  # Workers managed by this master
    def add_worker(self, worker):
        self.workers.append(worker)

class Worker(Node):
    def __init__(self, node_id, host):
        super().__init__(node_id, host)
        self.type = 'worker'
