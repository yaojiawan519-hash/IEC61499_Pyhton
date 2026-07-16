from BasicFB import *
import math

class F_SQRT(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "F_SQRT", "square root", Position=position)
        self.addInputEvent("REQ", "Service Request")
        self.addOutputEvent("CNF", "Confirmation of Requested Service")
        self.addInputVar("IN", "ANY_REAL", "Event Input Qualifier", 0.0)
        self.addOutputVar("OUT", "ANY_REAL", "Event Output Qualifier", 0.0)

    def eventTrigger(self, event):
        if event != "REQ":
            return
        IN = self.getVarValue("IN")
        if IN < 0:                        # 负数开方：OUT 置 0，不发 CNF
            print(f"[{self.Name}] REQ ignored, sqrt of negative (IN={IN})")
            self.setVarValue("OUT", 0.0)
            return
        OUT = math.sqrt(IN)               # OUT := SQRT(IN)
        self.setVarValue("OUT", OUT)
        print(f"[{self.Name}] REQ -> OUT={OUT}")
        self.sendOutputEvent("CNF")
