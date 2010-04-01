# -*- coding: utf-8 -*-

import optparse

class OptionError(Exception):
    def __init__(self, msg):
        self.msg = msg

class OptionFormatter(optparse.IndentedHelpFormatter):
    def __init__(self, appver, longname):
        self.appver = appver
        self.longappname = longname
        optparse.IndentedHelpFormatter.__init__(self)

    def format_usage(self, usage):
        template = u'{name} {version}\nИспользование:\n  {usage}'
        message = template.format(name = self.longappname, version=self.appver, usage=usage)
        return optparse._(message)

    def format_option_strings(self, option):
        self._short_opt_fmt = "%s"
        if option.takes_value():
            metavar = option.metavar or option.dest.upper()
            short_opts = [self._short_opt_fmt % sopt
                          for sopt in option._short_opts]
            long_opts = [self._long_opt_fmt % (lopt, metavar)
                         for lopt in option._long_opts]
        else:
            short_opts = option._short_opts
            long_opts = option._long_opts

        if self.short_first:
            opts = short_opts + long_opts
        else:
            opts = long_opts + short_opts

        return ", ".join(opts)

class OptionParser(optparse.OptionParser):
    def _add_version_option(self):
        self.add_option('-v', '--version', action='version', help=optparse._(u'отобразить версию программы и выйти'))

    def error(self, msg):
        raise OptionError(msg)
