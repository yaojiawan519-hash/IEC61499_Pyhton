from BasicFB import *

class E_CTU(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_CTU", "Count Up Counter", Position=position)
        self.addInputEvent("CU", "Count Up")
        self.addInputEvent("R", "Reset")
        self.addOutputEvent("CUO", "Count Up Output Event")
        self.addOutputEvent("RO", "Reset Output Event")
        self.addInputVar("PV", "UINT", "Preset Value")
        self.addOutputVar("Q", "BOOL", "CV >= PV")
        self.addOutputVar("CV", "UINT", "Counter Value")
        self.setVarValue("CV", 0)
        self.setVarValue("Q", 0)

    def eventTrigger(self, event):
        match self.ecc_status:
            case "Ready":
                if event == "CU":
                    self.ecc_status = "Counting"
                    self.actionCountUp()
                elif event == "R":
                    self.actionReset()
            case "Counting":
                if event == "CU":
                    self.actionCountUp()
                elif event == "R":
                    self.actionReset()

    def actionCountUp(self):
        CV = self.getVarValue("CV")
        PV = self.getVarValue("PV")
        if CV < PV:
            CV += 1
            self.setVarValue("CV", CV)
            print(f"[{self.Name}] CU -> CV={CV}")
            if CV >= PV:
                self.setVarValue("Q", 1)        # 到达 PV，切换信号置位
                self.sendOutputEvent("CUO")
        else:
            print(f"[{self.Name}] CU ignored, CV already at PV={PV}")

    def actionReset(self):
        self.setVarValue("CV", 0)
        self.setVarValue("Q", 0)
        print(f"[{self.Name}] R -> CV=0 (reset)")
        self.sendOutputEvent("RO")
