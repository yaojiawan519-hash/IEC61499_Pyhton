class runTime:

    def __init__(self, App):
        self.App = App
        self.rstart = self._find_restart()

    def _find_restart(self):
        """在网络中查找 E_RESTART SIFB（按 FBType）。"""
        for fb in self.App.FunctionBlocks:
            if getattr(fb, "FBType", "") == "E_RESTART":
                return fb
        return None

    def run(self):
        if self.rstart is not None:
            self.rstart.cold()

    def warm(self):
        if self.rstart is not None:
            self.rstart.warm()

    def stop(self):
        if self.rstart is not None:
            self.rstart.stop()
