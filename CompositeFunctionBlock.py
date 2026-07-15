from BasicFB import *

class CompositeFunctionBlock:

    def __init__(self, Name, Comment, FunctionBlocks,
                 InputEvents=None, OutputEvents=None,
                 InputVars=None, OutputVars=None, Position=None,
                 EventConnections=None, DataConnections=None):
        self.Name = Name
        self.Comment = Comment
        self.InputEvents = InputEvents if InputEvents is not None else []
        self.OutputEvents = OutputEvents if OutputEvents is not None else []
        self.InputVars = InputVars if InputVars is not None else []
        self.OutputVars = OutputVars if OutputVars is not None else []
        self.Position = Position
        self.FunctionBlocks = FunctionBlocks if FunctionBlocks is not None else []
        self.EventConnections = EventConnections if EventConnections is not None else []
        self.DataConnections = DataConnections if DataConnections is not None else []
        # 回指针：复合块自身也可挂到上层网络，sendOutputEvent 依赖它上行。
        self.network = None
        # 回填子块的网络指针：子块 sendOutputEvent 经本块 NotifyEvent 转发。
        for fb in self.FunctionBlocks:
            fb.network = self
        self._fbByName = {fb.Name: fb for fb in self.FunctionBlocks}
        # 将复合块自身加入字典，便于连接把事件/数据路由到本块接口。
        self._fbByName[self.Name] = self

    def addInputEvent(self, event, comment=""):
        self.InputEvents.append(Event(event, comment))

    def addOutputEvent(self, event, comment=""):
        self.OutputEvents.append(Event(event, comment))

    def addInputVar(self, var, datatype="BOOL", comment="", value=""):
        # 兼容两种调用：传入已构造的 Variable，或传 (name, datatype, comment[, value])
        if isinstance(var, Variable):
            self.InputVars.append(var)
        else:
            self.InputVars.append(Variable(var, datatype, value))

    def addOutputVar(self, var, datatype="BOOL", comment="", value=""):
        if isinstance(var, Variable):
            self.OutputVars.append(var)
        else:
            self.OutputVars.append(Variable(var, datatype, value))

    def __repr__(self):
        FB_list = [fb.Name for fb in self.FunctionBlocks]
        ev = [f"{s}.{p}->{d}.{q}" for s, p, d, q in self.EventConnections]
        dt = [f"{s}.{p}->{d}.{q}" for s, p, d, q in self.DataConnections]
        return ('Composite FB :name=' + self.Name
                + ' Function Blocks:' + str(FB_list)
                + ' EventConnections:' + str(ev)
                + ' DataConnections:' + str(dt))

    def setVarValue(self, var_name, value):
        # 读写本复合块接口上的输入/输出变量（与 BasicFB 一致）。
        for var in self.InputVars:
            if var.name == var_name:
                var.value = value
                return
        for var in self.OutputVars:
            if var.name == var_name:
                var.value = value
                return

    def getVarValue(self, var_name):
        for var in self.InputVars:
            if var.name == var_name:
                return var.value
        for var in self.OutputVars:
            if var.name == var_name:
                return var.value
        return None

    def ReadVarValue(self, FB_name, var_name):
        fb = self._fbByName.get(FB_name)
        return fb.getVarValue(var_name) if fb else None

    def WriteVarValue(self, FB_name, var_name, value):
        fb = self._fbByName.get(FB_name)
        if fb:
            fb.setVarValue(var_name, value)

    def propagateData(self, FB_name):
        """只更新即将接收事件的 FB_name 的数据输入：把所有以它为目的的数据连接
        的源输出变量值搬进来。在驱动该 FB 之前调用，保证它读到最新输入
        （如 E_SWITCH 收到 EI 前，先从 E_CTD.Q 刷新自己的 G）。"""  
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

    def eventTrigger(self, FB_name, event=None):
    
        if event is None:
            event = FB_name
            FB_name = self.Name
        if FB_name == self.Name:
            for sfb, spin, dfb, dpin in self.EventConnections:
                if sfb == self.Name and spin == event:
                    self.eventTrigger(dfb, dpin)
        else:
            fb = self._fbByName.get(FB_name)
            if fb is None:
                return
            self.propagateData(FB_name)
            fb.eventTrigger(event)

    def NotifyEvent(self, FB_name, event):
        """某功能块产生了输出事件：按事件连接转发到下游输入事件。"""
        if FB_name == self.Name:
            if self.network is not None:
                self.network.NotifyEvent(self.Name, event)
            return
        for sfb, spin, dfb, dpin in self.EventConnections:
            if sfb != FB_name or spin != event:
                continue
            if dfb == self.Name:
                # 连到本块输出事件槽：先刷新本块输出数据（此时同源前置连接已处理完），再上行。
                self.propagateData(self.Name)
                self.NotifyEvent(self.Name, dpin)
            else:
                self.eventTrigger(dfb, dpin)

