from BasicFB import *


class E_RESTART(BasicFB):
    """E_RESTART 服务接口功能块（SIFB），对应 typelib/E_RESTART.fbt。

    按 IEC 61499，resource（runtime）通过它管理应用生命周期：冷启动 / 暖重启 /
    停止时分别发出 COLD / WARM / STOP 输出事件，再经网络事件连接 fan-out 到
    各功能块。本块无输入事件、无变量（与 .fbt 一致）。

    服务序列（resource -> E_RESTART）：
        start   -> COLD   冷启动
        restart -> WARM   暖重启
        stop    -> STOP   停止
    runtime 直接调用下列方法触发对应输出事件。
    """
    def __init__(self, name, position=None):
        super().__init__(name, "E_RESTART",
                         "Resource restart SIFB (COLD/WARM/STOP)",
                         Position=position)
        # 无 EventInputs / InputVars / OutputVars（与 E_RESTART.fbt 一致）
        self.addOutputEvent("COLD", "Information on cold restart")
        self.addOutputEvent("WARM", "Information on warm restart")
        self.addOutputEvent("STOP", "resource is to be stopped")

    def cold(self):
        """冷启动：发出 COLD。"""
        self.sendOutputEvent("COLD")

    def warm(self):
        """暖重启：发出 WARM。"""
        self.sendOutputEvent("WARM")

    def stop(self):
        """停止：发出 STOP。"""
        self.sendOutputEvent("STOP")
