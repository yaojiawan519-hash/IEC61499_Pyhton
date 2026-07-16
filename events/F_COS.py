from BasicFB import *
import math

class F_COS(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "F_COS", "cosine in radians", Position=position)
        self.addInputEvent("REQ", "Service Request")
        self.addOutputEvent("CNF", "Confirmation of Requested Service")
        self.addInputVar("IN", "ANY_REAL", "Event Input Qualifier", 0.0)
        self.addOutputVar("OUT", "ANY_REAL", "Event Output Qualifier", 0.0)

    def eventTrigger(self, event):
        if event != "REQ":
            return
        OUT = math.cos(self.getVarValue("IN"))   # OUT := COS(IN)
        self.setVarValue("OUT", OUT)
        print(f"[{self.Name}] REQ -> OUT={OUT}")
        self.sendOutputEvent("CNF")
