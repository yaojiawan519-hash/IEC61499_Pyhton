from BasicFB import *

class F_DIV(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "F_DIV", "Divides two values", Position=position)
        self.addInputEvent("REQ", "Normal Execution Request")
        self.addOutputEvent("CNF", "Execution Confirmation")
        self.addInputVar("IN1", "ANY_NUM", "First function input", 0)
        self.addInputVar("IN2", "ANY_NUM", "Second function input", 0)
        self.addOutputVar("OUT", "ANY_NUM", "Function output", 0)

    def eventTrigger(self, event):
        if event != "REQ":
            return
        IN2 = self.getVarValue("IN2")
        if IN2 == 0:                       # 除零保护：OUT 置 0，不发 CNF
            print(f"[{self.Name}] REQ ignored, division by zero (IN2=0)")
            self.setVarValue("OUT", 0)
            return
        OUT = self.getVarValue("IN1") / IN2   # OUT := IN1 / IN2
        self.setVarValue("OUT", OUT)
        print(f"[{self.Name}] REQ -> OUT={OUT}")
        self.sendOutputEvent("CNF")
