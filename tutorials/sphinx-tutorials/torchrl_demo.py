# -*- coding: utf-8 -*-
"""
TorchRL Demo
============================
This demo was presented at ICML 2022 on the industry demo day.
"""
##############################################################################
# It gives a good overview of TorchRL functionalities. Feel free to reach out
# to vmoens@fb.com or submit issues if you have questions or comments about it.
#
# TorchRL is an open-source Reinforcement Learning (RL) library for PyTorch.
#
# https://github.com/pytorch/rl
#
# The PyTorch ecosystem team (Meta) has decided to invest in that library to
# provide a leading platform to develop RL solutions in research settings.
# It provides pytorch and **python-first**, low and high level **abstractions**
# for RL that are intended to be efficient, documented and properly tested.
# The code is aimed at supporting research in RL. Most of it is written in python
# in a highly modular way, such that researchers can easily swap components,
# transform them or write new ones with little effort.
# This repo attempts to align with the existing pytorch ecosystem libraries
# in that it has a dataset pillar (torchrl/envs), transforms, models, data utilities
# (e.g. collectors and containers), etc. TorchRL aims at having as few dependencies
# as possible (python standard library, numpy and pytorch).
# Common environment libraries (e.g. OpenAI gym) are only optional.
#
# Content:
#
# Unlike other domains, RL is less about media than algorithms. As such, it is harder
# to make truly independent components.
#
# What TorchRL is not:
# - a collection of algorithms: we do not intend to provide SOTA implementations of
# RL algorithms, but we provide these algorithms only as examples of how to use the library.
# - a research framework
#
# TorchRL has very few core dependencies, mostly PyTorch and functorch. All other
# dependencies (gym, torchvision, wandb / tensorboard) are optional.
#
# Data
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# TensorDict
# ------------------------------

import torch
from torchrl.data import TensorDict

###############################################################################
# Let's create a TensorDict.

batch_size = 5
tensordict = TensorDict(source={
    "key 1": torch.zeros(batch_size, 3),
    "key 2": torch.zeros(batch_size, 5, 6, dtype=torch.bool)
}, batch_size = [batch_size])
print(tensordict)

###############################################################################
# You can index a TensorDict as well as query keys.

print(tensordict[2])
print(tensordict["key 1"] is tensordict.get("key 1"))

###############################################################################
# The following shows how to stack multiple TensorDicts.

tensordict1 = TensorDict(source={
    "key 1": torch.zeros(batch_size, 1),
    "key 2": torch.zeros(batch_size, 5, 6, dtype=torch.bool)
}, batch_size = [batch_size])

tensordict2 = TensorDict(source={
    "key 1": torch.ones(batch_size, 1),
    "key 2": torch.ones(batch_size, 5, 6, dtype=torch.bool)
}, batch_size = [batch_size])

tensordict = torch.stack([tensordict1, tensordict2], 0)
tensordict.batch_size, tensordict["key 1"]

###############################################################################
# Here are some other functionalities of TensorDict.

print("view(-1): ", tensordict.view(-1).batch_size, tensordict.view(-1).get("key 1").shape)

print("to device: ", tensordict.to("cpu"))

# print("pin_memory: ", tensordict.pin_memory())

print("share memory: ", tensordict.share_memory_())

print("permute(1, 0): ",
      tensordict.permute(1, 0).batch_size,
      tensordict.permute(1, 0).get("key 1").shape)

print("expand: ",
      tensordict.expand(3, *tensordict.batch_size).batch_size,
      tensordict.expand(3, *tensordict.batch_size).get("key 1").shape)

###############################################################################
# You can create a **nested TensorDict** as well.

tensordict = TensorDict(source={
    "key 1": torch.zeros(batch_size, 3),
    "key 2": TensorDict(source={
        "sub-key 1": torch.zeros(batch_size, 2, 1)
    }, batch_size=[batch_size, 2])
}, batch_size = [batch_size])
tensordict

###############################################################################
# Replay buffers
# ------------------------------

from torchrl.data import ReplayBuffer, PrioritizedReplayBuffer

###############################################################################

rb = ReplayBuffer(100, collate_fn=lambda x: x)
rb.add(1)
rb.sample(1)

###############################################################################

rb.extend([2, 3])
rb.sample(3)

###############################################################################

rb = PrioritizedReplayBuffer(100, alpha=0.7, beta=1.1, collate_fn=lambda x: x)
rb.add(1)
rb.sample(1)
rb.update_priority(1, 0.5)

###############################################################################
# Here are examples of using a replaybuffer with tensordicts.

collate_fn = torch.stack
rb = ReplayBuffer(100, collate_fn=collate_fn)
rb.add(TensorDict({"a": torch.randn(3)}, batch_size=[]))
len(rb)

###############################################################################

rb.extend(TensorDict({"a": torch.randn(2, 3)}, batch_size=[2]))
print(len(rb))
print(rb.sample(10))
print(rb.sample(2).contiguous())

###############################################################################

torch.manual_seed(0)
from torchrl.data import TensorDictPrioritizedReplayBuffer
rb = TensorDictPrioritizedReplayBuffer(100, alpha=0.7, beta=1.1, priority_key="td_error")
rb.extend(TensorDict({"a": torch.randn(2, 3)}, batch_size=[2]))
tensordict_sample = rb.sample(2).contiguous()
tensordict_sample

###############################################################################

tensordict_sample["index"]

###############################################################################

tensordict_sample["td_error"] = torch.rand(2)
rb.update_priority(tensordict_sample)

for i, val in enumerate(rb._sum_tree):
    print(i, val)
    if i == len(rb):
        break

###############################################################################
# Envs
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

from torchrl.envs.libs.gym import GymWrapper, GymEnv
import gym

gym_env = gym.make("Pendulum-v1")
env = GymWrapper(gym_env)
env = GymEnv("Pendulum-v1")

###############################################################################

tensordict = env.reset()
env.rand_step(tensordict)

###############################################################################
# Changing environments config
# ------------------------------

env = GymEnv("Pendulum-v1", frame_skip=3, from_pixels=True, pixels_only=False)
env.reset()

###############################################################################

env.close()
del env

###############################################################################

from torchrl.envs import Compose, ObservationNorm, ToTensorImage, NoopResetEnv, TransformedEnv
base_env = GymEnv("Pendulum-v1", frame_skip=3, from_pixels=True, pixels_only=False)
env = TransformedEnv(base_env, Compose(NoopResetEnv(3), ToTensorImage()))
env.append_transform(ObservationNorm(keys_in=["next_pixels"], loc=2, scale=1))

###############################################################################
# Transforms
# ------------------------------

from torchrl.envs import Compose, ObservationNorm, ToTensorImage, NoopResetEnv, TransformedEnv
base_env = GymEnv("Pendulum-v1", frame_skip=3, from_pixels=True, pixels_only=False)
env = TransformedEnv(base_env, Compose(NoopResetEnv(3), ToTensorImage()))
env.append_transform(ObservationNorm(keys_in=["next_pixels"], loc=2, scale=1))

###############################################################################

env.reset()

###############################################################################

print("env: ", env)
print("last transform parent: ", env.transform[2].parent)

###############################################################################
# Vectorized Environments
# ------------------------------

from torchrl.envs import ParallelEnv
base_env = ParallelEnv(4, lambda: GymEnv("Pendulum-v1", frame_skip=3, from_pixels=True, pixels_only=False))
env = TransformedEnv(base_env, Compose(NoopResetEnv(3), ToTensorImage()))  # applies transforms on batch of envs
env.append_transform(ObservationNorm(keys_in=["next_pixels"], loc=2, scale=1))
env.reset()

###############################################################################

env.action_spec

###############################################################################
# Modules
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# Models
# ------------------------------
#
# Example of a MLP model:

from torchrl.modules import MLP, ConvNet
from torchrl.modules.models.utils import SquashDims
from torch import nn
net = MLP(num_cells=[32, 64], out_features=4, activation_class=nn.ELU)
print(net)
print(net(torch.randn(10, 3)).shape)

###############################################################################
# Example of a CNN model:

cnn = ConvNet(num_cells=[32, 64], kernel_sizes=[8, 4], strides=[2, 1], aggregator_class=SquashDims)
print(cnn)
print(cnn(torch.randn(10, 3, 32, 32)).shape)  # last tensor is squashed

###############################################################################
# TensorDictModules
# ------------------------------

from torchrl.modules import TensorDictModule
tensordict = TensorDict({"key 1": torch.randn(10, 3)}, batch_size=[10])
module = nn.Linear(3, 4)
td_module = TensorDictModule(module, in_keys=["key 1"], out_keys=["key 2"])
td_module(tensordict)
print(tensordict)

###############################################################################
# Sequences of Modules
# ------------------------------

from torchrl.modules import TensorDictSequential
backbone_module = nn.Linear(5, 3)
backbone = TensorDictModule(backbone_module, in_keys=["observation"], out_keys=["hidden"])
actor_module = nn.Linear(3, 4)
actor = TensorDictModule(actor_module, in_keys=["hidden"], out_keys=["action"])
value_module = MLP(out_features=1, num_cells=[4, 5])
value = TensorDictModule(value_module, in_keys=["hidden", "action"], out_keys=["value"])

sequence = TensorDictSequential(backbone, actor, value)
print(sequence)

###############################################################################

print(sequence.in_keys, sequence.out_keys)

###############################################################################

tensordict = TensorDict(
    {"observation": torch.randn(3, 5)}, [3],
)
backbone(tensordict)
actor(tensordict)
value(tensordict)

###############################################################################

tensordict = TensorDict(
    {"observation": torch.randn(3, 5)}, [3],
)
sequence(tensordict)
print(tensordict)

###############################################################################
# Functional Programming (Ensembling / Meta-RL)
# ----------------------------------------------

fsequence, (params, buffers) = sequence.make_functional_with_buffers()
len(list(fsequence.parameters()))  # functional modules have no parameters

###############################################################################

fsequence(tensordict, params=params, buffers=buffers)

###############################################################################

params_expand = [p.expand(4, *p.shape) for p in params]
buffers_expand = [b.expand(4, *b.shape) for b in buffers]
tensordict_exp = fsequence(tensordict, params=params_expand, buffers=buffers, vmap=(0, 0, None))
print(tensordict_exp)

###############################################################################
# Specialized Classes
# ------------------------------

torch.manual_seed(0)
from torchrl.data import NdBoundedTensorSpec
spec = NdBoundedTensorSpec(-torch.ones(3), torch.ones(3))
base_module = nn.Linear(5, 3)
module = TensorDictModule(module=base_module, spec=spec, in_keys=["obs"], out_keys=["action"], safe=True)
tensordict = TensorDict({"obs": torch.randn(5)}, batch_size=[])
module(tensordict)["action"]

###############################################################################

tensordict = TensorDict({"obs": torch.randn(5)*100}, batch_size=[])
module(tensordict)["action"]  # safe=True projects the result within the set

###############################################################################

from torchrl.modules import Actor
base_module = nn.Linear(5, 3)
actor = Actor(base_module, in_keys=["obs"])
tensordict = TensorDict({"obs": torch.randn(5)}, batch_size=[])
actor(tensordict)  # action is the default value

###############################################################################

# Probabilistic modules
from torchrl.modules import ProbabilisticTensorDictModule
from torchrl.data import TensorDict
from torchrl.modules import  TanhNormal, NormalParamWrapper
td = TensorDict({"input": torch.randn(3, 5)}, [3,])
net = NormalParamWrapper(nn.Linear(5, 4))  # splits the output in loc and scale
module = TensorDictModule(net, in_keys=["input"], out_keys=["loc", "scale"])
td_module = ProbabilisticTensorDictModule(
   module=module,
   dist_in_keys=["loc", "scale"],
   sample_out_key=["action"],
   distribution_class=TanhNormal,
   return_log_prob=False,
)
td_module(td)
print(td)

###############################################################################

# returning the log-probability
td = TensorDict({"input": torch.randn(3, 5)}, [3,])
td_module = ProbabilisticTensorDictModule(
   module=module,
   dist_in_keys=["loc", "scale"],
   sample_out_key=["action"],
   distribution_class=TanhNormal,
   return_log_prob=True,
)
td_module(td)
print(td)

###############################################################################

# Sampling vs mode / mean
from torchrl.envs.utils import set_exploration_mode
td = TensorDict({"input": torch.randn(3, 5)}, [3,])

torch.manual_seed(0)
with set_exploration_mode("random"):
    td_module(td)
    print("random:", td["action"])

with set_exploration_mode("mode"):
    td_module(td)
    print("mode:", td["action"])

with set_exploration_mode("mean"):
    td_module(td)
    print("mean:", td["action"])

###############################################################################
# Using Environments and Modules
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

from torchrl.envs.utils import step_mdp
env = GymEnv("Pendulum-v1")

action_spec = env.action_spec
actor_module = nn.Linear(3, 1)
actor = TensorDictModule(actor_module, spec=action_spec, in_keys=["observation"], out_keys=["action"])

torch.manual_seed(0)
env.set_seed(0)

max_steps = 100
tensordict = env.reset()
tensordicts = TensorDict({}, [max_steps])
for i in range(max_steps):
    actor(tensordict)
    tensordicts[i] = env.step(tensordict)
    tensordict = step_mdp(tensordict)  # roughly equivalent to obs = next_obs
    if env.is_done:
        break

tensordicts_prealloc = tensordicts.clone()
print("total steps:", i)
print(tensordicts)

###############################################################################

# equivalent
torch.manual_seed(0)
env.set_seed(0)

max_steps = 100
tensordict = env.reset()
tensordicts = []
for i in range(max_steps):
    actor(tensordict)
    tensordicts.append(env.step(tensordict))
    tensordict = step_mdp(tensordict)  # roughly equivalent to obs = next_obs
    if env.is_done:
        break
tensordicts_stack = torch.stack(tensordicts, 0)
print("total steps:", i)
print(tensordicts_stack)

###############################################################################

(tensordicts_stack == tensordicts_prealloc).all()

###############################################################################

# helper
torch.manual_seed(0)
env.set_seed(0)
tensordict_rollout = env.rollout(policy=actor, max_steps=max_steps)
tensordict_rollout

###############################################################################

(tensordict_rollout == tensordicts_prealloc).all()

###############################################################################
# Collectors
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

from torchrl.envs import ParallelEnv, EnvCreator
from torchrl.envs.libs.gym import GymEnv
from torchrl.modules import TensorDictModule
from torchrl.collectors import MultiSyncDataCollector, MultiaSyncDataCollector
from torch import nn

# EnvCreator makes sure that we can send a lambda function from process to process
parallel_env = ParallelEnv(3, EnvCreator(lambda: GymEnv("Pendulum-v1")))
create_env_fn=[parallel_env, parallel_env]

actor_module = nn.Linear(3, 1)
actor = TensorDictModule(actor_module, in_keys=["observation"], out_keys=["action"])

# Sync data collector
devices = ["cpu", "cpu"]

collector = MultiSyncDataCollector(
    create_env_fn=create_env_fn,  # either a list of functions or a ParallelEnv
    policy=actor,
    total_frames=240,
    max_frames_per_traj=-1,  # envs are terminating, we don't need to stop them early
    frames_per_batch=60,  # we want 60 frames at a time (we have 3 envs per sub-collector)
    passing_devices=devices,  # len must match len of env created
    devices=devices,
)

###############################################################################

for i, d in enumerate(collector):
    if i == 0:
        print(d)  # trajectories are split automatically in [6 workers x 10 steps]
    collector.update_policy_weights_()  # make sure that our policies have the latest weights if working on multiple devices
print(i)

###############################################################################

# async data collector: keeps working while you update your model
collector = MultiaSyncDataCollector(
    create_env_fn=create_env_fn,  # either a list of functions or a ParallelEnv
    policy=actor,
    total_frames=240,
    max_frames_per_traj=-1,  # envs are terminating, we don't need to stop them early
    frames_per_batch=60,  # we want 60 frames at a time (we have 3 envs per sub-collector)
    passing_devices=devices,  # len must match len of env created
    devices=devices,
)

for i, d in enumerate(collector):
    if i == 0:
        print(d)  # trajectories are split automatically in [6 workers x 10 steps]
    collector.update_policy_weights_()  # make sure that our policies have the latest weights if working on multiple devices
print(i)
del collector

###############################################################################
# Objectives
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# TorchRL delivers meta-RL compatible loss functions
# Disclaimer: This APi may change in the future
from torchrl.objectives import DDPGLoss
from torchrl.data import TensorDict
from torchrl.modules import TensorDictModule
import torch
from torch import nn

actor_module = nn.Linear(3, 1)
actor = TensorDictModule(actor_module, in_keys=["observation"], out_keys=["action"])

class ConcatModule(nn.Linear):
    def forward(self, obs, action):
        return super().forward(torch.cat([obs, action], -1))

value_module = ConcatModule(4, 1)
value = TensorDictModule(value_module, in_keys=["observation", "action"], out_keys=["state_action_value"])

loss_fn = DDPGLoss(actor, value, gamma=0.99)

###############################################################################

tensordict = TensorDict({
    "observation": torch.randn(10, 3),
    "next_observation": torch.randn(10, 3),
    "reward": torch.randn(10, 1),
    "action": torch.randn(10, 1),
    "done": torch.zeros(10, 1, dtype=torch.bool),
}, batch_size=[10])
#loss_td = loss_fn(tensordict)

###############################################################################

#loss_td

###############################################################################

tensordict

###############################################################################
# State of the Library
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# TorchRL is currently an **alpha-release**: there may be bugs and there is no
# guarantee about BC-breaking changes. We should be able to move to a beta-release
# by the end of the year. Our roadmap to get there comprises:
# - Distributed solutions
# - Offline RL
# - Greater support for meta-RL
# - Multi-task and hierarchical RL
#
# Contributing
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# We are actively looking for contributors and early users. If you're working in
# RL (or just curious), try it! Give us feedback: what will make the success of
# TorchRL is how well it covers researchers needs. To do that, we need their input!
# Since the library is nascent, it is a great time for you to shape it the way you want!

###############################################################################
# Installing the Library
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# The library is on PyPI: $ pip install torchrl