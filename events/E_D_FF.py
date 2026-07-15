from BasicFB import *

class E_D_FF(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_D_FF", "Data latch (d) flip flop", Position=position)
        self.addInputEvent("CLK", "Clock")
        self.addOutputEvent("EO", "Triggered if clock results in a change of Q")
        self.addInputVar("D", "BOOL", "Value to latch", 0)
        self.addOutputVar("Q", "BOOL", "Latched value", 0)
        self.setVarValue("Q", 0) 
        self.ecc_status = "START"

    def eventTrigger(self, event):
        if event != "CLK":
            return
        D = self.getVarValue("D")
        match self.ecc_status:
            case "START":
                if D == 1:                  # CLK[D]
                    self.ecc_status = "SET"
                    self.actionLatch()
            case "SET":
                if D == 0:                  # CLK[NOT D]
                    self.ecc_status = "RESET"
                    self.actionLatch()
                # D==1：Q 已为 1，无转移、无输出（CLK 丢弃）
            case "RESET":
                if D == 1:                  # CLK[D]
                    self.ecc_status = "SET"
                    self.actionLatch()
                # D==0：Q 已为 0，无转移、无输出（CLK 丢弃）

    def actionLatch(self):
        D = self.getVarValue("D")
        self.setVarValue("Q", D)            # Q := D
        print(f"[{self.Name}] CLK -> Q={D} (latched)")
        self.sendOutputEvent("EO")
