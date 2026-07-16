from BasicFB import *

class E_F_TRIG(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_F_TRIG", "Boolean falling edge detection", Position=position)
        self.addInputEvent("EI", "check for falling edge")
        self.addOutputEvent("EO", "confirmation that a falling edge was detected")
        self.addInputVar("QI", "BOOL", "value to check for a falling edge", 0)
        # fbt 中本块为复合网络：EI->E_D_FF.CLK, QI->E_D_FF.D,
        # E_D_FF.Q->E_SWITCH.G, E_D_FF.EO->E_SWITCH.EI, E_SWITCH.EO0->EO。
        # E_D_FF 仅在 Q 翻转时发 EO；翻转后 Q=0 即下降沿，E_SWITCH(G=0)走 EO0 => EO。
        # 这里将其展平为等价 BasicFB：内部 latch 对应 E_D_FF 的 Q，仅在 QI 实际
        # 翻转且新值为 0（下降沿）时发 EO。
        self._latch = 0                     # 等价 E_D_FF 的 Q 初值

    def eventTrigger(self, event):
        if event != "EI":
            return
        qi = self.getVarValue("QI")
        if qi == self._latch:
            return                          # QI 未变 => E_D_FF 不发 EO，无输出
        self._latch = qi                    # E_D_FF 锁存 Q:=D
        if qi == 0:                         # 翻转为 0：下降沿
            print(f"[{self.Name}] EI -> falling edge detected (QI=0)")
            self.sendOutputEvent("EO")
        # 翻转为 1（上升沿）：E_SWITCH 走 EO1，未连到 EO，故本块无输出
