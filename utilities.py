import re

class Position:
    def __init__(self,x,y):
        self.x=x
        self.y=y

class Connection:
    """功能块网络中的一条连接（事件连接或数据连接）。

    存储源/目的 (FB 名, 引脚名) 以及绘制时计算出的折线坐标 points。
    实现 __iter__ 使其可像旧版 4 元组 (sfb, spin, dfb, dpin) 一样被解包，
    因此网络运行时里 `for sfb, spin, dfb, dpin in self.EventConnections`
    之类的代码无需改动即可继续工作。
    """
    def __init__(self, source, source_pin, dest, dest_pin, kind="event"):
        self.source = source        # 源功能块名
        self.source_pin = source_pin  # 源引脚名
        self.dest = dest            # 目的功能块名
        self.dest_pin = dest_pin    # 目的引脚名
        self.kind = kind            # "event" 或 "data"
        self.points = []            # 绘制后的正交折线点 [(x, y), ...]（绝对坐标）

    def __iter__(self):
        # 兼容旧的 4 元组解包
        return iter((self.source, self.source_pin, self.dest, self.dest_pin))

    def __repr__(self):
        return f"{self.source}.{self.source_pin}->{self.dest}.{self.dest_pin}"

    @staticmethod
    def normalize(conn, kind="event"):
        """把一个连接规整为 Connection：已是 Connection 则补 kind，元组/列表则包装。"""
        if isinstance(conn, Connection):
            if not conn.kind or conn.kind == "event":
                conn.kind = kind
            return conn
        if isinstance(conn, (tuple, list)):
            return Connection(conn[0], conn[1], conn[2], conn[3], kind)
        return conn


# IEC 61499 TIME 字面量 -> 毫秒整数。
# 支持 "#T300ms" / "#T1s" / "#T2s500ms" / "#T1m" / "#T1h" / 纯数字（视为 ms）。
_TIME_RE = re.compile(r'#T?(\d+(?:\.\d+)?)(ns|us|µs|ms|s|m|h)?', re.IGNORECASE)
_UNIT_TO_MS = {'ns': 1e-6, 'us': 1e-3, 'µs': 1e-3, 'ms': 1.0, 's': 1000.0,
               'm': 60000.0, 'h': 3600000.0, None: 1.0}

def parseTime(value):
    """把 TIME 字面量或数值解析成毫秒整数；解析失败时原样返回（兼容已是数值的场景）。"""
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return value
    m = _TIME_RE.match(value.strip())
    if not m:
        # 纯数字字符串 -> 毫秒
        try:
            return int(value)
        except ValueError:
            return value
    num = float(m.group(1))
    unit = m.group(2)
    return int(num * _UNIT_TO_MS.get(unit, 1.0))
