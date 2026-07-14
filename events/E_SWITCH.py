from BasicFB import *

class E_SWITCH(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_SWITCH",
                         "Switching (demultiplexing) an event based on boolean input G",
                         Position=position)
        self.addInputEvent("EI", "Event Input")
        self.addOutputEvent("EO0", "Output, switched from EI when G=0")
        self.addOutputEvent("EO1", "Output, switched from EI when G=1")
        self.addInputVar("G", "BOOL", "Switch EI to EO0 when G=0, to EO1 when G=1", 0)

    def eventTrigger(self, event):
        if event == "EI":
            G = self.getVarValue("G")
            if G == 0:
                self.sendOutputEvent("EO0")
            elif G == 1:
                self.sendOutputEvent("EO1")
            # G 非法值时丢弃事件
