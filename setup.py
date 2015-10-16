from setuptools import setup, find_packages

setup(
    name="ECSPlugins",
    version="0.1",
    description="ECS Plugins",
    author="Stefan Midjich",
    packages=find_packages(),
    entry_points=open('plugins.cfg').read()
)
