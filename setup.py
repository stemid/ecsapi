from setuptools import setup, find_packages

try:
    plugins = open('/etc/ecs_plugins.cfg')
except:
    plugins = open('plugins.cfg')

setup(
    name="ECSPlugins",
    version="0.1",
    description="ECS Plugins",
    author="Stefan Midjich",
    packages=find_packages(),
    entry_points=plugins.read()
)
