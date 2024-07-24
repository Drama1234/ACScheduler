import tensorflow as tf
from tensorflow.keras.layers import Dense
from tensorflow.keras import layers,models
import numpy as np
from env.platform import *

class ActorNetwork(models.Model):
    """
    Actor network:用于决定在特定状态下采取的动作，输出策略，即在每个状态下选择每个动作的概率分布
    """
    def __init__(self,state_dim,action_dim):
        super(ActorNetwork, self).__init__()
        self.dense1 = Dense(128, activation='relu',input_shape=(state_dim,))
        self.dense2 = Dense(64, activation='relu')
        self.dense3 = Dense(32, activation='relu')
        self.policy_logits = layers.Dense(action_dim)
    def call(self,inputs):
        x = self.dense1(inputs)
        x = self.dense2(x)
        x = self.dense3(x)
        return self.policy_logits(x)

class CriticNetwork(models.Model):
    """
    Critic network:用于评估Actor网络的动作,输出的是当前策略在给定状态下的预期价值(通常是状态值或状态-动作值)
    """
    def __init__(self,state_dim):
        super(CriticNetwork, self).__init__()
        self.dense1 = Dense(128, activation='relu',input_shape=(state_dim,))
        self.dense2 = Dense(64, activation='relu')
        self.dense3 = Dense(32, activation='relu')
        self.value =Dense(1)

    def call(self, inputs):
        x = self.dense1(inputs)
        x = self.dense2(x)
        x = self.dense3(x)
        return self.value(x)
    
class DistributedActorCritic:
    def __init__(self, state_dim, action_dim,actor_lr=0.001, critic_lr=0.001):
        self.actor = ActorNetwork(state_dim, action_dim)
        self.critic = CriticNetwork(state_dim)
        self.actor_optimizer = tf.keras.optimizers.Adam(learning_rate=actor_lr)
        self.critic_optimizer = tf.keras.optimizers.Adam(learning_rate=critic_lr)
    def select_action(self,state):
        state_tensor = tf.convert_to_tensor(np.expand_dims(state,axis=0), dtype=tf.float32)
        logits = self.actor(state_tensor)
        action = tf.random.categorical(logits, 1)[0, 0].numpy()
        return action
    def update(self,state,action,reward,next_state,gamma):
        state = tf.convert_to_tensor(np.expand_dims(state, axis=0), dtype=tf.float32)
        next_state = tf.convert_to_tensor(np.expand_dims(next_state, axis=0), dtype=tf.float32)

        with tf.GradientTape() as critic_tape:
            state_value = self.critic(state)
            next_state_value = self.critic(next_state)
            advantage = reward + gamma * next_state_value - state_value
            critic_loss = tf.reduce_mean(tf.square(advantage))

        critic_grads = critic_tape.gradient(critic_loss, self.critic.trainable_variables)
        self.critic_optimizer.apply_gradients(zip(critic_grads, self.critic.trainable_variables))

        with tf.GradientTape() as actor_tape:
            logits = self.actor(state)
            actor_loss = -tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(labels=[action], logits=logits) * advantage)
        
        actor_grads = actor_tape.gradient(actor_loss, self.actor.trainable_variables)
        self.actor_optimizer.apply_gradients(zip(actor_grads, self.actor.trainable_variables))

def train_distributed_actor_critic(env, agent, gamma=0.99, num_episodes=1000, time_slice=10):
    for episode in range(num_episodes):
        state = env.reset()
        done = False
        tatal_reward = 0

        while not done:
            actions = []
            
            

        while not done:
            #计算策略网络（actor network）和值函数网络（critic network）的梯度
            with tf.GradientTape() as actor_tape, tf.GradientTape() as critic_tape:
                resource_utilization = np.array(env.get_state()['resource_state']).flatten()
                task_history_vector = np.array(list(env.get_state()['task_history']))
                
                state_tensor = tf.convert_to_tensor(np.concatenate([resource_utilization, task_history_vector]), dtype=tf.float32)

                policy_logits = actor(state_tensor)
                action_probabilities = tf.nn.softmax(policy_logits)
                actions = []
                for _ in range(time_slice):
                    action_index = tf.random.categorical(policy_logits, 1)[0, 0].numpy()
                    task = env.pending_tasks[0]
                    docker = Docker(container_id=f'container_{task.task_id}', cpu=task.runtime, ram=task.runtime, storage=task.runtime)
                    nodes = env.cloud_masters + env.edge_masters + [worker for master in env.cloud_masters + env.edge_masters for worker in master.workers]
                    node = nodes[action_index]
                    actions.append((task, docker, node))

                next_state, reward, done = env.step(actions)
                next_resource_utilization = np.array(next_state['resource_utilization']).flatten()
                next_task_history_vector = np.array(list(next_state['task_history']))
                next_state_tensor = tf.convert_to_tensor(np.concatenate([next_resource_utilization, next_task_history_vector]), dtype=tf.float32)

                value = critic(state_tensor)
                next_value = critic(next_state_tensor)
                advantage = reward + gamma * next_value - value

                policy_loss = -tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(labels=action_index, logits=policy_logits) * advantage)
                value_loss = tf.reduce_mean(tf.square(advantage))

                total_loss = policy_loss + value_loss

            actor_grads = actor_tape.gradient(total_loss, actor.trainable_variables)
            critic_grads = critic_tape.gradient(total_loss, critic.trainable_variables)
            actor_optimizer.apply_gradients(zip(actor_grads, actor.trainable_variables))
            critic_optimizer.apply_gradients(zip(critic_grads, critic.trainable_variables))

            state = next_state
            if done:
                print(f"Episode {episode + 1}/{num_episodes} completed")

def execute_policy(env, actor):
    state = env.reset()
    done = False
    while not done:
        resource_utilization = np.array(env.get_state()['resource_utilization']).flatten()
        task_history_vector = np.array(list(env.get_state()['task_history']))
        state_tensor = tf.convert_to_tensor(np.concatenate([resource_utilization, task_history_vector]), dtype=tf.float32)

        policy_logits = actor(state_tensor)
        action_probabilities = tf.nn.softmax(policy_logits)
        action_index = tf.argmax(action_probabilities).numpy()

        task = env.pending_tasks[0]
        docker = Docker(container_id=f'container_{task.task_id}', cpu=task.runtime, ram=task.runtime, storage=task.runtime)
        nodes = env.cloud_masters + env.edge_masters + [worker for master in env.cloud_masters + env.edge_masters for worker in master.workers]
        node = nodes[action_index]

        actions = [(task, docker, node)]
        next_state, reward, done = env.step(actions)
        state = next_state
        if done:
            print("Execution completed")
        







                    

        









