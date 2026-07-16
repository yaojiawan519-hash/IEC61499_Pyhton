
from utilities import Connection
from BasicFB import _default_output_path


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
         # 规整为 Connection 对象（兼容传入的 4 元组），便于 draw 记录坐标。
         self.EventConnections = [Connection.normalize(c, "event")
                                  for c in (EventConnections or [])]
         self.DataConnections = [Connection.normalize(c, "data")
                                 for c in (DataConnections or [])]
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
         fb.receiveEvent(event)         # 经 FB 入口计数输入事件，再触发 ECC

     def NotifyEvent(self, FB_name, event):
         """某功能块产生了输出事件：按事件连接转发到下游输入事件。"""
         for sfb, spin, dfb, dpin in self.EventConnections:
             if sfb == FB_name and spin == event:
                 self.TriggerEvent(dfb, dpin)

     # ------------------------------------------------------------------
     # 绘制：把本网络布局成一张 SVG，文件名与网络名相同（{Name}.svg）。
     # 坐标会回填到每个功能块（x/y/width/height）和每条 Connection（points）。
     # ------------------------------------------------------------------
     def draw(self, path=None):
         from pyelk import ELK   # 延迟导入：运行时不需要 pyelk

         TITLE_H = 30     # 功能块标题区高度（分隔线 y=26 之下留 4px）
         PORT_ROW = 18    # 每行端口的高度
         NODE_W = 130     # 功能块宽度
         PAD = 20         # 画布四周留白
         HEADER = 28      # 顶部网络名留白
         BACK_GAP = 15    # 回环边出/入端口的水平偏移

         fbs = self.FunctionBlocks

         # ---- 1. 为每个功能块计算尺寸，构建 ELK 节点 + 端口 ----
         # port_meta: port_id -> (fb_name, pin_name, kind, side)
         port_meta = {}
         children = []
         for fb in fbs:
             west = [ (e.name, "event") for e in fb.InputEvents ] + \
                    [ (v.name, "data")  for v in fb.InputVars  ]
             east = [ (e.name, "event") for e in fb.OutputEvents ] + \
                    [ (v.name, "data")  for v in fb.OutputVars  ]
             rows = max(len(west), len(east), 1)
             nh = TITLE_H + rows * PORT_ROW + 8
             ports = []
             for pin, kind in west:
                pid = f"{fb.Name}::{pin}"
                ports.append({"id": pid, "layoutOptions": {"port.side": "WEST"}})
                port_meta[pid] = (fb.Name, pin, kind, "WEST")
             for pin, kind in east:
                pid = f"{fb.Name}::{pin}"
                ports.append({"id": pid, "layoutOptions": {"port.side": "EAST"}})
                port_meta[pid] = (fb.Name, pin, kind, "EAST")
             children.append({"id": fb.Name, "width": NODE_W, "height": nh, "ports": ports})

         # ---- 2. 构建边（事件连接 + 数据连接）----
         all_conns = ([("event", c) for c in self.EventConnections] +
                      [("data", c)   for c in self.DataConnections])
         elk_edges = []
         for i, (kind, c) in enumerate(all_conns):
             elk_edges.append({
                 "id": f"e{i}",
                 "sources": [f"{c.source}::{c.source_pin}"],
                 "targets": [f"{c.dest}::{c.dest_pin}"],
             })

         elk_graph = {
             "id": "root",
             "layoutOptions": {
                 "elk.algorithm": "layered",
                 "elk.direction": "RIGHT",
                 "elk.edgeRouting": "ORTHOGONAL",
                 "elk.spacing.nodeNode": "160",
                 "elk.layered.spacing.nodeNodeBetweenLayers": "180",
             },
             "children": children,
             "edges": elk_edges,
         }
         layouted = ELK().layout(elk_graph)

         # ---- 3. 回填功能块坐标 + 把端口重排到标题分隔线下方 ----
         # 注意：pyelk 的 edge.sections 端点会落到节点边框中点而非端口，
         # 因此不用它的 section，端口位置也由我们自己重排。
         node_by_id = {nd["id"]: nd for nd in layouted["children"]}
         for fb in fbs:
             nd = node_by_id[fb.Name]
             fb.x, fb.y = nd["x"], nd["y"]
             fb.width, fb.height = nd["width"], nd["height"]
             nw, nh = fb.width, fb.height
             for side in ("WEST", "EAST"):
                 side_ports = [p for p in nd["ports"]
                               if p["layoutOptions"]["port.side"] == side]
                 n = len(side_ports)
                 if n == 0:
                     continue
                 spacing = (nh - TITLE_H) / (n + 1)
                 for i, p in enumerate(side_ports):
                     p["x"] = 0 if side == "WEST" else nw
                     p["y"] = TITLE_H + spacing * (i + 1)

         # ---- 4. 端口索引：(fb_name, pin) -> 绝对坐标 / kind / side ----
         port_index = {}
         for fb in fbs:
             nd = node_by_id[fb.Name]
             for p in nd["ports"]:
                 _, pin, kind, side = port_meta[p["id"]]
                 port_index[(fb.Name, pin)] = {
                     "x": fb.x + p["x"], "y": fb.y + p["y"],
                     "kind": kind, "side": side,
                 }

         # ---- 5. 路由每条连接（正交折线；回环边绕到节点下方）----
         nodes_bottom = max((fb.y + fb.height for fb in fbs), default=0)
         back_y = nodes_bottom + 30

         def route(c):
             s = port_index[(c.source, c.source_pin)]
             t = port_index[(c.dest, c.dest_pin)]
             sx, sy, tx, ty = s["x"], s["y"], t["x"], t["y"]
             if s["side"] == "EAST" and t["side"] == "WEST" and sx < tx:
                 mid = (sx + tx) / 2
                 return [(sx, sy), (mid, sy), (mid, ty), (tx, ty)]
             if s["side"] == "EAST" and t["side"] == "WEST" and sx > tx:
                 return [(sx, sy), (sx + BACK_GAP, sy),
                         (sx + BACK_GAP, back_y), (tx - BACK_GAP, back_y),
                         (tx - BACK_GAP, ty), (tx, ty)]
             return [(sx, sy), (tx, sy), (tx, ty)]

         for c in self.EventConnections:
             c.points = route(c)
         for c in self.DataConnections:
             c.points = route(c)

         # ---- 6. 渲染 SVG ----
         W = layouted.get("width", 0)
         graph_h = max(layouted.get("height", 0), back_y + 20)
         H = HEADER + graph_h
         out_path = _default_output_path(self.Name, "svg", path)

         svg = []
         svg.append(
             f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'width="{W + 2*PAD}" height="{H + 2*PAD}" '
             f'viewBox="{-PAD} {-PAD} {W + 2*PAD} {H + 2*PAD}">'
         )
         svg.append(f'<title>{self.Name}</title>')
         svg.append('<rect x="{}" y="{}" width="{}" height="{}" fill="#fafafa"/>'.format(
             -PAD, -PAD, W + 2*PAD, H + 2*PAD))
         # 顶部网络名
         svg.append(
             f'<text x="0" y="{-PAD + 18}" font-family="sans-serif" '
             f'font-size="15" font-weight="bold" fill="#1a202c">{self.Name}</text>')

         # 图形主体下移 HEADER，给顶部网络名留位
         svg.append(f'<g transform="translate(0,{HEADER})">')

         # 6.1 连线（先画线，避免压在节点上）：事件=蓝实线，数据=绿虚线
         for c in self.EventConnections + self.DataConnections:
             if not c.points:
                 continue
             pts = " ".join(f"{x},{y}" for x, y in c.points)
             if c.kind == "data":
                 svg.append(
                     f'<polyline points="{pts}" fill="none" '
                     f'stroke="#2f855a" stroke-width="2" stroke-dasharray="6 4"/>')
             else:
                 svg.append(
                     f'<polyline points="{pts}" fill="none" '
                     f'stroke="#2b6cb0" stroke-width="2"/>')

         # 6.2 节点 + 端口
         def pin_label(port_id):
             return port_meta[port_id][1]

         for fb in fbs:
             nd = node_by_id[fb.Name]
             nx, ny = fb.x, fb.y
             nw, nh = fb.width, fb.height
             svg.append(
                 f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" '
                 f'rx="6" fill="#ffffff" stroke="#2d3748" stroke-width="1.5"/>')
             svg.append(
                 f'<text x="{nx + nw/2}" y="{ny + 16}" text-anchor="middle" '
                 f'dominant-baseline="middle" font-family="sans-serif" '
                 f'font-size="12" font-weight="bold" fill="#1a202c">{fb.Name}</text>')
             svg.append(
                 f'<line x1="{nx}" y1="{ny + 26}" x2="{nx + nw}" y2="{ny + 26}" '
                 f'stroke="#2d3748" stroke-width="1"/>')
             for p in nd["ports"]:
                 px, py = nx + p["x"], ny + p["y"]
                 kind = port_meta[p["id"]][2]
                 side = p["layoutOptions"]["port.side"]
                 if kind == "data":
                     # 数据端口：方块
                     svg.append(
                         f'<rect x="{px-4}" y="{py-4}" width="8" height="8" '
                         f'fill="#2b6cb0" stroke="#1a365d"/>')
                 else:
                     # 事件端口：圆点
                     svg.append(
                         f'<circle cx="{px}" cy="{py}" r="4" '
                         f'fill="#d69e2e" stroke="#744210"/>')
                 lx = px + 8 if side == "WEST" else px - 8
                 anchor = "start" if side == "WEST" else "end"
                 svg.append(
                     f'<text x="{lx}" y="{py}" text-anchor="{anchor}" '
                     f'dominant-baseline="middle" font-family="sans-serif" '
                     f'font-size="10" fill="#4a5568">{pin_label(p["id"])}</text>')

         svg.append('</g>')
         svg.append("</svg>")

         with open(out_path, "w", encoding="utf-8") as f:
             f.write("\n".join(svg))
         return out_path
