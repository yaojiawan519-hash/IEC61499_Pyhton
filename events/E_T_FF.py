from BasicFB import *

class E_T_FF(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_T_FF", "Toggle flip flop", Position=position)
        self.addInputEvent("CLK", "Clock for triggering a output toggle")
        self.addOutputEvent("EO", "Output Q has changed")
        self.addOutputVar("Q", "BOOL", "value of flip flop", 0)
        # ECC: START ->SET(Condition=CLK) ->START(Condition=1)。
        # SET 为瞬态：每个 CLK 都执行 TOGGLE(Q:=NOT Q) 并发 EO，随后即回 START。
        self.setVarValue("Q", 0)
        self.ecc_status = "START"

    def eventTrigger(self, event):
        if event != "CLK":
            return
        self.ecc_status = "SET"
        self.actionToggle()
        self.ecc_status = "START"      # Condition="1" 立即回到 START

    def actionToggle(self):
        Q = 0 if self.getVarValue("Q") else 1   # Q := NOT Q
        self.setVarValue("Q", Q)
        print(f"[{self.Name}] CLK -> Q={Q} (toggled)")
        self.sendOutputEvent("EO")
