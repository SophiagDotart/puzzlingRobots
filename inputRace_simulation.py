import numpy as np
import csv

#----- Parameters -----
numNodes = 100              #amount of robots = nodes that make up the swarm
timeSteps = 100             #amount of times each robot does a step = calculate its state and map 
numInputs = 5               #amount of inputs = games to be introduced in the swarm
initRootProb = 0.8          #initial value of probability for determining whether a node becomes a root
decayRate = 0.05            #decay rate for the exponential function
timeToPassive = 50          # clock out time if the active state and update count has not changed for too long

#----- States variables -----
PASSIVE = 0
ACTIVE = 1
states = np.zeros(numNodes, dtype=int)   # 0 = passive, 1 = active, 2 = root
inputs = np.zeros(numNodes, dtype=int)   # 0 = none
ROOT = np.zeros(numNodes, dtype=bool)

#----- Visualization variables
resultAmounts = []                       # store the results to display them
resultInputSurvival = []

dictInputs = {inp: {"active": 0, "root": 0, "introduced": None, "last seen": None} for inp in range( 1, numInputs + 1)} # dict to track all inputs throughout its lifetime
dictVanishInputs = {}

#----- Input arrival time -----
inputInputTimes = sorted(np.random.choice(range(timeSteps), size = numInputs))

#----- Additional functions -----
def expDecay(t, p0, dec):               # general exponential decay function 
    return p0 * np.power((1- dec), t)    # or continous p0b*np.e^(-dec*t); t = time step that passed 

def isNeigbour():                       # in hardware this is not required because each robot will not receive any information from non neighbours, so here is just an approx
    return np.random.rand() < (np.random.choice(8)/numNodes)

def becomeRoot():
    return np.random.rand() < expDecay(t, initRootProb, decayRate)    # calculate probability for becoming a root


#----- Simulation -----
for t in range(timeSteps + timeToPassive):                                  # timeToPassive so that each input organically has enough time to fade
    for idx, intro_time in enumerate(inputInputTimes, start=1):
        if t == intro_time:
            target = np.random.randint(0, numNodes)
            inputs[target] = idx
            states[target] = ACTIVE
            ROOT[target] = becomeRoot()
            dictInputs[idx]["introduced"] = t
    
    for i in range(numNodes):
        if (isNeigbour()):
            if (inputs[i] == 0):
                inputs[i] = np.random.randint(1, int(numInputs))            # Init new random input arrival times if it has not been done yet
            
            if isNeigbour() and inputs[i] != 0:
                ROOT[i] = becomeRoot()
                if (np.random.rand() < 0.05):                #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! change this to compare timestamps in the proper code
                    inputs[i] = np.random.randint(1, numInputs + 1)
                    states[i] = ACTIVE

        becomeRoot()
        
    
    #----- Calculate vanish delays -----
    vanishDelays = []
    for j in range(1, numInputs):
        if j in dictVanishInputs and ((j + 1) in dictInputs) and (dictInputs[j +1]["introduced"] is not None):
            vanishDelays.append(dictVanishInputs[j] - dictInputs[j + 1]["introduced"])
    avgVanishDelay = np.mean(vanishDelays) 

    #----- Create Diagrams -----
    for j in range(1,numInputs + 1):                                            # 0 would mean "no input", so we start at 1
        countPassive = np.sum((inputs == j) & (states == PASSIVE))    
        countActive = np.sum((inputs == j) & (states == ACTIVE))     
        countRoot = np.sum((inputs == j) & ROOT)
            

        if ((countActive + countRoot) > 0):
            dictInputs[j]["active"] = countActive
            dictInputs[j]["root"] = countRoot
            dictInputs[j]["last seen"] = t
        elif j > 1 and dictInputs[j-1]["last seen"] is not None:
                dictVanishInputs[j] = t                                         # store vanish time
        resultAmounts.append({                                                  # Store results in resultAmounts on amount of nodes in each state at each Step -> Summary graph
            'steps': t,
            'input': j,
            'passive': countPassive,
            'active': countActive,
            'root': countRoot,
        })
        resultInputSurvival.append({                                            # Store for input survival rate graph
            'steps': t,
            'input': j,
            'introduced': dictInputs[j]["introduced"],
            'last seen': dictInputs[j]["last seen"]
            })



#----- Export results -----
with open("simulation_resultAmountOfEachStateBySteps.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=['steps', 'input', 'passive', 'active', 'root'])
    f.write(
        f"Amount of each states and input at every time step\nParameters:\n"
        f"Amount of nodes: {numNodes}; Total amount of time/ steps: {timeSteps}; Amount of inputs: {numInputs}\n"
        f"Initial probability for expo. decay: {initRootProb}; Decay rate: {decayRate}\n")
    writer.writeheader()
    writer.writerows(resultAmounts)

print("Simulation complete! Results saved to simulation_resultAmountOfEachStateBySteps.csv")

with open("simulation_inputSurvivalRate.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=['time', 'input', 'active', 'root'], extrasaction='ignore')
    f.write(
        f"Survival and Spreading rates for inputs\n Parameters:\n"
        f"Amount of nodes: {numNodes}; Total amount of time/ steps: {timeSteps}\n Total amount on inputs: {numInputs}"
        f"Average circulating time of old inputs when new ones are introduced: {avgVanishDelay}") 
    writer.writeheader()
    for j in range(1, numInputs + 1):
        writer.writerow({
            "input": j,
            "introduced": dictInputs[j]["introduced"],
            "last_seen": dictInputs[j]["last seen"],
            "vanish_delay": dictVanishInputs.get(j, None)
        })

print(f"Simulation 2 complete! Results saved to simulation_inputSurvivalRate.csv")
