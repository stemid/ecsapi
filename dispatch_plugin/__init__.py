# Dispatch alerts to external executables.
import json
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

        self.l.debug('Received request: {request_params}'.format(
            request_params=request.params.keys()
        ))

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

        if self.config.get(self.plugin_name, 'input') == 'False':
            proc_stdin = None
        else:
            proc_stdin = subprocess.PIPE

        self.l.debug('Executing command: {command}'.format(
            command=command_args
        ))

        command = subprocess.Popen(
            command_args,
            stdin=proc_stdin
        )

        # Handle process input
        if self.config.get(self.plugin_name, 'input') == 'False':
            (stdout, stderr) = command.communicate()
        else:
            self.l.debug('Sending input to process: {input}'.format(
                input=self.config.get(self.plugin_name, 'input')
            ))

            # Process JSON list as input
            if self.config.get(self.plugin_name, 'input').startswith('[') \
               and self.config.get(self.plugin_name, 'input').endswith(']'):
                input_lines = json.loads(self.config.get(self.plugin_name, 'input'))

                for line in input_lines:
                    (stdout, stderr) = command.communicate(
                        line.format(
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
                        self.l.error(
                            'Error in process communication: {stderr}'.format(
                                stderr=stderr
                            )
                        )
                        break

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
            self.l.error('Error in process communication: {stderr}'.format(
                stderr=stderr
            ))

        if stdout:
            self.l.info('stdout: {stdout}'.format(
                stdout=stdout
            ))
