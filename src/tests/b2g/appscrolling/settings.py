from eideticker.test import B2GAppActionTest

class Test(B2GAppActionTest):
    def __init__(self, testinfo, appname, **kwargs):
        B2GAppActionTest.__init__(self, testinfo, appname, **kwargs)

        self.cmds = []
        for i in range(5):
            self.cmds.append(['scroll_down'])
            self.cmds.append(['scroll_up'])
