import os
import xml.etree.ElementTree as ET

# 导出文件（svg/fbt）默认输出目录
OUTPUT_DIR = "outputs"


def _default_output_path(name, ext, path):
    """返回导出路径：指定了 path 就用 path；否则放到 output 目录下（自动创建）。"""
    if path:
        return path
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, f"{name}.{ext}")



class Variable:
  def __init__(self, name, datatype="BOOL", value=""):
          self.name = name
          self.datatype = datatype
          self.value = value
class Event:
  def __init__(self, name, comment=""):
          self.name = name
          self.comment = comment
          self.count = 0   # 事件触发计数（输入/输出共用），监督用
  def increment(self):
          self.count += 1


def _increment_event(event_list, name):
  """在事件列表中按名查找并递增计数，返回找到的 Event（找不到返回 None）。"""
  for e in event_list:
      if e.name == name:
          e.increment()
          return e
  return None

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
          # 绘制坐标：由 FunctionBlockNetwork.draw 在布局后回填。
          # x/y 为左上角绝对坐标，width/height 为块尺寸。
          self.x = None
          self.y = None
          self.width = None
          self.height = None
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
  # ---- 事件监督：输入/输出事件各带一个计数器 ----
  # 输入事件计数在 receiveEvent（事件入口）里递增；输出事件计数在
  # sendOutputEvent 里递增。eventTrigger 由各子类覆盖且不调 super，
  # 故输入计数放在不被覆盖的 receiveEvent 包装里，再分发到 eventTrigger。
  def receiveEvent(self, event):
         """事件入口：先记输入事件计数，再驱动 ECC（eventTrigger）。"""
         _increment_event(self.InputEvents, event)
         self.eventTrigger(event)
  def eventTrigger(self, event):
         """ECC 入口基类默认实现（空）。子类按事件名做状态迁移/动作。"""
         pass
  def getEventCount(self, name):
         """取某个事件的触发计数（先查输入事件，再查输出事件）。找不到返回 None。"""
         for e in self.InputEvents:
             if e.name == name:
                 return e.count
         for e in self.OutputEvents:
             if e.name == name:
                 return e.count
         return None
  def sendOutputEvent(self, event):
         # 功能块内部产生输出事件时调用：先记输出事件计数，再交给网络转发。
         # 没挂网络（单元测试里）则只计数不转发，保证可单独实例化测试。
         _increment_event(self.OutputEvents, event)
         if self.network is not None:
             self.network.NotifyEvent(self.Name, event)

  # ------------------------------------------------------------------
  # 绘制：把单个功能块画成 SVG 并存盘，文件名与功能块名相同（{Name}.svg）。
  # 无需 pyelk（单块无需布局），端口重排到标题分隔线下方，与网络 draw 风格一致。
  # 绘制后回填 self.x / self.y / self.width / self.height。
  # ------------------------------------------------------------------
  def draw(self, path=None):
         TITLE_H = 30     # 标题区高度（分隔线 y=26 之下留 4px）
         PORT_ROW = 18    # 每行端口高度
         NODE_W = 130     # 功能块宽度
         PAD = 20         # 画布四周留白

         # WEST = 输入事件 + 输入变量；EAST = 输出事件 + 输出变量
         west = [(e.name, "event") for e in self.InputEvents] + \
                [(v.name, "data")  for v in self.InputVars]
         east = [(e.name, "event") for e in self.OutputEvents] + \
                [(v.name, "data")  for v in self.OutputVars]
         rows = max(len(west), len(east), 1)
         nw = NODE_W
         nh = TITLE_H + rows * PORT_ROW + 8

         # 单块放在画布左上角留白处；回填坐标
         nx, ny = PAD, PAD
         self.x, self.y = nx, ny
         self.width, self.height = nw, nh

         # 端口在 [TITLE_H, nh] 区间内按边均匀分布
         def place(items, side):
             n = len(items)
             if n == 0:
                 return []
             spacing = (nh - TITLE_H) / (n + 1)
             return [(name, kind, 0 if side == "WEST" else nw,
                      TITLE_H + spacing * (i + 1)) for i, (name, kind) in enumerate(items)]
         west_ports = place(west, "WEST")
         east_ports = place(east, "EAST")

         W = nw + 2 * PAD
         H = nh + 2 * PAD
         out_path = _default_output_path(self.Name, "svg", path)

         svg = []
         svg.append(
             f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
         )
         svg.append(f'<title>{self.Name}</title>')
         svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fafafa"/>')

         # 功能块主体
         svg.append(
             f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" '
             f'rx="6" fill="#ffffff" stroke="#2d3748" stroke-width="1.5"/>')
         svg.append(
             f'<text x="{nx + nw/2}" y="{ny + 16}" text-anchor="middle" '
             f'dominant-baseline="middle" font-family="sans-serif" '
             f'font-size="12" font-weight="bold" fill="#1a202c">{self.Name}</text>')
         svg.append(
             f'<line x1="{nx}" y1="{ny + 26}" x2="{nx + nw}" y2="{ny + 26}" '
             f'stroke="#2d3748" stroke-width="1"/>')

         def draw_port(name, kind, px, py, side):
             # 端口图形：事件=圆点，数据=方块
             if kind == "data":
                 svg.append(
                     f'<rect x="{px-4}" y="{py-4}" width="8" height="8" '
                     f'fill="#2b6cb0" stroke="#1a365d"/>')
             else:
                 svg.append(
                     f'<circle cx="{px}" cy="{py}" r="4" '
                     f'fill="#d69e2e" stroke="#744210"/>')
             lx = px + 8 if side == "WEST" else px - 8
             anchor = "start" if side == "WEST" else "end"
             svg.append(
                 f'<text x="{lx}" y="{py}" text-anchor="{anchor}" '
                 f'dominant-baseline="middle" font-family="sans-serif" '
                 f'font-size="10" fill="#4a5568">{name}</text>')

         for name, kind, px, py in west_ports:
             draw_port(name, kind, nx + px, ny + py, "WEST")
         for name, kind, px, py in east_ports:
             draw_port(name, kind, nx + px, ny + py, "EAST")

         svg.append("</svg>")
         with open(out_path, "w", encoding="utf-8") as f:
             f.write("\n".join(svg))
         return out_path

  # ------------------------------------------------------------------
  # 导出 IEC 61499 FBType (.fbt) 文档。
  # 类中保存的是接口（事件 + 变量），完整导出；ECC 在本类里以代码形式
  # 实现（eventTrigger 的 match/case），未作为结构化数据保存，因此
  # BasicFB/ECC 段只导出一个 START 状态的骨架，保证 fbt 仍是合法的
  # BasicFB 类型（可在 4diac 等工具中打开后再补 ECC）。
  # ------------------------------------------------------------------
  def ExportXML(self, path=None):
         fbtype = ET.Element("FBType", {"Name": self.Name,
                                        "Comment": self.Comment or ""})
         ET.SubElement(fbtype, "Identification", {"Standard": "61499-2"})
         ET.SubElement(fbtype, "VersionInfo",
                       {"Organization": "", "Author": "",
                        "Version": "1.0", "Date": "", "Remarks": ""})

         iface = ET.SubElement(fbtype, "InterfaceList")
         if self.InputEvents:
             ei = ET.SubElement(iface, "EventInputs")
             for e in self.InputEvents:
                 ET.SubElement(ei, "Event",
                               {"Name": e.name, "Type": "Event",
                                "Comment": e.comment or ""})
         if self.OutputEvents:
             eo = ET.SubElement(iface, "EventOutputs")
             for e in self.OutputEvents:
                 ET.SubElement(eo, "Event",
                               {"Name": e.name, "Type": "Event",
                                "Comment": e.comment or ""})
         if self.InputVars:
             iv = ET.SubElement(iface, "InputVars")
             for v in self.InputVars:
                 ET.SubElement(iv, "VarDeclaration",
                               {"Name": v.name, "Type": v.datatype})
         if self.OutputVars:
             ov = ET.SubElement(iface, "OutputVars")
             for v in self.OutputVars:
                 ET.SubElement(ov, "VarDeclaration",
                               {"Name": v.name, "Type": v.datatype})

         # 最小 ECC 骨架：仅 START 状态（实际 ECC 由代码实现，见 eventTrigger）
         basic = ET.SubElement(fbtype, "BasicFB")
         ecc = ET.SubElement(basic, "ECC")
         ET.SubElement(ecc, "ECState",
                       {"Name": "START", "x": "0", "y": "0", "Comment": ""})

         ET.indent(fbtype, space="  ")
         out_path = _default_output_path(self.Name, "fbt", path)
         with open(out_path, "wb") as f:
             f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
             f.write(b'<!DOCTYPE FBType>\n')
             f.write(ET.tostring(fbtype, encoding="UTF-8"))
         return out_path
