from BasicFB import *

class PID(BasicFB):
    """增量式 PID 控制器功能块（带抗积分饱和与输出限幅）。

    事件：
        INIT -> INITO   初始化：清零内部状态（积分项、上一次误差）
        REQ  -> CNF     周期性计算：读取 SP/PV，计算 OUT 并发出确认
        RST  -> CNF     复位积分项与历史误差（保持参数）

    变量：
        输入：SP 设定值, PV 过程量, Kp, Ki, Kd, Ts 采样周期(秒),
              AutoMan 自动/手动切换, ManualIn 手动输出值,
              OutMin 输出下限, OutMax 输出上限
        输出：OUT 控制输出, Error 偏差, Integral 积分项, Derivative 微分项
    """
    def __init__(self, name, position=None):
        super().__init__(name, "PID", "PID Controller", Position=position)
        self.addInputEvent("INIT", "Initialize")
        self.addInputEvent("REQ", "Compute request")
        self.addInputEvent("RST", "Reset integrator")
        self.addOutputEvent("INITO", "Init confirmation")
        self.addOutputEvent("CNF", "Compute confirmation")

        self.addInputVar("SP", "REAL", "Setpoint", 0.0)
        self.addInputVar("PV", "REAL", "Process variable", 0.0)
        self.addInputVar("Kp", "REAL", "Proportional gain", 1.0)
        self.addInputVar("Ki", "REAL", "Integral gain", 0.0)
        self.addInputVar("Kd", "REAL", "Derivative gain", 0.0)
        self.addInputVar("Ts", "REAL", "Sample time [s]", 1.0)
        self.addInputVar("AutoMan", "BOOL", "1=Auto, 0=Manual", 1)
        self.addInputVar("ManualIn", "REAL", "Manual output value", 0.0)
        self.addInputVar("OutMin", "REAL", "Output lower limit", 0.0)
        self.addInputVar("OutMax", "REAL", "Output upper limit", 100.0)

        self.addOutputVar("OUT", "REAL", "Control output", 0.0)
        self.addOutputVar("Error", "REAL", "SP - PV", 0.0)
        self.addOutputVar("Integral", "REAL", "Integral term", 0.0)
        self.addOutputVar("Derivative", "REAL", "Derivative term", 0.0)

        # 内部状态（非 IEC 暴露变量）：积分累计、上一次偏差。
        self._integral = 0.0
        self._last_error = 0.0

        self.ecc_status = "START"

    def eventTrigger(self, event):
        match self.ecc_status:
            case "START":
                if event == "INIT":
                    self.ecc_status = "INIT"
                    self.actionInit()
                    self.sendOutputEvent("INITO")
                    self.ecc_status = "START"
                elif event == "REQ":
                    self.ecc_status = "REQ"
                    self.actionCompute()
                    self.sendOutputEvent("CNF")
                    self.ecc_status = "START"
                elif event == "RST":
                    self.ecc_status = "RST"
                    self.actionReset()
                    self.sendOutputEvent("CNF")
                    self.ecc_status = "START"

    def actionInit(self):
        """清零内部状态，输出归 0。"""
        self._integral = 0.0
        self._last_error = 0.0
        self.setVarValue("Integral", 0.0)
        self.setVarValue("Derivative", 0.0)
        self.setVarValue("Error", 0.0)
        self.setVarValue("OUT", 0.0)
        print(f"[{self.Name}] INIT -> state cleared")

    def actionReset(self):
        """仅复位积分项与历史误差，保留增益参数。"""
        self._integral = 0.0
        self._last_error = 0.0
        self.setVarValue("Integral", 0.0)
        self.setVarValue("Derivative", 0.0)
        print(f"[{self.Name}] RST -> integrator reset")

    def actionCompute(self):
        SP = float(self.getVarValue("SP") or 0.0)
        PV = float(self.getVarValue("PV") or 0.0)
        Kp = float(self.getVarValue("Kp") or 0.0)
        Ki = float(self.getVarValue("Ki") or 0.0)
        Kd = float(self.getVarValue("Kd") or 0.0)
        Ts = float(self.getVarValue("Ts") or 0.0)
        AutoMan = self.getVarValue("AutoMan")
        ManualIn = float(self.getVarValue("ManualIn") or 0.0)
        OutMin = float(self.getVarValue("OutMin") or 0.0)
        OutMax = float(self.getVarValue("OutMax") or 0.0)

        # 手动模式：直通手动输入，并同步内部误差状态。
        if not AutoMan:
            out = self._clamp(ManualIn, OutMin, OutMax)
            self.setVarValue("OUT", out)
            self.setVarValue("Error", SP - PV)
            print(f"[{self.Name}] REQ (Manual) -> OUT={out}")
            return

        error = SP - PV

        # 积分项累加（位置式积分）。采样时间为 0 时退化为纯 PD。
        if Ts > 0:
            self._integral += error * Ts
        derivative = 0.0
        if Ts > 0:
            derivative = (error - self._last_error) / Ts
        self._last_error = error

        # 抗积分饱和：积分项也限幅，避免长期饱和后恢复迟滞。
        self._integral = self._clamp(self._integral, OutMin, OutMax)

        # 位置式 PID：u = Kp*e + Ki*∫e + Kd*de/dt
        p_term = Kp * error
        i_term = Ki * self._integral
        d_term = Kd * derivative
        out = p_term + i_term + d_term
        out = self._clamp(out, OutMin, OutMax)

        self.setVarValue("Error", error)
        self.setVarValue("Integral", self._integral)
        self.setVarValue("Derivative", derivative)
        self.setVarValue("OUT", out)
        print(f"[{self.Name}] REQ -> error={error}, P={p_term}, "
              f"I={i_term}, D={d_term}, OUT={out}")

    @staticmethod
    def _clamp(value, low, high):
        if high < low:                  # 上下限配错，交换以保证 low<=high
            low, high = high, low
        if value < low:
            return low
        if value > high:
            return high
        return value
