from BasicFB import *

class E_SR(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_SR", "Event-driven bistable", Position=position)
        self.addInputEvent("S", "Set output Q")
        self.addInputEvent("R", "Reset output Q")
        self.addOutputEvent("EO", "Output Q has changed")
        self.addOutputVar("Q", "BOOL", "value of flip flop", 0)
        # ECC 与 E_RS 相同（仅输入事件排列顺序不同）：
        # START->SET(S), SET->RESET(R), RESET->SET(S)；EO 只在 Q 真正改变时发出。
        self.setVarValue("Q", 0)
        self.ecc_status = "START"

    def eventTrigger(self, event):
        match self.ecc_status:
            case "START":
                if event == "S":
                    self.ecc_status = "SET"
                    self.actionSet()
                # R 在 START 态无转移（Q 已为 0，忽略）
            case "SET":
                if event == "R":
                    self.ecc_status = "RESET"
                    self.actionReset()
                # S 在 SET 态无转移（Q 已为 1，忽略）
            case "RESET":
                if event == "S":
                    self.ecc_status = "SET"
                    self.actionSet()
                # R 在 RESET 态无转移（Q 已为 0，忽略）

    def actionSet(self):
        self.setVarValue("Q", 1)            # Q := TRUE
        print(f"[{self.Name}] S -> Q=1 (set)")
        self.sendOutputEvent("EO")

    def actionReset(self):
        self.setVarValue("Q", 0)            # Q := FALSE
        print(f"[{self.Name}] R -> Q=0 (reset)")
        self.sendOutputEvent("EO")
