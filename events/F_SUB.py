from BasicFB import *

class F_SUB(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "F_SUB", "Subtracts two number values", Position=position)
        self.addInputEvent("REQ", "Normal Execution Request")
        self.addOutputEvent("CNF", "Execution Confirmation")
        self.addInputVar("IN1", "ANY_MAGNITUDE", "First function input", 0)
        self.addInputVar("IN2", "ANY_MAGNITUDE", "Second function input", 0)
        self.addOutputVar("OUT", "ANY_MAGNITUDE", "IN2 subtracted from IN1", 0)

    def eventTrigger(self, event):
        if event != "REQ":
            return
        OUT = self.getVarValue("IN1") - self.getVarValue("IN2")   # OUT := IN1 - IN2
        self.setVarValue("OUT", OUT)
        print(f"[{self.Name}] REQ -> OUT={OUT}")
        self.sendOutputEvent("CNF")
