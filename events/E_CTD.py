from BasicFB import *

class E_CTD(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_CTD", "Count Down Counter", Position=position)
        self.addInputEvent("CD", "Count Down")
        self.addInputEvent("LD", "Load counter value")
        self.addOutputEvent("CDO", "Count Down Output Event")
        self.addOutputEvent("LDO", "Load Output Event")
        self.addInputVar("PV", "UINT", "Preset Value")
        self.addOutputVar("Q", "BOOL", "CV <= 0")
        self.addOutputVar("CV", "UINT", "Counter Value")
        # 初值 CV=0 => Q=1：首次 EI 时 G=1，触发 LD 装入 PV，从而自举启动循环递减。
        self.setVarValue("CV", 0)
        self.setVarValue("Q", 1)

    def eventTrigger(self, event):
        match self.ecc_status:
            case "Ready":
                if event == "LD":
                    self.ecc_status = "Counting"
                    self.actionLoad()
                elif event == "CD":
                    self.ecc_status = "Counting"
                    self.actionCountDown()
            case "Counting":
                if event == "CD":
                    self.actionCountDown()
                elif event == "LD":
                    self.actionLoad()

    def actionLoad(self):
        PV = self.getVarValue("PV")
        self.setVarValue("CV", PV)
        self.setVarValue("Q", 0)
        print(f"[{self.Name}] LD -> CV={PV} (loaded)")
        self.sendOutputEvent("LDO")

    def actionCountDown(self):
        CV = self.getVarValue("CV")
        if CV > 0:
            CV -= 1
            self.setVarValue("CV", CV)
            print(f"[{self.Name}] CD -> CV={CV}")
            if CV == 0:
                self.setVarValue("Q", 1)        # 减到 0，切换信号置位
                self.sendOutputEvent("CDO")
        else:
            print(f"[{self.Name}] CD ignored, CV already 0")
