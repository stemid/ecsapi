# Web API for Monitorscout ECS (Event Callback Server)
# by Stefan Midjich <swehack@gmail.com>

try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
    pass

from json import dumps as json_dumps
from logging import Formatter, getLogger, DEBUG, WARN, INFO
from logging.handlers import SysLogHandler, RotatingFileHandler

import pkg_resources
from bottle import get, post, route, run, default_app, debug, request

config = RawConfigParser()
config.readfp(open('ecs.cfg'))
config.read([
    'ecs_local.cfg',
    '/etc/ecs.cfg'
])

# Setup logging
formatter = Formatter(config.get('logging', 'log_format'))
l = getLogger('ecs')
if config.get('logging', 'log_handler') == 'syslog':
    syslog_address = config.get('logging', 'syslog_address')

    if syslog_address.startswith('/'):
        h = SysLogHandler(
            address=syslog_address,
            facility=SysLogHandler.LOG_LOCAL0
        )
    else:
        h = SysLogHandler(
            address=(
                config.get('logging', 'syslog_address'),
                config.get('logging', 'syslog_port')
            ),
            facility=SysLogHandler.LOG_LOCAL0
        )
else:
    h = RotatingFileHandler(
        config.get('logging', 'log_file'),
        maxBytes=config.getint('logging', 'log_max_bytes'),
        backupCount=config.getint('logging', 'log_max_copies')
    )
h.setFormatter(formatter)
l.addHandler(h)

if config.get('logging', 'log_debug'):
    l.setLevel(DEBUG)
else:
    l.setLevel(WARN)


@get(config.get('api', 'url_path'))
def ecs():
    l.debug('Received callback from {client_ip}'.format(
        client_ip=request.remote_route[0]
    ))

    for entrypoint in pkg_resources.iter_entry_points('ecs.plugins'):
        # Get plugin class and name from entrypoint
        l.debug('Loading entry point {point}'.format(
            point=entrypoint.name
        ))
        plugin_class = entrypoint.load()
        plugin_name = entrypoint.name

        # Setup plugin log handler
        plugin_log = getLogger('ecs_'+plugin_name)
        plugin_log.addHandler(h)
        plugin_log.setLevel(DEBUG)

        # Instantiate the class
        try:
            inst = plugin_class(
                config,
                plugin_log,
                request=request
            )
        except Exception as e:
            l.error('Plugin {plugin} raised exception: {exception}: {error}'.format(
                plugin=plugin_name,
                exception=e.__class__.__name__,
                error=str(e)
            ))
            continue

        # Run plugin
        try:
            inst.run()
        except Exception as e:
            l.error('Plugin {plugin} raised exception: {exception}: {error}'.format(
                plugin=plugin_name,
                exception=e.__class__.__name__,
                error=str(e)
            ))
            continue


if __name__ == '__main__':
    run(
        host=config.get('api', 'host'),
        port=config.get('api', 'port')
    )
    debug(config.get('logging', 'log_debug'))
else:
    application = default_app()
