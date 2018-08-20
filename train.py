# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 01:06:59 2018

@author: Julius
"""

from tensorforce.agents import PPOAgent
from tensorforce.execution import Runner
from coinbase_env import Coinbase
import numpy as np
import os

env = Coinbase()

network_spec = [
    dict(type='internal_lstm', size=512),
    dict(type='internal_lstm', size=512),
    dict(type='internal_lstm', size=512),
]

agent = PPOAgent(
    states=env.states,
    actions=env.actions,
    network=network_spec,
    #batch_size=4096,
    # BatchAgent
    #keep_last_timestep=True,
    # PPOAgent
    step_optimizer=dict(
        type='adam',
        learning_rate=1e-3
    ),
    optimization_steps=10,
    # Model
    scope='ppo',
    discount=0.999,
    # DistributionModel
    #distributions_spec=None,
    entropy_regularization=0.01,
    # PGModel
    baseline_mode=None,
    baseline=None,
    baseline_optimizer=None,
    gae_lambda=None,
    # PGLRModel
    likelihood_ratio_clipping=0.2,
    #summary_spec=None,
    #distributed_spec=None
)

# Create the runner
runner = Runner(agent=agent, environment=env)

# Callback function printing episode statistics
def episode_finished(r):
    print("Finished episode {ep} after {ts} timesteps ({d} days) (reward: {reward})".format(ep=r.episode, ts=r.episode_timestep, d = t.episode_timestep / 24
                                                                                 reward=r.episode_rewards[-1]))
    if r.episode % 100 == 0:
        agent.save_model(os.getcwd() + '\\model')
    return True


# Start learning
runner.run(episodes=20000, max_episode_timesteps=100000, episode_finished=episode_finished)
runner.close()

# Print statistics
print("Learning finished. Total episodes: {ep}. Average reward of last 100 episodes: {ar}.".format(
    ep=runner.episode,
    ar=np.mean(runner.episode_rewards[-100:]))
)
