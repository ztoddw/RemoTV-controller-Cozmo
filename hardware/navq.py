############################################################
# Remo.TV Controller for NXP/EmCraft 8M Mini NavQ          #
# This example code runs on a brushless NXP Cup Car w/ PX4 #
# Written by: Landon Haugh (landon.haugh@nxp.com)          #
############################################################

# Notes for controller.conf:
# Make sure video FPS is set to 30
# Make sure video res is set to 640x480

import logging
from time import sleep

log = logging.getLogger('RemoTV.hardware.navq')

try:
    from mavsdk import System
    from mavsdk.offboard import (Attitude, OffboardError)
    import asyncio
except ImportError:
    log.critical("You need to install mavsdk and asyncio")
    log.critical("Please install mavsdk for python and restart this script.")
    log.critical("To install: pip3 install mavsdk asyncio")

# Initialize MAVSDK and its asyncio loop
rover = System()
loop = asyncio.get_event_loop()

# Initial yaw/thrust values
yaw = 0
thrust = 0

def setup(robot_config):
    global rover
    global loop

    # MAVSDK uses the asyncio library.
    # asyncio allows for asynchronous code.
    # Because our function prototypes from Remo.TV are not async,
    # we must create nested async functions and run them with the looper.

    # Connect to rover w/ UART3 port
    # This requires the FMU to have TELEM2 enabled as a MAVLink port.
    async def connect():
        await rover.connect(system_address="serial:///dev/ttymxc2:921600")

    # If connection is good, continue
    async def check_connection():
        async for state in rover.core.connection_state():
            if state.is_connected:
                print("Rover discovered with UUID: {state.uuid}")
                break

    async def arm():
        await rover.action.arm()

    # Set initial attitude to 0 so the rover doesn't start driving
    async def set_attitude_zero():
        await rover.offboard.set_attitude(Attitude(0.0, 0.0, 0.0, 0.0))
        await asyncio.sleep(0.5)

    # Start offboard mode
    async def start():
        await rover.offboard.start()

    # Disarm
    async def disarm(): 
        await rover.action.disarm()

    # Now, run those functions in succession with the looper.
    loop.run_until_complete(connect())
    
    print("Waiting for rover to connect...")
    loop.run_until_complete(check_connection())

    print("-- Arming")
    loop.run_until_complete(arm())

    print("-- Setting initial setpoint")
    loop.run_until_complete(set_attitude_zero())

    print("-- Starting offboard")
    try:
        loop.run_until_complete(start())
    except OffboardError as error:
        print("Starting offboard mode failed with error code: \
            {error._result.result}")
        loop.run_until_complete(disarm())
        return

    return

def move(args):
    global yaw
    global thrust

    # Command received from Remo.TV controls
    command = args['button']['command']
    log.debug("Move command: %s", command)

    # Move rover at set yaw and thrust for one second, then stop.
    # If the rover continues forward, a crash is likely due to the
    # 3 second delay in video feed on Remo.TV.
    async def move_rover(yaw, thrust):
        print("Moving...")
        await rover.offboard.set_attitude(Attitude(0.0,0.0,yaw,thrust))
        await asyncio.sleep(1.0)
        await rover.offboard.set_attitude(Attitude(0.0,0.0,yaw,0.0))

    async def disarm():
        await rover.action.disarm()

    # Change yaw/thrust based on command received.
    if command == 'l':
        print("Moving left...")
        yaw = yaw - 45.0
        thrust = 0.1
        # move left

    if command == 'r':
        # move right
        print("Moving right...")
        yaw = yaw + 45.0
        thrust = 0.1

    if command == 'f':
        # move forwards
        thrust = 0.15
        print("Moving forward...")

    if command == 's':
        # stop
        thrust = 0

    if command == 'x':
        # stop
        thrust = -0.1

    # Move the rover. If command is denied, disarm and shutdown.        
    try:
        print([yaw,thrust])
        loop.run_until_complete(move_rover(yaw,thrust))
    except OffboardError as error:
        print("Starting offboard mode failed with error code: \
            {error._result.result}")
        loop.run_until_complete(disarm())
        return

    return
