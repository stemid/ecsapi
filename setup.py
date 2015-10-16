from setuptools import setup, find_packages

#plugins_path = './plugins'
#packages = find_packages(plugins_path)

setup(
    name="ECSPlugins",
    version="0.1",
    description="ECS Plugins",
    author="Stefan Midjich",
    packages=find_packages(),
    entry_points="""
    [ecs.plugins]
    SamplePlugin = sample_plugin:SamplePlugin
    LoggingPlugin = logging_plugin:LoggingPlugin
    """
)
