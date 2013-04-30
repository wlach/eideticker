import datetime

class LoggingMixin(object):

    @classmethod
    def log(cls, msg):
        datestr = datetime.datetime.now().strftime("%b %d %H:%M:%S %Z")
        print "%s %s | %s" % (datestr, cls.__name__, msg)
