import random

class Hw:
    AMOUNT_MODULES = 4
    RESET_PIN = 1

    def __init__(self):
        pass
    
    def listenThroughModule(self, module):
        msg = self.readModule(module)
        return msg

    def sendThroughRandomModule(self, msg):
        module = random.randint(0, self.AMOUNT_MODULES - 1)
        self.sendThroughModule(msg, module)
        return module

    def sendThroughModule(self, msg, module):
        pass

    def readModule(self, number):
        pass

    def initAllHw(self):
        print(f"[FYI] Initiated all hardware")

    def resetRobot(self):
        print(f"[FYI] Will restart the system now")
        self.RESET_PIN = True

    def signalThatsWrong(self):
        pass
        # maybe light up sth to let the user know?
