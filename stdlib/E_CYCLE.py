import threading
import time
from BasicFB import *
from utilities import parseTime

class E_CYCLE(BasicFB):
    def __init__(self, name, position=None):
        super().__init__(name, "E_CYCLE", "Periodic event generator", Position=position)
        self.addInputEvent("START", "Start the periodic generation of events")
        self.addInputEvent("STOP", "Stop the generation of events")
        self.addOutputEvent("EO", "Periodically triggered output event")
        self.addInputVar("DT", "TIME", "cycle time")
        self.setVarValue("DT", 1000)  # 默认周期 1000 ms
        self._running = False
        self._thread = None

    def timerThread(self):
        while self._running:
            dt = parseTime(self.getVarValue("DT"))
            time.sleep(dt / 1000.0)  # 毫秒转秒
            if self._running:
                self.sendOutputEvent("EO")  # 经网络转发 EO

    def eventTrigger(self, event):
        if event == "START":
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self.timerThread, daemon=True)
                self._thread.start()
        elif event == "STOP":
            self._running = False  # 线程在下次循环检测到后自行退出
