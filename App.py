from FunctionBlockNetwork  import *
from utilities import Position
from events.E_CYCLE import E_CYCLE
from events.E_SWITCH import E_SWITCH
from events.E_CTU import E_CTU
from events.E_CTD import E_CTD
class App(FunctionBlockNetwork):
    def __init__(self):
        self.FunctionBlocks = []
        # ===== 共用周期发生器：300ms =====
        e_cycle=E_CYCLE("E_CYCLE_1",Position(0,0))
        e_cycle.setVarValue("DT", "#T300ms")
        self.FunctionBlocks.append(e_cycle)
        # ===== 循环递增计数器：循环值 64 =====
        e_switch_up=E_SWITCH("E_SWITCH_UP",Position(0,100))
        e_ctu=E_CTU("E_CTU_1",Position(0,200))
        e_ctu.setVarValue("PV", 64)
        self.FunctionBlocks.append(e_switch_up)
        self.FunctionBlocks.append(e_ctu)
        # ===== 循环递减计数器：循环值 32 =====
        e_switch_dn=E_SWITCH("E_SWITCH_DN",Position(400,100))
        e_ctd=E_CTD("E_CTD_1",Position(400,200))
        e_ctd.setVarValue("PV", 32)
        self.FunctionBlocks.append(e_switch_dn)
        self.FunctionBlocks.append(e_ctd)
        # 连接由本应用直接分类填入两个队列：事件连接 / 数据连接。
        # 每条 = (源FB名, 源引脚名, 目的FB名, 目的引脚名)
        self.EventConnections = []
        self.DataConnections = []
        # ----- Up Counter 连接 -----
        # E_CYCLE.EO -> E_SWITCH.EI
        self.EventConnections.append((e_cycle.Name, e_cycle.OutputEvents[0].name,
                                      e_switch_up.Name, e_switch_up.InputEvents[0].name))
        # E_SWITCH.EO0 (G=0) -> E_CTU.CU   正常递增
        self.EventConnections.append((e_switch_up.Name, e_switch_up.OutputEvents[0].name,
                                      e_ctu.Name, e_ctu.InputEvents[0].name))
        # E_SWITCH.EO1 (G=1) -> E_CTU.R    到 64 复位
        self.EventConnections.append((e_switch_up.Name, e_switch_up.OutputEvents[1].name,
                                      e_ctu.Name, e_ctu.InputEvents[1].name))
        # E_CTU.Q -> E_SWITCH.G            到限位切换
        self.DataConnections.append((e_ctu.Name, e_ctu.OutputVars[0].name,
                                     e_switch_up.Name, e_switch_up.InputVars[0].name))

        # ----- Down Counter 连接 -----
        # E_CYCLE.EO -> E_SWITCH.EI
        self.EventConnections.append((e_cycle.Name, e_cycle.OutputEvents[0].name,
                                      e_switch_dn.Name, e_switch_dn.InputEvents[0].name))
        # E_SWITCH.EO0 (G=0) -> E_CTD.CD   正常递减
        self.EventConnections.append((e_switch_dn.Name, e_switch_dn.OutputEvents[0].name,
                                      e_ctd.Name, e_ctd.InputEvents[0].name))
        # E_SWITCH.EO1 (G=1) -> E_CTD.LD   到 0 重装 PV
        self.EventConnections.append((e_switch_dn.Name, e_switch_dn.OutputEvents[1].name,
                                      e_ctd.Name, e_ctd.InputEvents[1].name))
        # E_CTD.Q -> E_SWITCH.G            到限位切换
        self.DataConnections.append((e_ctd.Name, e_ctd.OutputVars[0].name,
                                     e_switch_dn.Name, e_switch_dn.InputVars[0].name))
        super().__init__("myApp", "", self.FunctionBlocks,
                         self.EventConnections, self.DataConnections)
