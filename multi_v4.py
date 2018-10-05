# TEAM SYMBIOSIS
# SIT302 - Project Delivery
# Trimester 2, 2018
# CrazyFlie 2.0 Drone - Flight-Control Solution Multi-waypoint Upgrade (v4)

# NOTE: This version flies multi-waypoints with time delays (set by user) at each point
#       Designed to be used in conjunction with Unity / C#

"""
Bitcraze CrazyFlie 2.0 Drone
 - Automatic Flight-Control Prototype Solution

This program connects to the Crazyflie at the `URI` and runs a multi-waypoint flight sequence.

This program does not utilise an external location system: it has been
tested with (and designed for) the Flowdeck in line with our Sprint 2 goals.

Written by:
Paul Hammond (for Symbiosis Team)
216171484
"""

"""
ATTENTION: 	
X, Y, Z follows standard 3-D Co-ordinate Geometry (+Y = Front, +X = Right, +Z = Up)
Positive rotation is anti-clockwise
"""

import logging
import time
import math
import sys
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)    # investigate this for logging battery level

'''	   
GENERAL ATTRIBUTES
'''
# Constants
HOVER_HEIGHT_STD = 0.5        # metres
HOVER_TIME_STD = 0.2          # seconds
DESTINATION_HOVER_TIME = 15   # seconds (to be set as desired)
INIT_VELOCITY_FWD = 0.5       # metres / sec
VELOCITY_SIDE = 0             # do not modify
URI = "radio://0/80/2M"       # CrazyRadio Frequency

# Global Variables
heightDrone = 0
yawRate = 0
climbRate = 0
arrayX = []                  # X Coordinates for each point
arrayY = []                  # Y Coordinates for each point
arrayZ = []                  # Z Coordinates for each point
arrayOrientation = []        # Orientation based on 360 degree bearings (eg. 0/360, 90, 180, 270)
arrayRotationAngle = []      # Rotation angle for drone to face next point
arrayVelocityFWD = []
arrayTravelTime = []
arrayDistance = []
arrayHeightDifference = []   # Vertical change between two points
arrayHoverTime = []          # Duration of hover (seconds) at each waypoint


'''
Methods
'''
# Method: Calculate Hypotenuse (using Pythagoras Theorem) and return value
def Hypotenuse(opposite, adjacent):
    return math.sqrt((opposite * opposite + adjacent * adjacent))


# Method: Fly and climb / descend to next designated waypoint (x, y, z)
def Traverse(velocityFWD, travelTime, currentHeight, destinationHeight):
    # Calculate number of iterations and climb rate
    iterations = travelTime * 10
    heightDrone = currentHeight
    climbRate = (destinationHeight - currentHeight) / iterations      # +ve = ascend, -ve = descend  
    
    # Traverse Flight Path
    print("\nTraversing to height of %f" %(destinationHeight))
    for i in range(iterations):
        heightDrone += climbRate
        print("Current height: %.1f" %(heightDrone))
        cf.commander.send_hover_setpoint(velocityFWD, VELOCITY_SIDE, 0, heightDrone)
        time.sleep(0.1)


# Method: Hover Drone
def Hover(hoverHeight, hoverTime):
    # Convert time to iterations
    iterations = int(hoverTime * 10)  

    # Hover Drone
    print("\nHovering at %f metres" %(hoverHeight))
    for i in range(iterations):
        cf.commander.send_hover_setpoint(0, 0, 0, hoverHeight)
        time.sleep(0.1)


# Method: Rotates the drone anti-clockwise whilst in hover
def Rotate(rotationAngle, hoverHeight):
    YAWTIME = 2 	# seconds

    # Calculate yawRate and iterations
    yawRate = rotationAngle / YAWTIME    # degrees / second           
    iterations = YAWTIME * 10

    # Rotate Drone
    print("\nRotating to %f degrees" %(rotationAngle))
    for i in range(iterations):
        cf.commander.send_hover_setpoint(0, 0, yawRate, hoverHeight)
        time.sleep(0.1)


# Method: Run the flight sequence
def RunFlightSequence(angle, velocityForward, travelTime, hoverTime, heightCurrent, heightDestination):
    # HOVER AT WAYPOINT FOR USER-ALLOTED TIME (SEC)
    if (hoverTime != 0):
        print("Hovering at waypoint for %f seconds" %(hoverTime))
        Hover(heightCurrent, hoverTime)

    # ROTATE DRONE TOWARDS NEXT WAYPOINT
    # Rotate to correct orientation
    if (angle != 0):
        Rotate(angle, heightCurrent)
        Hover(heightCurrent, HOVER_TIME_STD)
           
    # TRAVERSE TO NEXT WAYPOINT
    if (velocityForward != 0):
        Traverse(velocityForward, travelTime, heightCurrent, heightDestination)


# Method: Get co-ordinates from file
def GetCoords():
    inputData = ""
    deliminator = ","
    #filePath = "C:\\Test\\MW\\InspectorOout\\test.txt"
    filePath = "C:\\Test\\Multi-waypoints\\Waypoints.txt"

    #Open File and read contents
    myFile = open(filePath, 'r')
    inputData = myFile.readlines()

    # Read each line (co-ordinate) and assign to appropriate array
    for line in inputData:
        contents = line.split(deliminator)
        arrayX.append(float(contents[0]))
        arrayY.append(float(contents[1]))
        arrayZ.append(float(contents[2]))
        arrayHoverTime.append(float(contents[3]))

    # Close File
    myFile.close()


# Method: Display flight parameters on console
def DisplayFlightParameters():
    index = 0

    print("\nDisplaying flight parameters...\n")
    print("Point \t\tX-Coordinate \tY-Coordinate \tZ-Coordinate \tHover Time (sec)")
    # Traverse through each array and display co-ordinate values
    while (index < len(arrayX)):
        print("%d: \t\t%.1f \t\t%.1f \t\t%.1f \t\t%.1f" %(index, arrayX[index], arrayY[index], arrayZ[index], arrayHoverTime[index]))
        index += 1

    print("\nDistances...")
    for distance in arrayDistance:
        print(distance)

    print("\nTravel Times...")
    for travelTime in arrayTravelTime:
        print(travelTime)

    print("\nForward Velocities...")
    for velocity in arrayVelocityFWD:
        print(velocity)

    print("\nHeight Differences...")
    for height in arrayHeightDifference:
        print("%.1f" %(height))

    print("\nOrientations...")
    for bearing in arrayOrientation:
        print(bearing)

    print("\nAngles...")
    for angle in arrayRotationAngle:
        print(angle)


# Calculates and returns the drone orientation according to 360 degree bearings (navigation)
def CalculateOrientation(x, y):
    angle = 0.0
    orientation = 0
    zero_value = False
    
    # Calculate orientation if flight path lies parallel to x or y axis (ie delta x or y = 0)
    if (x == 0):
        zero_value = True
        if (y > 0):
            orientation = 0
        else:
            orientation = 180
    if (y == 0):
        zero_value = True
        if (x > 0):
            orientation = 90
        else:
            orientation = 270
        
    # Calculate orientation if flight path does not lie parallel to x or y axis
    if (zero_value is False):
        if (x < 0 and y > 0):
            angle = abs(math.degrees(math.atan(x / y)))
        else:
            angle = abs(math.degrees(math.atan(y / x)))
    
        # Calculate orientation according to line gradients
        if (x < 0 and y > 0):
            orientation = 360 - int(angle)
        elif (x > 0 and y > 0):
            orientation = int(angle)
        elif (x > 0 and y < 0):
            orientation = 90 + int(angle)
        elif (x < 0 and y < 0):
            orientation = 270 - int(angle)

    return orientation


# Calculates and returns the drone's angle to rotate to next waypoint     
def CalculateRotationAngle(orientation_current, orientation_destination):
    rotationAngle = 0.0
    
    # Calculate Angle
    rotationAngle = orientation_destination - orientation_current

    # Adjust Angle to account for 360 / 0 degree error
    if (rotationAngle > 180):
        rotationAngle += -360
    elif (rotationAngle < -180):
        rotationAngle += 360
        
    return rotationAngle


# Calculate and return travel time as an integer value
def CalculateTravelTime(distance):
    return (round)(distance / INIT_VELOCITY_FWD)          


# Calculate and return drone velocity to accomodate for time as an integer
def CalculateForwardVelocity(distance, travelTime):
    return distance / travelTime                     


# Calculate all of the flight parameters and store in arrays
def CalculateFlightParameters():
    index = 0
    orientation = 0

    # Append Start Orientation (Bearing: 0 degrees)
    arrayOrientation.append(0)
    
    while (index < len(arrayX) - 1):
        X = arrayX[index + 1] - arrayX[index]
        Y = arrayY[index + 1] - arrayY[index]
        Z_Delta = arrayZ[index + 1] - arrayZ[index]

        # Calculate and assign flight distances between points
        arrayDistance.append(Hypotenuse(X, Y))

        # Calculate and assign travel times between points
        arrayTravelTime.append(CalculateTravelTime(arrayDistance[index]))

        # Calculate and assign forward velocities between points
        arrayVelocityFWD.append(CalculateForwardVelocity(arrayDistance[index], arrayTravelTime[index]))

        # Calculate and assign height changes across points
        #arrayHeightDifference.append(HOVER_HEIGHT_STD + Z)
        arrayHeightDifference.append(Z_Delta)

        # Calcualte and append orientation between points
        arrayOrientation.append(CalculateOrientation(X, Y))                 
        
        index += 1

    # Append End Orientation (Bearing: 0 degrees)
    arrayOrientation.append(0)

    # Calculate and assign drone rotation angles
    index = 0
    while (index < len(arrayOrientation) - 1):
        arrayRotationAngle.append(CalculateRotationAngle(arrayOrientation[index], arrayOrientation[index + 1]))
        index += 1
    
    
'''			
# Flight-Control Program
'''
if __name__ == '__main__':
    # Get coordinates and calculate flight parameters
    GetCoords()
    CalculateFlightParameters()
    DisplayFlightParameters()
    
    #'''
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf

        cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        cf.param.set_value('kalman.resetEstimation', '0')
        time.sleep(2)

        # TAKE-OFF
        heightDrone = HOVER_HEIGHT_STD
        Hover(heightDrone, HOVER_TIME_STD)
        
        # FLY TO WAY-POINTS
        index = 0
        while (index < len(arrayDistance)):
            RunFlightSequence(arrayRotationAngle[index], arrayVelocityFWD[index], arrayTravelTime[index], arrayHoverTime[index], arrayZ[index], arrayZ[index + 1])
            index += 1

        # Rotate back to origin
        RunFlightSequence(arrayRotationAngle[index], 0, 0, arrayHoverTime[index], HOVER_HEIGHT_STD, 0)
        
        # LAND and SHUTDOWN
        Hover(0.1, 1)                           # Land
        
        # Engine shut-off
        cf.commander.send_stop_setpoint()
    #'''
