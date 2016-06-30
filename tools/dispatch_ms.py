#!/usr/bin/env python
# This is a dispatch command that can be used with the dispatch_plugin to send
# alerts for monitorscout. It works with the MS API to fetch alert contacts
# from MS and determine how to send the alert.

from __future__ import print_function

import threading
import subprocess
from pprint import pprint as pp
from sys import exit, stderr
from argparse import ArgumentParser, FileType
from logging import Formatter, getLogger, DEBUG, WARN, INFO
from logging.handlers import SysLogHandler, RotatingFileHandler
try:
    from configparser import RawConfigParser
    from xmlrpc.client import ServerProxy, Error
except ImportError:
    from ConfigParser import RawConfigParser
    from xmlrpclib import ServerProxy, Error


parser = ArgumentParser(
    description=('Arguments accepted are the same as the format values from'
                 ' dispatch_plugin. Please provide a valid configuration or'
                 ' this script will fail.')
)

# Pretty much same arguments here as in format_data dict from the 
# dispatch_plugin
parser.add_argument(
    '--config',
    type=FileType('r'),
    help='Additional configuration'
)

parser.add_argument(
    '--time'
)

parser.add_argument(
    '--alert',
)

parser.add_argument(
    '--status'
)

parser.add_argument(
    '--monitor'
)

parser.add_argument(
    '--organisation',
    required=True
)

parser.add_argument(
    '--alert_time_period_state'
)

parser.add_argument(
    '--device',
    required=True
)

parser.add_argument(
    '--device_hostname'
)

parser.add_argument(
    '--monitor_name'
)

parser.add_argument(
    '--monitor_type'
)

args = parser.parse_args()

alert_data = {
    'time': args.time,
    'alert': args.alert,
    'status': args.status,
    'monitor': args.monitor,
    'organisation': args.organisation,
    'alert_time_period_state': args.alert_time_period_state,
    'device': args.device,
    'device_hostname': args.device_hostname,
    'monitor_name': args.monitor_name,
    'monitor_type': args.monitor_type
}

config = RawConfigParser()
config.read(['ecs.cfg', 'ecs_local.cfg', '/etc/ecs.cfg'])
if args.config:
    config.readfp(args.config)

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


# Timeout callback helper function
def timeout_callback(self, p):
    if p.poll() is None:
        try:
            p.kill()
            l.error('Process {pid} taking too long, killed'.format(
                pid=p.pid
            ))
        except OSError as e:
            if e.errno != errno.ESRCH:
                raise


# Execute alert command
def alert_command(command, input_data):
    proc_stdin = subprocess.PIPE

    proc = subprocess.Popen(
        command,
        stdin=proc_stdin
    )

    timer = threading.Timer(
        config.getint('DispatchPlugin', 'timeout'),
        timeout_callback,
        [proc]
    )
    timer.start()

    (stdout, stderr) = proc.communicate(input_data)

    if stderr:
        l.error('Alert command error: {error}'.format(
            error=stderr
        ))

    timer.cancel()
    timer.join()

    return stdout


# Send an E-mail alert
def email_alert(recipient, alert={}):
    email_message = (
        'Alert from www.monitorscout.com\n'
        '\n'
        'Device name: {device_hostname}\n'
        'Monitor name: {monitor_name}\n'
        'State: {status}\n'
        'Time: {time}\n'
        'Error: {error_msg}\n'
        '\n'
        'Alert Time Period State: {alert_time_period_state}\n'
        '\n'
        'Device: https://monitorscout.com/device/{device}\n'
        'Monitor: https://monitorscout.com/monitor/{device}/{monitor_type}/{monitor}\n'
        'Acknowledge alert: https://monitorscout.com/alert/unhandled/{monitor_type}_alert/{monitor}/\n'
        '\n'
        '/ Delivered from www.monitorscout.com via Cygatehosting ECS API\n'
    ).format(**alert)

    l.debug('Sending e-mail message to {rcpt}'.format(
        rcpt=recipient
    ))

    alert['subject'] = config.get('DispatchPlugin', 'email_subject').format(
        **alert
    )

    alert['email'] = recipient
    alert['from'] = config.get('DispatchPlugin', 'email_from')
    alert['return_path'] = config.get('DispatchPlugin', 'email_return_path')
    alert['reply_to'] = config.get('DispatchPlugin', 'email_reply_to')

    command = config.get('DispatchPlugin', 'email_cmd')
    cmd_args = []
    for _cmd in command.split(' '):
        cmd_args.append(_cmd.format(**alert))

    l.debug('Executing email command: {cmd}'.format(
        cmd=cmd_args
    ))
    stdout = alert_command(cmd_args, email_message)
    l.debug('Command finished: {stdout}'.format(
        stdout=stdout
    ))


# Send pager alert
def pager_alert(recipient, alert={}):
    pager_message = (
        'Alert from www.monitorscout.com\n'
        '\n'
        'Device name: {device_hostname}\n'
        'Monitor name: {monitor_name}\n'
        'State: {status}\n'
        'Time: {time}\n'
        'Error: {error_msg}\n'
    ).format(**alert)

    l.debug('Sending pager message')

    alert['pager'] = recipient

    command = config.get('DispatchPlugin', 'pager_cmd')
    cmd_args = []
    for _cmd in command.split(' '):
        cmd_args.append(_cmd.format(**alert))

    l.debug('Executing pager command: {cmd}'.format(
        cmd=cmd_args
    ))
    stdout = alert_command(cmd_args, pager_message)
    l.debug('Command finished: {stdout}'.format(
        stdout=stdout
    ))


if not config.get('DispatchPlugin', 'ms_api_host'):
    parser.print_help()
    exit(1)

try:
    # Connect to MS API
    server = ServerProxy('http://{ms_api_host}:{ms_api_port}/'.format(
        ms_api_host=config.get('DispatchPlugin', 'ms_api_host'),
        ms_api_port=config.getint('DispatchPlugin', 'ms_api_port')
    ))

    # Get a session ID
    sid = server.login(
        config.get('DispatchPlugin', 'ms_api_username'),
        config.get('DispatchPlugin', 'ms_api_password'),
        config.get('DispatchPlugin', 'ms_api_account')
    )
except Error as e:
    print('Connection to MS API failed: {error}'.format(
        error=str(e)
    ), file=stderr)
    exit(1)

# Get the alert data
_alert = None
if args.monitor_type == 'monitor':
    _alert = server.monitor.r_get_alerts(sid, args.alert, '')
elif args.monitor_type == 'passive_monitor':
    _alert = server.monitor.passive.r_get_alerts(sid, args.alert, '')
elif args.monitor_type == 'process_monitor':
    _alert = server.device.process.monitor.r_get_alerts(sid, args.alert, '')
elif args.monitor_type == 'metric_monitor':
    _alert = server.metric.monitor.r_get_alerts(sid, args.alert, '')

# Add the error_msg to our own dict of alert_data
if _alert:
    _alert_data = _alert['entity_data'].get(args.alert)
    alert_data['error_msg'] = _alert_data['error_msg']


# Contact handling code, handles stuff like if contacts should receive alerts
# and what type of alerts they should receive.
contacts = []

# Get the device contacts
device_id = args.device
device_data = server.device.r_get2(sid, {'id': device_id})

if not len(device_data['matches']):
    l.debug('No such device found')
else:
    device = device_data['entity_data'][device_data['matches'][0]]
    device_alerts_enabled = device.get('alerts_enabled')

    if device_alerts_enabled:
        # Get the contacts of the first device in the search results
        dev_contacts = device.get('alert_user_contacts')

        if not len(dev_contacts):
            l.debug('{device}: No contacts found for device'.format(
                device=device_id
            ))
        else:
            contacts.extend(dev_contacts)

        dev_users = device.get('alert_users')

        if not len(dev_users):
            l.debug('{device}: No users found for device'.format(
                device=device_id
            ))
        else:
            contacts.extend(dev_users)
    else:
        l.debug('{device}: Alerts disabled for device, skipping'.format(
            device=device_id
        ))


# Get monitor contacts
monitor_id = args.monitor
if args.monitor_type == 'passive_monitor':
    monitor_data = server.monitor.passive.r_get2(sid, {'id': monitor_id})
else:
    monitor_data = server.monitor.r_get2(sid, {'id': monitor_id})

if not len(monitor_data['matches']):
    l.debug('No such monitor found')
else:
    monitor = monitor_data['entity_data'][monitor_data['matches'][0]]
    monitor_alerts_enabled = monitor.get('alerts_enabled')

    if monitor_alerts_enabled:
        mon_contacts = monitor.get('alert_user_contacts')

        if not len(mon_contacts):
            l.debug('No contacts found on monitor')
        else:
            contacts.extend(mon_contacts)

        mon_users = monitor.get('alert_users')

        if not len(mon_users):
            l.debug('{monitor}: No users found on monitor'.format(
                monitor=monitor_id
            ))
        else:
            contacts.extend(mon_users)
    else:
        l.debug('{monitor}: Alerts disabled for monitor, skipping'.format(
            monitor=monitor_id
        ))

# Sort the found contacts so we have unique ID values.
sorted_contacts = sorted(set(contacts))
l.debug('Processing contacts: {contacts}'.format(
    contacts=sorted_contacts
))

# For all contacts found we attempt to send e-mail and pager messages
# depending on their settings.
for contact in sorted_contacts:
    # Fetch contact JSON data from MS API
    contact_data = server.user.contact.r_get2(sid, {'id': contact})

    if not len(contact_data['matches']):
        l.debug('{contact}: No such contact found'.format(
            contact=contact
        ))

        contact_data = server.user.r_get2(sid, {'id': contact})

    if not len(contact_data['matches']):
        l.debug('{contact}: No such user found'.format(
            contact=contact
        ))
        continue

    c = contact_data['entity_data'][contact_data['matches'][0]]

    if c.get('notify_by_email', False):
        if not c.get('email_verified', False):
            l.debug('{contact}: Email not verified'.format(
                contact=c.get('email', c.get('id'))
            ))

        if not c.get('email', False):
            l.debug('{contact}: Email not present'.format(
                contact=c.get('id')
            ))

        if c.get('email_verified') and c.get('email'):
            try:
                email_alert(
                    c.get('email'),
                    alert_data
                )
            except Exception as e:
                l.exception('Email alert failed with exception')
                pass

    if c.get('notify_by_pager', False):
        if not c.get('pager_verified', False):
            l.debug('{contact}: Pager not verified'.format(
                contact=c.get('pager_number', c.get('id'))
            ))

        if not c.get('pager_number', False):
            l.debug('{contact}: Pager not present'.format(
                contact=c.get('id')
            ))

        if c.get('pager_verified') and c.get('pager_number'):
            try:
                pager_alert(
                    c.get('pager_number'),
                    alert_data
                )
            except Exception as e:
                l.exception('Pager alert failed with exception')
                pass
