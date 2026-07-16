from FunctionBlockNetwork import *
from utilities import Position
from stdlib.E_RESTART import E_RESTART
from stdlib.LED_BLINK import LED_BLINK


class Blink(FunctionBlockNetwork):
    """LED 闪灯应用网络：E_RESTART + 一个 LED_BLINK 复合功能块。

    按 IEC 61499，resource（runtime）不直接戳 LED_BLINK 的 START，而是触发
    E_RESTART 的 COLD/WARM/STOP，经事件连接 fan-out 到 LED_BLINK：
        RSTART.COLD -> LED_BLINK.START   冷启动
        RSTART.WARM -> LED_BLINK.START   暖重启
        RSTART.STOP -> LED_BLINK.STOP    停止
    """
    def __init__(self, blinks=5, period="#T400ms"):
        rstart = E_RESTART("RSTART", Position(-100, 0))
        led = LED_BLINK("LED_BLINK", blinks=blinks, period=period,
                        position=Position(0, 0))
        fbs = [rstart, led]
        ev = [
            (rstart.Name, "COLD", led.Name, "START"),
            (rstart.Name, "WARM", led.Name, "START"),
            (rstart.Name, "STOP", led.Name, "STOP"),
        ]
        super().__init__("Blink", "LED blink network", fbs,
                         EventConnections=ev, DataConnections=[])
        # 子块 network 由父类 __init__ 回填为 self；
        # LED_BLINK 的输出事件经本网络 NotifyEvent 上行。

    def NotifyEvent(self, FB_name, event):
        """观察 LED_BLINK 的输出事件（BLINK/DONE）。"""
        if FB_name == "LED_BLINK":
            cv = self.ReadVarValue("LED_BLINK", "CV")
            print(f"[Blink] {event}  (CV={cv})")
        super().NotifyEvent(FB_name, event)


if __name__ == "__main__":
    from runTime import runTime

    runtime = runTime(Blink())
    print("FB network loaded:", runtime.App.Name)
    print("Blocks:", [fb.Name for fb in runtime.App.FunctionBlocks])
    print("E_RESTART:", runtime.rstart.Name if runtime.rstart else "<缺失>")
    runtime.run()
    input("\n网络运行中，按回车退出...\n")
    runtime.stop()
    print("已停止。")
