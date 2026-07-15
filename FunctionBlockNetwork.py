
class FunctionBlockNetwork:
     def __init__(self, Name, Comment, FunctionBlocks,
                  EventConnections=None, DataConnections=None,
                  InputEvents=None, OutputEvents=None,
                  InputVars=None, OutputVars=None, Position=None):
         self.Name = Name
         self.Comment = Comment
         self.InputEvents = InputEvents if InputEvents is not None else []
         self.OutputEvents = OutputEvents if OutputEvents is not None else []
         self.InputVars = InputVars if InputVars is not None else []
         self.OutputVars = OutputVars if OutputVars is not None else []
         self.Position = Position
         self.FunctionBlocks = FunctionBlocks
         self.EventConnections = EventConnections if EventConnections is not None else []
         self.DataConnections = DataConnections if DataConnections is not None else []
         # 回填网络指针：功能块内部 sendOutputEvent 依赖它把输出事件转发回网络。
         for fb in self.FunctionBlocks:
             fb.network = self
         self._fbByName = {fb.Name: fb for fb in self.FunctionBlocks}

     def __repr__(self):
        FB_list = [fb.Name for fb in self.FunctionBlocks]
        ev = [f"{s}.{p}->{d}.{q}" for s, p, d, q in self.EventConnections]
        dt = [f"{s}.{p}->{d}.{q}" for s, p, d, q in self.DataConnections]
        return ('FB Network :name=' + self.Name
                + ' Function Blocks:' + str(FB_list)
                + ' EventConnections:' + str(ev)
                + ' DataConnections:' + str(dt))

     def ReadVarValue(self, FB_name, var_name):
         fb = self._fbByName.get(FB_name)
         return fb.getVarValue(var_name) if fb else None

     def WriteVarValue(self, FB_name, var_name, value):
         fb = self._fbByName.get(FB_name)
         if fb:
             fb.setVarValue(var_name, value)

     def propagateData(self, FB_name):
         """只更新即将接收事件的 FB_name 的数据输入：把所有以它为目的的数据连接
         的源输出变量值搬进来。在驱动该 FB 的 ECC 之前调用，保证它读到最新输入
         （如 E_SWITCH 收到 EI 前，先从 E_CTU.Q 刷新自己的 G）。"""
         for sfb, spin, dfb, dpin in self.DataConnections:
             if dfb != FB_name:
                 continue
             src = self._fbByName.get(sfb)
             dst = self._fbByName.get(dfb)
             if src is None or dst is None:
                 continue
             value = src.getVarValue(spin)
             if value is not None:
                 dst.setVarValue(dpin, value)

     def TriggerEvent(self, FB_name, event):
         fb = self._fbByName.get(FB_name)
         if fb is None:
             return
         self.propagateData(FB_name)     # 只刷新本 FB 的输入数据，再驱动 ECC
         fb.eventTrigger(event)

     def NotifyEvent(self, FB_name, event):
         """某功能块产生了输出事件：按事件连接转发到下游输入事件。"""
         for sfb, spin, dfb, dpin in self.EventConnections:
             if sfb == FB_name and spin == event:
                 self.TriggerEvent(dfb, dpin)
