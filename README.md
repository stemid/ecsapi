# Monitorscout.com ECS API

Monitorscout.com has an Event Callback Server feature where alerts can be sent as HTTP GET requests to an external API. 

This is an external API service to receive those alerts and process them. 

# Configuration

  * ecs.cfg - defaults
  * ecs\_local.cfg - overrides

# Plugins

Plugins do everything, the API feature is only to execute all the plugins in order. 

See sample\_plugin or logging\_plugin for examples. 

Activate plugins by editing entry\_points in setup.py. 

    [ecs.plugins]
    SamplePlugin = sample_plugin:SamplePlugin
    LoggingPlugin = logging_plugin:LoggingPlugin

Remove a plugin from this list to disable it, and then run setup.py. 

  sudo python setup.py install

No need to restart server after that. 

# TODO

  * Auto-generate entry\_points for plugins in setup.py

## Links

  * http://base-art.net/Articles/64/
  * http://aroberge.blogspot.se/2008/12/plugins-part-6-setuptools-based.html
