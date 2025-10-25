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
inputs = np.zeros(numNodes, dtype=int)   # 0 = none, >0 = input ID
ROOT = np.zeros(numNodes, dtype=bool)

#----- Visualization variables
resultAmounts = []                       # store the results to display them
resultInputSurvival = []

anyInputsEver = set()                   #obj to save all inputs ever to display
activeInputs = set()                    # obj to save all inputs currently still represented (at least by 1 node) in the swarm 

#----- Input arrival time -----
inputInputTimes = sorted(np.random.choice(range(timeSteps), size = numInputs))

#----- Additional functions -----
def expDecay(t, p0, dec):               # general exponential decay function 
    return p0 * np.power((1- dec), t)    # or continous p0b*np.e^(-dec*t); t = time step that passed 

def isNeigbour():                       # in hardware this is not required because each robot will not receive any information from non neighbours, so here is just an approx
    return np.random.rand() < (np.random.choice(8)/numNodes)

def becomeRoot():
    pRoot = expDecay(t, initRootProb, decayRate)    # calculate probability for becoming a root
    return np.random.rand() < pRoot

#----- Simulation -----
for t in range(timeSteps + timeToPassive):                                  # timeToPassive so that each input organically has enough time to fade
    for i in range(numNodes):
        if (isNeigbour() == 1):
            if (inputs[i] == 0):
                inputs[i] = np.random.randint(1, int(numInputs))            # Init new random input arrival times if it has not been done yet
            
            if (states[i] == 1 & (np.random.rand() < 0.05)):                #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! change this to compare timestamps in the proper code
                inputs[i] = np.random.randint(1, numInputs + 1)

            for counter in range(1, numInputs + 1):                         # This is the 3 random peer approach gpt mentioned. Change to neighbour limited one
                activeInputs.add(counter)
                if counter not in range(anyInputsEver):
                    anyInputsEver.add(counter)
        becomeRoot()
        
    

    #----- Create Diagrams -----
    alive_inputs = {inp for inp in activeInputs if np.any(inputs == inp)}       # Check which inputs are still represented by at least one node
    for j in range(1,numInputs + 1):                                            # 0 would mean "no input", so we start at 1
        countPassive = np.sum((inputs == j) and (states == PASSIVE))    
        countActive = np.sum((inputs == j) and (states == ACTIVE))     
        countRoot = np.sum((inputs == j) and ROOT)
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
            'introduced': int(j in activeInputs & (t == inputInputTimes(j-1))),
            # maybe add a last seen?
            #'last seen': max_t where input j !=0 
            'last seen': tLastSeen
            })
        countPassive = 0
        countActive = 0
        countRoot = 0
        tLastSeen = 0


#----- Export results -----
with open("simulation_resultAmountOfEachStateBySteps.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=['step', 'input', 'passive', 'active', 'root'])
    f.write(f"Amount of each states and input at every time step\n Parameters:\n Amount of nodes: {numNodes}; Total amount of time/ steps: {timeSteps}\n Initial probability for expo. decay: {initRootProb}; Decay rate: {decayRate}\n Amount of inputs: {numInputs}")
    writer.writeheader()
    writer.writerows(resultAmounts)

print("Simulation complete! Results saved to simulation_resultAmountOfEachStateBySteps.csv")

with open("simulation_inputSurvivalRate.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=['time', 'input', 'active', 'root'])
    f.write(f"Survival and Spreading rates for inputs\n Parameters:\n Amount of nodes: {numNodes}; Total amount of time/ steps: {timeSteps}\n Total amount on inputs: {numInputs}") 
    # avg survival rate after introduction of next input? avg lifespan normed to the length of time to the introduction to the next input??!!!!!!!!!!!!!!!!!!
    writer.writeheader()
    writer.writerows(resultInputSurvival)

print(f"Simulation 2 complete! Results saved to simulation_inputSurvivalRate.csv")
