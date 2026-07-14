import re

class Position:
    def __init__(self,x,y):
        self.x=x
        self.y=y

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
