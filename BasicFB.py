class Variable:
  def __init__(self, name, datatype="BOOL", value=""):
          self.name = name
          self.datatype = datatype
          self.value = value
class Event:
  def __init__(self, name, comment=""):
          self.name = name
          self.comment = comment
class BasicFB:
  def __init__(self, Name, FBType="", Comment="",
               InputEvents=None, OutputEvents=None,
               InputVars=None, OutputVars=None, Position=None):
          self.Name = Name
          self.FBType = FBType
          self.Comment = Comment
          self.InputEvents = InputEvents if InputEvents is not None else []
          self.OutputEvents = OutputEvents if OutputEvents is not None else []
          self.InputVars = InputVars if InputVars is not None else []
          self.OutputVars = OutputVars if OutputVars is not None else []
          self.Position = Position
          self.ecc_status = "Ready"
          # 回指针：所属的功能块网络，由 FunctionBlockNetwork 在构造时回填。
          # 只有挂到网络上的实例才非 None；sendOutputEvent 依赖它把输出事件
          # 经网络转发到下游功能块。
          self.network = None
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
  def setVarValue(self, var_name, value):
         # 同时覆盖输入与输出变量：E_CTU/E_CTD 的 CV、Q 都是输出变量，
         # 内部动作要用 setVarValue 写它们；PV 是输入变量，外部要写它。
         for var in self.InputVars:
             if var.name == var_name:
                 var.value = value
                 return
         for var in self.OutputVars:
             if var.name == var_name:
                 var.value = value
                 return
  def getVarValue(self, var_name):
         # 同时能在输入/输出变量里查值：E_SWITCH 要读输入 G，E_CTU 要读输入 PV，
         # 也要读输出 CV。找不到返回 None（与 test_MOTOR 期望一致）。
         for var in self.InputVars:
             if var.name == var_name:
                 return var.value
         for var in self.OutputVars:
             if var.name == var_name:
                 return var.value
         return None
  def sendOutputEvent(self, event):
         # 功能块内部产生输出事件时调用：交给网络转发到下游输入事件。
         # 没挂网络（单元测试里）则忽略，保证可单独实例化测试。
         if self.network is not None:
             self.network.NotifyEvent(self.Name, event)
