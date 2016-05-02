# Dispatch plugin

Plugin dispatches alert data from ECS to a command. If available this plugin will attempt a connection to the MS API to get alert users information.

# Configuration

Configure ecs.cfg with a DispatchPlugin section. 

In this section each entry starting with command will be used to execute that command, and each entry starting with input will be used as input to stdin of the command. 

You can also specify accompanying timeout entries but timeout is an entry you can actually keep global if you just define it with no suffix. See the example. 

This is sequential so commandNumber5 will use inputNumber5 in the order they were defined. Therefore if you have 4 commands with no input you should define 4 inputs with value False if you want to use a fifth input for a fifth command. 

The following parameters can be used both in command and in input. All but the first one are directly from www.monitorscout.com ECS.

  * now - current time when plugin is executed
  * alert - alert ID
  * status - UP, DOWN
  * monitor - monitor ID
  * organisation - organisation ID
  * alert\_time\_period\_state - what state the monitor should be in according to time periods
  * device - device ID
  * device\_hostname - device hostname
  * monitor\_name - monitor name
  * monitor\_type - monitor type

Hint: You can also use JSON list syntax in input entries to input multiple lines of data into stdin. The last list member will be followed by EOF. 

## Example

    [DispatchPlugin]
    # Global timeout
    timeout = 30

    # Command definitions must have matching input definitions, they can use 
    # any unique suffix but it must match.
    command1 = echo {status}: {device_hostname}
    command2 = echo 2: {status}: {device_hostname}
    command3 = tee /tmp/output

    input1 = False
    input2 = False
    input3 = {status}: {device_hostname}
