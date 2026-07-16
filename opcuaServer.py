"""OPC UA 服务器模块（独立 class）。

把 IEC 61499 功能块网络暴露成 OPC UA 地址空间：
  - 每个功能块 -> Server.Objects 下的一个 Object；
  - 每个功能块的 InputEvents / OutputEvents / InputVars / OutputVars
    -> 该 Object 下的 Variables（事件用 BOOL，变量按其数据类型）。
  - 输入侧（InputEvents / InputVars）可写，输出侧只读。

服务器在后台线程里跑 asyncua 的事件循环；主线程通过 start/stop 控制生命周期，
通过 register_app / register_function_block 建节点，通过 update_value 写值。
"""
import asyncio
import threading
from asyncua import Server


class OpcuaServer:
    def __init__(self, host="127.0.0.1", port=4840,
                 uri="http://iec61499.python.runtime"):
        self.host = host
        self.port = port
        self.uri = uri
        self.loop = None
        self.server = None
        self.idx = None
        self._stop_event = threading.Event()
        self._ready = threading.Event()      # server init 完成
        self._thread = None
        # (fb_name, var_name) -> asyncua Node
        self._var_nodes = {}

    # ---------------- 生命周期 ----------------
    def start(self):
        """启动后台线程，阻塞到 server 初始化完成（可建节点）为止。"""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=10):
            raise RuntimeError("OPC UA Server 启动超时")

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._serve())
        finally:
            self.loop.close()

    async def _serve(self):
        self.server = Server()
        await self.server.init()
        self.server.set_endpoint(
            f"opc.tcp://{self.host}:{self.port}/freeopcua/server/"
        )
        self.idx = await self.server.register_namespace(self.uri)
        self._ready.set()   # 通知主线程：可以注册节点了
        print(
            f"OPC UA Server 启动于: "
            f"opc.tcp://{self.host}:{self.port}/freeopcua/server/"
        )
        async with self.server:
            while not self._stop_event.is_set():
                await asyncio.sleep(0.2)
        print("OPC UA Server 已停止。")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    # ---------------- 内部：跨线程提交协程 ----------------
    def _run_coro(self, coro):
        if self.loop is None:
            raise RuntimeError("OpcuaServer 未启动")
        fut = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return fut.result()

    # ---------------- 注册功能块网络 ----------------
    def register_app(self, app):
        """把 app 里每个功能块建成 OPC UA Object，端口/变量建成 Variables。"""
        for fb in app.FunctionBlocks:
            self.register_function_block(fb)

    def register_function_block(self, fb):
        self._run_coro(self._register_function_block_coro(fb))

    async def _register_function_block_coro(self, fb):
        obj = await self.server.nodes.objects.add_object(self.idx, fb.Name)
        groups = (
            ("InputEvents",  fb.InputEvents,  True),
            ("OutputEvents", fb.OutputEvents, False),
            ("InputVars",    fb.InputVars,    True),
            ("OutputVars",   fb.OutputVars,   False),
        )
        for group_name, items, writable in groups:
            for item in items:
                value = self.coerce_value(item)
                node = await obj.add_variable(self.idx, item.name, value)
                if writable:
                    await node.set_writable()      # 输入侧允许客户端写
                self._var_nodes[(fb.Name, item.name)] = node

    @staticmethod
    def coerce_value(item):
        """把 Variable/Event 转成 OPC UA 可写的 Python 值。
        Event（无 datatype 属性）按整数计数占位（初值 0），与事件计数器一致；
        Variable 按其 datatype 转换。"""
        # Event：无 datatype，存事件计数（int）
        if not hasattr(item, "datatype"):
            return 0
        datatype = (item.datatype or "").upper()
        value = item.value
        if datatype in ("", "BOOL"):
            if value in (None, "", 0, "0", "False", "false", False):
                return False
            return True
        if datatype in ("UINT", "INT", "UDINT", "DINT", "USINT", "SINT",
                        "BYTE", "WORD", "DWORD", "TIME"):
            try:
                return int(value) if value not in (None, "") else 0
            except (TypeError, ValueError):
                return 0
        if datatype in ("REAL", "LREAL"):
            try:
                return float(value) if value not in (None, "") else 0.0
            except (TypeError, ValueError):
                return 0.0
        # 字符串/其它：原样返回
        return value if value not in (None, "") else ""

    # ---------------- 读写变量（供主线程调用）----------------
    def writeVariable(self, fb_name, var_name, value):
        """从任意线程把值写到某功能块某变量节点；节点不存在则跳过。
        非阻塞：把 write 协程提交到后台事件循环，不等结果。返回是否找到节点。"""
        node = self._var_nodes.get((fb_name, var_name))
        if node is None or self.loop is None:
            return False
        asyncio.run_coroutine_threadsafe(node.write_value(value), self.loop)
        return True

    # 兼容旧名
    def update_value(self, fb_name, var_name, value):
        return self.writeVariable(fb_name, var_name, value)

    def sync_from_app(self, app):
        """把 app 中所有功能块的事件计数 + 变量值推到 OPC UA。"""
        for fb in app.FunctionBlocks:
            for e in fb.InputEvents + fb.OutputEvents:
                self.writeVariable(fb.Name, e.name, int(e.count))
            for v in fb.InputVars + fb.OutputVars:
                self.writeVariable(fb.Name, v.name, self.coerce_value(v))


# --- 运行测试（主线程） ---
if __name__ == "__main__":
    from App import App

    server = OpcuaServer()
    server.start()
    app = App()
    server.register_app(app)
    print("已注册功能块:", [fb.Name for fb in app.FunctionBlocks])
    print("已注册变量节点数:", len(server._var_nodes))

    try:
        while True:
            import time
            time.sleep(2)
            server.sync_from_app(app)
            print("[Main] 同步一次 FB 输出值到 OPC UA")
    except KeyboardInterrupt:
        print("正在停止 OPC UA Server ...")
        server.stop()
        print("已退出。")
