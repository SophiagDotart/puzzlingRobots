# puzzlingRobots

[More Info on the hardware side of the project](https://fabacademy.org/2025/labs/ilmenau/students/sophia-guzman/final-project.html
) 

### Possible feature expansions in the future:

- support of heterogenous swarms
- movement support for each robot
- support 3dimensional structures
- inter swarm coordination

### Code cleaning to-dos:

 -> Critical urgency
    - max msg resend to prevent the ACK response loop

 -> Important
    - Implement validation system for the RSPA
    - support directed communication
    - support input takeover

 -> Good 
    - Cleaner separation of abstraction levels in msg conversion
    - Cleaner separation of map data types in map conversion
    - Combine BUSY and IDLE flags
    - Implement message origin consistency across a handshake

 -> Nice-to-have
    - msg queue

 -> When hardware is connected
    - Run tests on hw
    - Measure the actual time for a step

## Explain workings of algorithm

### Priiority-based decition making

![diagram of how a robot thinks](/figures/ablaufPipelineV2.png) 

### Layout of communication protocol

![msg architecture](/figures/msgArchitectureV8.png)

### Formula for RSPA

$$X_{new}, Y_{new} = X_{sender} + X_{orientation}, Y_{sender} + Y_{orientation}$$ 
with $X_{orientation},Y_{orientation}  \in \{-1, 1 \}$
