import random

class Hw:
    AMOUNT_MODULES = 4
    RESET_PIN = 1

    def __init__(self):
        pass
    
    def listenThroughModule(self, module):
        msg = self.readModule(module)

    def sendThroughRandomModule(self, msg):
        module = random.randint(0, self.AMOUNT_MODULES - 1)
        self.sendThroughModule(msg)

    def sendThroughModule(self, msg):
        pass

    def readModule(self, number):
        pass

    def initAllHw(self):
        pass

    def resetRobot(self):
        self.RESET_PIN = 1
