# Sample plugin, does nothing at all.

class SamplePlugin(object):
    """Plugins must have a class ending in the word Plugin, but this can be 
    configured in setup.py.
    """

    def __init__(self, config, logging, **kw):
        """The main plugin class configured as entry_point in setup.py must
        also have an __init__ method.

        This does not have to do much but takes at least two arguments, with
        a RawConfigParser object and a logging object.

        The last keyword arguments are optional and not implemented yet.
        """
        self.plugin_name = 'Sample'

    def run(self):
        """This method is run after each plugin is instantiated. It takes no
        arguments and should instead take class attributes set by __init__.
        """
        return True
