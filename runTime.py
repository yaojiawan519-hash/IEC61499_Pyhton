import threading


class runTime:

    def __init__(self, App, opcua=True, opcua_host="127.0.0.1", opcua_port=4840,
                 watch=True, watch_interval=0.5):
        self.App = App
        self.rstart = self._find_restart()
        # OPC UA 服务器：把每个功能块建成 Object，端口/变量建成 Variables。
        # 未安装 asyncua 时优雅降级（不影响 runtime 本身运行）。
        self.opcua = None
        if opcua:
            try:
                from opcuaServer import OpcuaServer
                self.opcua = OpcuaServer(host=opcua_host, port=opcua_port)
                self.opcua.start()
                self.opcua.register_app(App)
                print(f"OPC UA: 已注册 {len(App.FunctionBlocks)} 个功能块")
            except Exception as e:
                print(f"OPC UA 启动失败（忽略）: {e}")
                self.opcua = None
        # statusWatch 线程：定时读取所有功能块的事件计数/变量值，
        # 通过 opcua.writeVariable 推到 OPC UA 信息模型（节流，避免频繁更新）。
        self._watch_stop = threading.Event()
        self._watch_thread = None
        self._watch_interval = watch_interval
        if watch and self.opcua is not None:
            self._watch_thread = threading.Thread(target=self._statusWatch,
                                                   daemon=True)
            self._watch_thread.start()

    def _find_restart(self):
        """在网络中查找 E_RESTART SIFB（按 FBType）。"""
        for fb in self.App.FunctionBlocks:
            if getattr(fb, "FBType", "") == "E_RESTART":
                return fb
        return None

    def _statusWatch(self):
        """后台线程：每隔 watch_interval 秒把所有功能块的事件计数与变量值
        写到 OPC UA。事件 -> count（int）；变量 -> 按数据类型转换后的值。"""
        opcua = self.opcua
        while not self._watch_stop.is_set():
            for fb in self.App.FunctionBlocks:
                for e in fb.InputEvents + fb.OutputEvents:
                    opcua.writeVariable(fb.Name, e.name, int(e.count))
                for v in fb.InputVars + fb.OutputVars:
                    opcua.writeVariable(fb.Name, v.name, opcua.coerce_value(v))
            self._watch_stop.wait(self._watch_interval)

    def run(self):
        if self.rstart is not None:
            self.rstart.cold()

    def warm(self):
        if self.rstart is not None:
            self.rstart.warm()

    def stop(self):
        self._watch_stop.set()
        if self._watch_thread is not None:
            self._watch_thread.join(timeout=1)
        if self.rstart is not None:
            self.rstart.stop()
        if self.opcua is not None:
            self.opcua.stop()
