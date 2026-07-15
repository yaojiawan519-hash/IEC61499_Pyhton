from BasicFB import *
class MOTOR(BasicFB):
    def __init__(self, name):
        super().__init__(name)
        self.addInputEvent("Start")
        self.addInputEvent("Stop")
        self.addOutputEvent("Done")
        G=Variable("G", "BOOL", 0)
        self.addInputVar(G)
        STATUS=Variable("STATUS", "STRING", "")
        self.addOutputVar(STATUS)
    def eventTrigger(self, event):
            match self.ecc_status:
                case "Ready":
                    if event == "Start":
                        self.ecc_status = "Running"
                        self.actionStart()
                case "Running":
                    if event == "Stop":
                        self.ecc_status = "Ready"
                        self.actionStop()

    def actionStart(self):
            print("ECC is starting...")

    def actionStop(self):
            print("ECC is stopping...")   