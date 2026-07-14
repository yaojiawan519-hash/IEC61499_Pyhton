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
    runtime = runTime(App())
    print("FB network loaded:", runtime.App.Name)
    print("Blocks:", [fb.Name for fb in runtime.App.FunctionBlocks])
    runtime.run()
    print("\n网络运行中，按任意键退出...")
    _read_any_key()
    runtime.stop()
    print("已停止。")


if __name__ == "__main__":
    raise SystemExit(main())
