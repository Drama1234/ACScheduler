from env.platform import *

# 边缘集群内部带宽：500 Mbps
# 边缘集群之间带宽：200 Mbps
# 边缘集群与终端设备之间带宽：100 Mbps
# 边缘集群与云中心之间带宽：1000 Mbps
# 云中心内部带宽：2000 Mbps

# 边缘集群不需要Master节点的情况
# 分布式计算模型：
# 边缘节点通常运行分布式计算任务，每个节点相对独立，依赖于分布式算法（如边缘AI推理、数据预处理等）
# 边缘节点可以直接与云中心进行通信，处理完成后上传结果
# 去中心化管理：
# 边缘集群通过去中心化的方式进行管理，每个节点自管理并与其他节点协同工作
# 使用边缘代理或协调服务来处理节点之间的通信和任务调度


# 创建云中心和边缘集群的主机
cloud_hosts = [Host(host_id=f'cloud_host_{i}', cpu=32, ram=128, storage=1024) for i in range(12)]
edge_clusters = [[Host(host_id=f'edge_host_{i}_{j}', cpu=16, ram=64, storage=512) for j in range(4)] for i in range(4)]
terminal = [Host(host_id=f'terminal_host_{i}', cpu=4, ram=16, storage=128) for i in range(4)] 

# 配置云中心内部带宽
for i in range(12):
    for j in range(12):
        if i != j:
            cloud_hosts[i].add_bandwidth(cloud_hosts[j].host_id, 2000)  # 2000 Mbps

# 配置边缘集群内部带宽
for cluster in edge_clusters:
    for i in range(len(cluster)):
        for j in range(len(cluster)):
            if i != j:
                cluster[i].add_bandwidth(cluster[j].host_id, 500)  # 500 Mbps

# 配置边缘集群之间带宽
for i in range(len(edge_clusters)):
    for j in range(len(edge_clusters)):
        if i != j:
            for host in edge_clusters[i]:
                for target_host in edge_clusters[j]:
                    host.add_bandwidth(target_host.host_id, 200)  # 200 Mbps

# 配置边缘集群与终端设备之间带宽
for i in range(len(edge_clusters)):
    for j in range(len(terminal)):
        for host in edge_clusters[i]:
            host.add_bandwidth(terminal[j].host_id, 100)  # 100 Mbps
            terminal[j].add_bandwidth(host.host_id, 100)  # 100 Mbps

# 配置边缘集群与云中心之间带宽
for i in range(len(edge_clusters)):
    for j in range(len(cloud_hosts)):
        for host in edge_clusters[i]:
            host.add_bandwidth(cloud_hosts[j].host_id, 1000)  # 1000 Mbps
            cloud_hosts[j].add_bandwidth(host.host_id, 1000)  # 1000 Mbps

# 创建云中心和边缘集群的节点
# 云3个master节点，9个worker节点
cloud_masters = [Master(node_id=f'master_{i}', host=cloud_hosts[0])]
cloud_workers = [Worker(node_id=f'worker_{i}', host=cloud_hosts[i + 1]) for i in range(9)]#4-12

# 创建边缘集群
# 4个集群，每个集群1个master节点，4个worker节点
edge_masters = [Master(node_id=f'edge_master_{i}', host=edge_clusters[i][0]) for i in range(4)]
edge_workers = [[Worker(node_id=f'edge_worker_{i}_{j}', host=edge_clusters[i][j]) for j in range(1, 5)] for i in range(4)]

# 将worker添加到对应的master
for master in cloud_masters:
    for worker in cloud_workers:
        master.add_worker(worker)

for i, master in enumerate(edge_masters):
    for worker in edge_workers[i]:
        master.add_worker(worker)











        