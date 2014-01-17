import datetime
import mozlog

_handler = mozlog.StreamHandler()
_handler.setFormatter(mozlog.MozFormatter(include_timestamp=True))
logger = mozlog.getLogger('Eideticker', _handler)


class LoggingMixin(object):

    @classmethod
    def log(cls, msg):
        datestr = datetime.datetime.now().strftime("%b %d %H:%M:%S %Z")
        print "%s %s | %s" % (datestr, cls.__name__, msg)
