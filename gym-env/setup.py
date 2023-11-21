from setuptools import setup

setup(
    name="gym_env",  # Use same name as sibling directory.
    version="1.0.0",  # Version number.
    install_requires=[
        "gym",
        "numpy",
        "torch",
        "tianshou",
        "wandb",
        "smurves",
    ],  # Python packages required by our environments.
)
