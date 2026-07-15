from BasicFB import *

class E_CTUD(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_CTUD", "Event-Driven Up-Down Counter", Position=position)
        self.addInputEvent("CU", "Count Up")
        self.addInputEvent("CD", "Count Down")
        self.addInputEvent("R", "Reset")
        self.addInputEvent("LD", "Load")
        self.addOutputEvent("CO", "Count Output Event")
        self.addOutputEvent("RO", "Reset Output Event")
        self.addOutputEvent("LDO", "Load Output Event")
        self.addInputVar("PV", "UINT", "Preset Value")
        self.addOutputVar("QU", "BOOL", "CV >= PV")
        self.addOutputVar("QD", "BOOL", "CV <= 0")
        self.addOutputVar("CV", "UINT", "Counter Value")
        self.setVarValue("CV", 0)
        self.setVarValue("QU", 0)
        self.setVarValue("QD", 1)           # CV=0 => QD=1
        # ECC 初始状态 START；CU/CD/R/LD 处理后均无条件(Condition="1")回到 START。
        self.ecc_status = "START"

    def eventTrigger(self, event):
        if self.ecc_status != "START":
            return
        CV = self.getVarValue("CV")
        if event == "CU":
            if CV < 65535:                  # CU[(CV<65535)]
                self.ecc_status = "CU"
                self.actionCountUp()
                self.actionUpdateQUQD()
                self.sendOutputEvent("CO")
                self.ecc_status = "START"
            else:
                print(f"[{self.Name}] CU ignored, CV already at max 65535")
        elif event == "CD":
            if CV > 0:                      # CD[(CV>0)]
                self.ecc_status = "CD"
                self.actionCountDown()
                self.actionUpdateQUQD()
                self.sendOutputEvent("CO")
                self.ecc_status = "START"
            else:
                print(f"[{self.Name}] CD ignored, CV already 0")
        elif event == "R":
            self.ecc_status = "R"
            self.actionReset()
            self.actionUpdateQUQD()
            self.sendOutputEvent("RO")
            self.ecc_status = "START"
        elif event == "LD":
            self.ecc_status = "LD"
            self.actionLoad()
            self.actionUpdateQUQD()
            self.sendOutputEvent("LDO")
            self.ecc_status = "START"

    def actionCountUp(self):
        CV = self.getVarValue("CV") + 1
        self.setVarValue("CV", CV)
        print(f"[{self.Name}] CU -> CV={CV}")

    def actionCountDown(self):
        CV = self.getVarValue("CV") - 1
        self.setVarValue("CV", CV)
        print(f"[{self.Name}] CD -> CV={CV}")

    def actionReset(self):
        self.setVarValue("CV", 0)
        print(f"[{self.Name}] R -> CV=0 (reset)")

    def actionLoad(self):
        PV = self.getVarValue("PV")
        self.setVarValue("CV", PV)
        print(f"[{self.Name}] LD -> CV={PV} (loaded)")

    def actionUpdateQUQD(self):
        CV = self.getVarValue("CV")
        PV = self.getVarValue("PV")
        self.setVarValue("QU", 1 if CV >= PV else 0)
        self.setVarValue("QD", 1 if CV == 0 else 0)
