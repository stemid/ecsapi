# Also an example that simply logs data to the logging handler provided.

class LoggingPlugin(object):
    plugin_name = 'LoggingPlugin'

    def __init__(self, config, logging, **kw):
        self.l = logging
        self.config = config
        self.request = kw['request']

    def run(self):
        self.l.info('Request params: {params}'.format(
            params=self.request.params.keys()
        ))
