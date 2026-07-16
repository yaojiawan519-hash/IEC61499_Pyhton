import sys
import termios
import tty
from App import App
from runTime import  runTime


def _read_any_key():
    try:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
    except (ValueError, termios.error):
     
        try:
            return input()
        except EOFError:
            return ""
    try:
        tty.setcbreak(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main():
    app = App()
    runtime = runTime(app)
    print("FB network loaded:", runtime.App.Name)
    print("Blocks:", [fb.Name for fb in runtime.App.FunctionBlocks])

    # ---- FunctionBlockNetwork.draw 测试：把网络布局成 SVG ----
    try:
        svg_path = app.draw()
        print(f"\n[draw] SVG 已生成: {svg_path}")
        print("[draw] 功能块坐标:")
        for fb in app.FunctionBlocks:
            print(f"       {fb.Name:14s} x={fb.x} y={fb.y} "
                  f"w={fb.width} h={fb.height}")
        print("[draw] 连接折线点数:")
        for c in app.EventConnections + app.DataConnections:
            print(f"       [{c.kind:5s}] {c}  -> {len(c.points)} pts")
    except Exception as e:
        print(f"\n[draw] 绘制失败: {e}（未安装 pyelk？）")

    runtime.run()
    print("\n网络运行中，按任意键退出...")
    _read_any_key()
    runtime.stop()
    print("已停止。")


if __name__ == "__main__":
    raise SystemExit(main())
