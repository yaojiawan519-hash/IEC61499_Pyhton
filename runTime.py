class runTime:
    def __init__(self, App):
        self.App = App
    def run(self):      
        self.App.TriggerEvent("E_CYCLE_1", "START")

    def stop(self):
        self.App.TriggerEvent("E_CYCLE_1", "STOP")

