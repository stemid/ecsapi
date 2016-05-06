# Dispatch alerts to external executables.
import json
import subprocess
import threading
import errno
from datetime import datetime

class DispatchPlugin(object):
    plugin_name = 'DispatchPlugin'

    def __init__(self, config, logging, **kw):
        self.l = logging
        self.config = config
        self.request = kw['request']
        self.plugin_name = self.l.name.lstrip('ecs_')
        self.now = datetime.now()

        # Use global timeout if available
        if self.config.has_option(self.plugin_name, 'timeout'):
            self.timeout = self.config.getint(self.plugin_name, 'timeout')
        else:
            self.timeout = False

    # Helper method to timeout command dispatches
    def _timeout_callback(self, p):
        if p.poll() is None:
            try:
                p.kill()
                self.l.error('Process {pid} taking too long, killing'.format(
                    pid=p.pid
                ))
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise

    # Helper method to extract commands and inputs from the configuration
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

                # If no global timeout is defined, try to find local
                if self.timeout is False:
                    try:
                        local_timeout = self.config.getint(
                            self.plugin_name,
                            'timeout{0}'.format(
                                key.split('command')[-1]
                            )
                        )
                    except Exception as e:
                        self.l.debug(str(e))
                        local_timeout = False
                        pass
                else:
                    local_timeout = False

                commands.append({
                    'command': command,
                    'input': input_data,
                    'timeout': local_timeout
                })

        return commands

    # run() is executed by plugin engine
    def run(self):
        request = self.request

        if not self.config.has_section(self.plugin_name):
            self.l.error('Must configure {plugin}'.format(
                plugin=self.plugin_name
            ))
            raise NotImplementedError

        alert = request.params.get('status', '').split(',')[0]
        alert_time_period_state = request.params.get(
            'alert_time_period_state',
            ''
        )

        # Check if alert is in scheduled downtime state
        if alert_time_period_state == 'DOWN':
            self.l.debug('Monitor {monitor}: Skipped while in downtime period'.format(
                monitor=request.params.get('monitor', '')
            ))
        else:
            for command in self.get_commands():
                if self.timeout:
                    timeout = self.timeout
                else:
                    timeout = command['timeout']

                self.execute(
                    command['command'],
                    command['input'],
                    timeout
                )

    # This executes the configured commands
    def execute(self, command, input_data=False, timeout=False):
        request = self.request

        command_args = []
        _command_args = command.split(' ')

        # Check if relevant values are set
        if not len(request.params.get('status', '')):
            raise StandardError('Must provide status argument')

        if not len(request.params.get('monitor', '')):
            raise StandardError('Must provide monitor argument')

        if not len(request.params.get('device', '')):
            raise StandardError('Must provide device_hostname argument')

        # This dict gets passed into command formats and input formats
        format_data = {
            'time': self.now,
            'alert': request.params.get('alert', ''),
            'status': request.params.get('status', ''),
            'monitor': request.params.get('monitor', ''),
            'organisation': request.params.get('organisation', ''),
            'alert_time_period_state': request.params.get(
                'alert_time_period_state',
                ''
            ),
            'device': request.params.get('device', ''),
            'device_hostname': request.params.get('device_hostname', ''),
            'monitor_name': request.params.get('monitor_name', ''),
            'monitor_type': request.params.get('monitor_type', '')
        }

        # Format command arguments
        for _cmd in _command_args:
            command_args.append(_cmd.format(format_data))

        if input_data:
            proc_stdin = subprocess.PIPE
        else:
            proc_stdin = None

        proc = subprocess.Popen(
            command_args,
            stdin=proc_stdin
        )

        self.l.debug('Executed command[{pid}]: {input} | {command}'.format(
            input=input_data,
            command=command_args,
            pid=proc.pid
        ))

        # Start a thread to create a timeout poller for proc
        timer = threading.Timer(timeout, self._timeout_callback, [proc])
        timer.start()

        # Handle process input
        if input_data:
            # Process JSON list as input
            if input_data.startswith('[') and input_data.endswith(']'):
                input_lines = json.loads(input_data)
                input_data = '\n'.join(input_lines)

            (stdout, stderr) = proc.communicate(input_data.format(format_data))

            if stderr:
                self.l.error(
                    'Error in process communication: {stderr}'.format(
                        stderr=stderr
                    )
                )
        else:
            (stdout, stderr) = proc.communicate()

        # End the timer thread if it hasn't already
        timer.cancel()
        timer.join()

        if stderr:
            self.l.error('Error in process communication: {stderr}'.format(
                stderr=stderr
            ))

        if stdout:
            self.l.info('stdout: {stdout}'.format(
                stdout=stdout
            ))
