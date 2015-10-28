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

    def get_commands(self):
        commands = []
        for key, item in self.config.items(self.plugin_name):
            if key.startswith('command'):
                command = item
                # Find corresponding input or use False
                try:
                    input_data = self.config.get(
                        self.plugin_name,
                        'input{0}'.format(
                            key.split('command')[-1]
                        )
                    )
                except Exception as e:
                    self.l.debug(str(e))
                    input_data = False
                    pass

                if input_data == 'False':
                    input_data = False

                commands.append({
                    'command': command,
                    'input': input_data
                })

        return commands

    def run(self):
        if not self.config.has_section(self.plugin_name):
            self.l.error('Must configure {plugin}'.format(
                plugin=self.plugin_name
            ))
            raise NotImplementedError

        for command in self.get_commands():
            self.execute(command['command'], command['input'])

    def execute(self, command, input_data=False):
        request = self.request

        command_args = []
        _command_args = command.split(' ')

        # Format command arguments
        for _cmd in _command_args:
            command_args.append(
                _cmd.format(
                    alert=request.params.get('alert', ''),
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

        if input_data:
            proc_stdin = subprocess.PIPE
        else:
            proc_stdin = None

        self.l.debug('Executing command: {input} | {command}'.format(
            input=input_data,
            command=command_args
        ))

        command = subprocess.Popen(
            command_args,
            stdin=proc_stdin
        )

        # Handle process input
        if input_data:
            # Process JSON list as input
            if input_data.startswith('[') and input_data.endswith(']'):
                input_lines = json.loads(input_data)
                input_data = '\n'.join(input_lines)

            (stdout, stderr) = command.communicate(
                input_data.format(
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

        else:
            (stdout, stderr) = command.communicate()

        if stderr:
            self.l.error('Error in process communication: {stderr}'.format(
                stderr=stderr
            ))

        if stdout:
            self.l.info('stdout: {stdout}'.format(
                stdout=stdout
            ))
