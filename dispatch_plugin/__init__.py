# Dispatch alerts to external executables.
import subprocess

class DispatchPlugin(object):
    plugin_name = 'DispatchPlugin'

    def __init__(self, config, logging, **kw):
        self.l = logging
        self.config = config
        self.request = kw['request']
        self.plugin_name = self.l.name.lstrip('ecs_')

    #def execute(path, **
    def run(self):
        request = self.request

        if not self.config.has_section(self.plugin_name):
            self.l.error('Must configure {plugin}'.format(
                plugin=self.plugin_name
            ))
            raise NotImplementedError

        command_args = []
        _command_args = self.config.get(
            self.plugin_name, 'command'
        ).split(' ')

        # Format command arguments
        for _cmd in _command_args:
            command_args.append(
                _cmd.format(
                    status=request.params.get('status', ''),
                    monitor=request.params.get('monitor', ''),
                    organisation=request.params.get('oranisation', ''),
                    alert_time_period_state=request.params.get(
                        'alert_time_period_state',
                        ''
                    ),
                    device=request.params.get('device', ''),
                    device_hostname=request.params.get('device_hostname', ''),
                    monitor_name=request.params.get('monitor_name', ''),
                    monitor_type=request.params.get('monitor_type', '')
                )
            )

        command = subprocess.Popen(
            command_args
        )

        # Handle process input
        if self.config.get(self.plugin_name, 'input') == 'False':
            (stdout, stderr) = command.communicate()
        else:
            (stdout, stderr) = command.communicate(
                self.config.get(self.plugin_name, 'input').format(
                    status=request.params.get('status', ''),
                    monitor=request.params.get('monitor', ''),
                    organisation=request.params.get('oranisation', ''),
                    alert_time_period_state=request.params.get(
                        'alert_time_period_state',
                        ''
                    ),
                    device=request.params.get('device', ''),
                    device_hostname=request.params.get('device_hostname', ''),
                    monitor_name=request.params.get('monitor_name', ''),
                    monitor_type=request.params.get('monitor_type', '')
                )
            )

        if stderr:
            self.l.error('Command failed: {stderr}'.format(
                stderr=stderr
            ))

        if stdout:
            self.l.info('stdout: {stdout}'.format(
                stdout=stdout
            ))
