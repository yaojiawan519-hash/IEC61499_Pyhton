from BasicFB import *
import math

class F_ABS(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "F_ABS", "absolute value", Position=position)
        self.addInputEvent("REQ", "Service Request")
        self.addOutputEvent("CNF", "Confirmation of Requested Service")
        self.addInputVar("IN", "ANY_NUM", "Event Input Qualifier", 0)
        self.addOutputVar("OUT", "ANY_NUM", "Event Output Qualifier", 0)

    def eventTrigger(self, event):
        if event != "REQ":
            return
        OUT = abs(self.getVarValue("IN"))   # OUT := ABS(IN)
        self.setVarValue("OUT", OUT)
        print(f"[{self.Name}] REQ -> OUT={OUT}")
        self.sendOutputEvent("CNF")
