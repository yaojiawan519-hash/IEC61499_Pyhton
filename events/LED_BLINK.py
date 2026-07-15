from BasicFB import *
from CompositeFunctionBlock import CompositeFunctionBlock
from events.E_CYCLE import E_CYCLE
from events.E_CTD import E_CTD
from events.E_SWITCH import E_SWITCH
from utilities import Position


class LED_BLINK(CompositeFunctionBlock):
    """LED 闪灯复合功能块（无 ECC，纯路由子网络）。

    闪烁表现为对外输出一串 BLINK 脉冲事件，闪烁指定次数后输出 DONE。
    真正的 LED 电平翻转应由外部一个带 ECC 的 BasicFB 消费 BLINK 来完成
    （复合功能块本身没有 ECC，不能持翻转状态）。

    内部子网络：
        E_CYCLE  -- 周期滴答发生器（DT = 闪烁周期）
        E_CTD    -- 倒计数器（PV = 闪烁次数，减到 0 时 Q=1）
        E_SWITCH -- 按 E_CTD.Q 把滴答切换到 BLINK(仍在闪) 或 DONE(闪完)

    事件流：
        START -> CTD.LD        装入闪烁次数（Q=0）
        START -> CYCLE.START   启动周期滴答
        STOP  -> CYCLE.STOP
        CYCLE.EO -> SW.EI
        SW.EO0 (G=0) -> CTD.CD      仍需闪：递减
        SW.EO0 (G=0) -> 本块.BLINK  输出一次闪烁脉冲
        SW.EO1 (G=1) -> CYCLE.STOP  闪完：停止滴答
        SW.EO1 (G=1) -> 本块.DONE   输出完成
    数据流：
        CTD.Q  -> SW.G
        CTD.CV -> 本块.CV   （把剩余次数引到对外输出变量）
    """
    def __init__(self, name, blinks=5, period="#T500ms", position=None):
        # ---- 内部子功能块 ----
        cycle = E_CYCLE("CYCLE", Position(0, 0))
        cycle.setVarValue("DT", period)
        ctd = E_CTD("CTD", Position(0, 200))
        ctd.setVarValue("PV", blinks)
        sw = E_SWITCH("SW", Position(0, 100))
        fbs = [cycle, sw, ctd]

        me = name  # 事件连接里复合块自身做源/目的时的名字（= self.Name）
        # ---- 事件连接：(源FB, 源引脚, 目的FB, 目的引脚) ----
        ev = [
            (me, "START", ctd.Name, "LD"),        # 装入闪烁次数
            (me, "START", cycle.Name, "START"),   # 启动滴答
            (me, "STOP", cycle.Name, "STOP"),
            (cycle.Name, "EO", sw.Name, "EI"),    # 滴答 -> 切换
            (sw.Name, "EO0", ctd.Name, "CD"),     # G=0: 递减
            (sw.Name, "EO0", me, "BLINK"),        # G=0: 闪烁脉冲
            (sw.Name, "EO1", cycle.Name, "STOP"), # G=1: 停止
            (sw.Name, "EO1", me, "DONE"),         # G=1: 完成
        ]
        # ---- 数据连接 ----
        dt = [
            (ctd.Name, "Q", sw.Name, "G"),        # 计数到位 -> 切换
            (ctd.Name, "CV", me, "CV"),           # 剩余次数 -> 对外输出
        ]

        super().__init__(name, "LED blinker (E_CYCLE+E_CTD+E_SWITCH)", fbs,
                         Position=position,
                         EventConnections=ev, DataConnections=dt)
        # 对外接口
        self.addInputEvent("START", "开始闪烁")
        self.addInputEvent("STOP", "停止闪烁")
        self.addOutputEvent("BLINK", "一次闪烁脉冲")
        self.addOutputEvent("DONE", "闪烁完成")
        self.addOutputVar("CV", "UINT", "剩余闪烁次数", 0)


class _StdoutObserver:
    """把复合块的输出事件打印到 stdout，模拟上层网络消费者。
    仅用于独立演示；放进上层网络时 network 由父网络回填，无需此观察者。"""
    def __init__(self, owner_name):
        self.owner_name = owner_name

    def NotifyEvent(self, FB_name, event):
        print(f"[{self.owner_name}] 输出事件 -> {event}")


if __name__ == "__main__":
    import time
    led = LED_BLINK("LED1", blinks=5, period="#T400ms")
    led.network = _StdoutObserver(led.Name)   # 独立演示：挂观察者接收输出事件
    print(led)
    led.eventTrigger("START")
    time.sleep(3.0)
    print("最终 CV =", led.getVarValue("CV"))
