import torch
import numpy as np
import tianshou as ts
import pprint
from tianshou.utils import WandbLogger
from tianshou.env import SubprocVectorEnv
from tianshou.data import Collector, VectorReplayBuffer
from tianshou.trainer import offpolicy_trainer, onpolicy_trainer
from torch.serialization import save
from agents import TwoAgentPolicy
from agents.lib_agents import *
from utils.envs import make_envs, MakeEnv
from utils.config import puck_params, bar_params, env_params
import argparse
import os

# Maps algorithms to their respective classes
algo_mapping = {
    "sine": SinePolicy,
    "random": RandomPolicy,
    "greedy": GreedyPolicy,
    "smurve": SmurvePolicy,
    "dqn": DQN,
    "sac": SAC,
    "ppo": PPO,
    "ddpg": DDPG,
    "td3": TD3,
}

# Global variables for policy ang arguments
policy = None
args = None


def train_fn(epoch, env_step):
    """Hook called at beginning of training

    Args:
        epoch (int): Epoch number
        env_step (int): Step number in the environment
    """
    tot_steps = args.epoch * args.step_per_epoch
    if args.eps_train_decay == "const":
        eps = args.eps_train_final
    elif args.eps_train_decay == "lin":
        eps = args.eps_train - (env_step / tot_steps) * (
            args.eps_train - args.eps_train_final
        )
    elif args.eps_train_decay == "exp":
        eps = args.eps_train * (
            (args.eps_train_final / args.eps_train) ** (env_step / tot_steps)
        )
    policy.set_eps(eps)


def test_fn(epoch, env_step):
    """Test hook function called while training

    Args:
        epoch (int): Epoch number
        env_step (int): Step number in the environment
    """
    policy.set_eps(args.eps_test)


def save_checkpoint_fn(epoch: int, env_step: int, gradient_step: int):
    """Function hook to save model

    Args:
        epoch (int): Epoch number
        env_step (int): Step number in the environment
        gradient_step (int): Step number in the gradient

    Returns:
        str: Path where to save the model/policy
    """
    save_folder = "saved_policies/{}".format(args.run_id)
    if not os.path.isdir(save_folder):
        os.makedirs(save_folder)

    puck_file_path = "{}/puck_{}.pth".format(save_folder, args.puck)
    print("saving puck")
    torch.save(policy.puck_policy.state_dict(), puck_file_path)

    bar_file_path = "{}/bar_{}.pth".format(save_folder, args.bar)
    print("saving bar")
    torch.save(policy.bar_policy.state_dict(), bar_file_path)

    save_path = "{}/log".format(save_folder)
    if not os.path.isfile(save_path):
        with open(save_path, "w") as f:
            pass
    return save_path


def get_args():
    """Retuns the arguments for the script

    Returns:
        Argument object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--puck", type=str, default="sine", choices=list(algo_mapping.keys())
    )
    parser.add_argument(
        "--bar", type=str, default="ppo", choices=list(algo_mapping.keys())
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--discrete", action="store_true", default=False)
    parser.add_argument("--discrete-k", type=int, default=7)
    parser.add_argument("--eps-test", type=float, default=0.005)
    parser.add_argument("--eps-train", type=float, default=1.0)
    parser.add_argument("--eps-train-final", type=float, default=0.05)
    parser.add_argument(
        "--eps-train-decay", type=str, default="exp", choices=["exp", "lin", "const"]
    )
    parser.add_argument("--buffer-size", type=int, default=10000)
    parser.add_argument("--stack-num", type=int, default=5)
    parser.add_argument("--exploration-noise", type=bool, default=True)
    parser.add_argument("--target-update-freq", type=int, default=500)
    parser.add_argument("--epoch", type=int, default=20)
    parser.add_argument("--step-per-epoch", type=int, default=10000)
    parser.add_argument("--step-per-collect", type=int, default=10)
    parser.add_argument("--update-per-step", type=float, default=0.1)
    parser.add_argument("--repeat-per-collect", type=int, default=2)
    parser.add_argument("--episode-per-test", type=int, default=100)
    parser.add_argument("--episode-per-collect", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--training-num", type=int, default=10)
    parser.add_argument("--test-num", type=int, default=100)
    parser.add_argument("--logdir", type=str, default="log")
    parser.add_argument("--render", type=float, default=0.0)
    parser.add_argument(
        "--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu"
    )

    parser.add_argument("--wandb-save-interval", type=int, default=1)
    parser.add_argument("--wandb-project", type=str, default="ds251_project")
    parser.add_argument("--wandb-name", type=str, required=True)
    parser.add_argument("--wandb-entity", type=str, default="mitulvardhan")
    parser.add_argument("--wandb-run-id", type=str, default=None)

    parser.add_argument("--trainer", type=str, default="on", choices=["off", "on"])
    parser.add_argument("--save", action="store_true", default=False)
    parser.add_argument("--load-puck-id", type=str, default=None)
    parser.add_argument("--load-bar-id", type=str, default=None)
    parser.add_argument("--run-id", type=str, default=None)

    return parser.parse_args()


def init_and_call_policy():
    """Initialises and calls policies for the agent puck and bar

    Returns:
        Tuple[Policy, Policy]: Returns the policies for puck and bar
    """
    if "call_params" in puck_params[args.puck]:
        puck_params_init = (
            puck_params[args.puck]["init_params"]
            if "init_params" in puck_params[args.puck]
            else {}
        )
        puck_params_call = (
            puck_params[args.puck]["call_params"]
            if "call_params" in puck_params[args.puck]
            else {}
        )

        policy_puck = algo_mapping[args.puck](**puck_params_init)(**puck_params_call)
    else:
        policy_puck = algo_mapping[args.puck](**puck_params[args.puck])

    if "call_params" in bar_params[args.bar]:
        bar_params_init = (
            bar_params[args.bar]["init_params"]
            if "init_params" in bar_params[args.bar]
            else {}
        )
        bar_params_call = (
            bar_params[args.bar]["call_params"]
            if "call_params" in bar_params[args.bar]
            else {}
        )

        policy_bar = algo_mapping[args.bar](**bar_params_init)(**bar_params_call)
    else:
        policy_bar = algo_mapping[args.bar](**bar_params[args.bar])

    return (policy_puck, policy_bar)


def load_policy(policy_puck, policy_bar):
    """Loads the policy if the load_puck_id and load_bar_id are not None

    Args:
        policy_puck (Policy): Puck policy to be loaded into
        policy_bar (Policy): Bar policy to be loaded into

    Returns:
        Tuple[Policy, Policy]: Returns the policy after loading if any
    """
    if args.load_puck_id is not None:
        print("Loading Puck Policy..")
        if args.device == "cuda":
            policy_puck.load_state_dict(
                torch.load(
                    "saved_policies/{}/puck_{}.pth".format(args.load_puck_id, args.puck)
                )
            )
        else:
            policy_puck.load_state_dict(
                torch.load(
                    "saved_policies/{}/puck_{}.pth".format(
                        args.load_puck_id, args.puck
                    ),
                    map_location=torch.device("cpu"),
                )
            )

    if args.load_bar_id is not None:
        print("Loading Bar Policy..")
        if args.device == "cuda":
            policy_bar.load_state_dict(
                torch.load(
                    "saved_policies/{}/bar_{}.pth".format(args.load_bar_id, args.bar)
                )
            )
        else:
            policy_bar.load_state_dict(
                torch.load(
                    "saved_policies/{}/bar_{}.pth".format(args.load_bar_id, args.bar),
                    map_location=torch.device("cpu"),
                )
            )
    return policy_puck, policy_bar


def train():
    """Trains the agent puck and bar

    Raises:
        Exception: If arguments are not set
        Exception: If proper algorithm is not used with proper trainer
    """
    if args is None:
        raise Exception("args not set")

    print("Using device: ", args.device)
    env = MakeEnv(**env_params["train"]).create_env()
    args.state_shape = env.observation_space.shape
    args.action_shape = env.action_space.shape

    # Create training and testing environments
    (train_envs_obj, train_envs) = make_envs(args.training_num, **env_params["train"])
    train_envs = SubprocVectorEnv(train_envs)
    (test_envs_obj, test_envs) = make_envs(args.test_num, **env_params["test"])
    test_envs = SubprocVectorEnv(test_envs)
    print(
        f"Created {args.training_num} training environments and {args.test_num} test environments.."
    )

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    train_envs.seed(args.seed)
    test_envs.seed(args.seed)

    # define policies for puck and bar here
    print("Initialising Policies..")
    policy_puck, policy_bar = init_and_call_policy()
    # Loading policies
    policy_puck, policy_bar = load_policy(policy_puck, policy_bar)
    # Create Two Agent Policy
    policy = TwoAgentPolicy(
        (policy_puck, policy_bar),
        observation_space=env.observation_space,
        action_space=env.action_space,
    )

    print("Creating replay buffer with train and test collector..")
    if (args.puck == "sac" and puck_params["sac"]["call_params"]["recurrent"]) or (
        args.bar == "sac" and bar_params["sac"]["call_params"]["recurrent"]
    ):
        buffer = VectorReplayBuffer(
            args.buffer_size, args.training_num, stack_num=args.stack_num
        )
    else:
        buffer = VectorReplayBuffer(args.buffer_size, args.training_num)

    train_collector = Collector(
        policy,
        train_envs,
        buffer,
        exploration_noise=args.exploration_noise,
    )
    test_collector = Collector(
        policy, test_envs, exploration_noise=args.exploration_noise
    )

    logger = WandbLogger(
        save_interval=args.wandb_save_interval,
        project=args.wandb_project,
        name=args.wandb_name,
        entity=args.wandb_entity,
        run_id=args.wandb_run_id,
    )

    if not args.save:
        save_checkpoint_fn = None

    print("Starting training and testing model ..")
    if (
        args.trainer == "off"
        and puck_params[args.puck].get("trainer", "off") == "off"
        and bar_params[args.bar].get("trainer", "off") == "off"
    ):
        result = offpolicy_trainer(
            policy,
            train_collector,
            test_collector,
            args.epoch,
            args.step_per_epoch,
            args.step_per_collect,
            args.episode_per_test,
            args.batch_size,
            train_fn=train_fn,
            test_fn=test_fn,
            logger=logger,
            update_per_step=args.update_per_step,
            save_checkpoint_fn=save_checkpoint_fn,
        )
    elif (
        args.trainer == "on"
        and puck_params[args.puck].get("trainer", "on") == "on"
        and bar_params[args.bar].get("trainer", "on") == "on"
    ):
        result = ts.trainer.onpolicy_trainer(
            policy,
            train_collector,
            test_collector,
            max_epoch=args.epoch,
            step_per_epoch=args.step_per_epoch,
            repeat_per_collect=args.repeat_per_collect,
            episode_per_test=args.episode_per_test,
            batch_size=args.batch_size,
            episode_per_collect=args.episode_per_collect,
            logger=logger,
            save_checkpoint_fn=save_checkpoint_fn,
        )
    else:
        raise Exception("Invalid trainer with algorithm")

    pprint.pprint(result)


if __name__ == "__main__":
    args = get_args()
    train()
