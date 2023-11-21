# MARL Penalty Shot Challenge
In this project we have a task to do a `MARL (Multi-Agent Reinforcement Learning) Penalty Shot Challenge` by creating our own platform to pit SOTA Deep Reinforcement Learning algorithms against each other. It involves two agents simulating a penalty shootout. We have two entities that we would be playing on, `The Bar` and `The Puck`.

## Table of Contents
- [Features](#features)
- [How to begin](#how-to-begin)
    - [Install packages](#install-packages)
    - [Train and test a model](#train-and-test-a-model)
    - [Play as bar](#to-play-as-bar)
- [Codebase](#codebase)
    - [Game Environment](#game-environment)
    - [Agents](#agents)
    - [Async Communication](#async-communication)
    - [Examples](#examples)
- [Team Members](#team-members)
- [Course and Professor](#course-and-professor)
- [Want to contribute?](#want-to-contribute)
- [Acknowledgement](#acknowledgement)

## Features
- Visualization of the unique environment at every step
- Complete customization of environments and policies
- Asynchronous server for manual interaction with a policy

[Back to TOC](#table-of-contents)

## How to begin

### Install packages
>The `-e` flag is included to make the project package editable

>Login to `wandb.ai` to record your experimental runs 
```bash
pip install -e .
pip install -e ./gym-env
wandb login
```

[Back to TOC](#table-of-contents)

### Train and test a model
> Use files in `utils/config/` to control configuration of agent specific policy hyper-parameters and environment parameters

#### Example command to run that trains a puck and bar with PPO algorithm and uses a previously saved policy for each of the agents with 1 training environment and 2 test environment 
```bash
python ./utils/train.py  --wandb-name "ds251_project" --training-num 1 --test-num 2 --puck ppo --bar ppo --load-puck-id both_ppo --load-bar-id both_ppo 
```

[Back to TOC](#table-of-contents)

### To play as bar:
Open 3 terminals and run 
```bash
python ./examples/server/start_server.py
```
```bash
python ./examples/server/agent_puck.py
```
```bash
python ./examples/server/agent_bar.py
```
Click `Start` and use the mouse slider to control the direction of the bar.

[Back to TOC](#table-of-contents)

## Codebase
### Game Environment
It comprises a puck and a bar, with the puck moving horizontally at a consistent speed towards the bar. Each entity is independently controlled by its respective agent. The objective for the puck is to surpass the bar and reach the final line, while the bar aims to intercept the puck before it reaches the final line.

The environment is constructed using the OpenAI Gym library, where two action parameters corresponding to the puck and bar are accepted. The game progresses by one time step, producing a tuple output of state, reward, completion state, and an additional information object. [Back to TOC](#table-of-contents)

### Agents
- `lib-agents`: It features trivial, value based and policy based algorithms including `smurve`, `DQN`, `TD3`, `PPO` and `DDPG`.
- `comm-agents`: It implements the hardcoded approach for finding a baseline and pure exploration strategy. It also implements the mouse slider.
- Also implements a `TwoAgentPolicyWrapper` to combine policies for the puck and the agent.
[Back to TOC](#table-of-contents)

### Utils
- Contains training script and utility functions implementing wrappers
- Stores policy and environment configuration information. 
[Back to TOC](#table-of-contents)

### Async Communication
To support asynchronous inputs from agents, we have created a main server which controls the environment. The agents using client class to connect to the server and use its step function to give their action and receive corresponding result tuple. The server takes actions from the agents as input and synchronizes them and updates the environment by one time step. [Back to TOC](#table-of-contents)

### Examples
- Script for playing with the puck as a bar
- A notebook demonstrating smurves
[Back to TOC](#table-of-contents)


## Team Members
- `Abhishek Kumar (12140040)`
- `Arnav Gautam (12140280)`
- `Dhruv Gupta (12140580)`
- `Mitul Vardhan (12141070)`

## Course and Professor
- This Project is done under Professor and Course of IIT Bhilai:

1. `Professor: Soumyajit Pramanik`
2. `Course: DS251`

[Back to TOC](#table-of-contents)
## Want to Contribute?
We welcome everyone to report bugs, raise issues, add features etc. Contact the [team members](#team-members) of this project to discuss more.

[Back to TOC](#table-of-contents)
## Acknowledgement
- We thank Prof. Soumyajit Pramanik for providing us with this opportunity to explore and learn more about SOTA algorithms through a project.
- We also thank the creators of Tianshou and OpenAI Gym library which forms a core part of our codebase
- We thank the open source community for wonderful libraries for everything under the sun! 

[Back to TOC](#table-of-contents)
