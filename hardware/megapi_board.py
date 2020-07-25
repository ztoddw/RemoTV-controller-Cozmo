import time, sys
import logging
import asyncio, threading
from megapi import MegaPi
log = logging.getLogger('RemoTV.hardware.megapi_tractor')

'''
The MegaPi is an arduino compatable microcontroller kit by Makeblock
The megapi can be mounted on top of a RaspberryPi
Requires the megapi library available in Pip.

This code should work for the Ultimate 2.0 kit robot,
The code assumes your wheels are standard DC motors in skidsteer formation
Arm is an encoded motor,
and the claw is the Encoder motor

Please look at MegapiBot._prepare_motor_states to configure motors
Look at MegapiBot.handle_input to configure robot input actions

For more information visit http://learn.makeblock.com/python-for-megapi/
MegaPi libary https://github.com/Makeblock-official/PythonForMegaPi
'''

# Default time per message
motorTime = 0.2
# Speed of drive motors
drivingSpeed = 150
# Speed of arm drive
armSpeed = 50
# Speed of grabber
grabberSpeed = 50

# Motor ID's
LEFT_TRACK = 2
RIGHT_TRACK = 3
GRABBER = 4
ARM = 1

def setup(robot_config):
    global megapiBot
    megapiBot = MegapiBot(robot_config)
    motorTime = robot_config.getfloat('megapi_board', 'motor_time')
    drivingSpeed = robot_config.getint('megapi_board', 'driving_speed')
    armSpeed = robot_config.getint('megapi_board', 'arm_speed')
    grabberSpeed = robot_config.getint('megapi_board', 'grabber_speed')
    LEFT_TRACK = robot_config.getint('megapi_board', 'left_track_port')
    RIGHT_TRACK = robot_config.getint('megapi_board', 'right_track_port')
    GRABBER = robot_config.getint('megapi_board', 'grabber_port')
    ARM = robot_config.getint('megapi_board', 'arm_port')

def move(args):
    try:
        megapiBot.handle_input(args)
    except:
        e = sys.exc_info()
        log.critical("MegapiBot Error: " + str(e))

# MegaPi Robot controller class
class MegapiBot:
    ## STARTREGION = Initialization
    # MegaPI Robot Controller class constructior
    # robot_config = Controller configuration data
    def __init__(self, robot_config):
        # Configure the motors
        self._prepare_motor_states()
        # Construct the megapi object
        self.bot = MegaPi()
        self.bot.start()
        log.debug("MegaPiBot Initialized")
        # Start the main_loop() in a separate thread
        self.tsk = threading.Thread(target=self.main_loop, daemon=True)
        self.tsk.start()
        log.debug("MegaPiBot Activated")

    # motors dictionary factory
    # Defines the motors speeds, ports, and status
    def _prepare_motor_states(self):
        self.motors = {
            LEFT_TRACK: self._default_motor_state(LEFT_TRACK, -drivingSpeed, False),
            RIGHT_TRACK: self._default_motor_state(RIGHT_TRACK, drivingSpeed, False),
            GRABBER: self._default_motor_state(GRABBER, grabberSpeed, False),
            ARM: self._default_motor_state(ARM, armSpeed, True)
        }

    # Defines the default states of motor objects.
    # Motor is an interger of the port number
    # Speed is a 0 to 255 interger of how fast the motor will turn when active
    # Encoder is a boolean which is true when using an encoder motor port
    def _default_motor_state(self, motor, speed, encoder):
        return {
            'motor': motor,
            'defaultSpeed': speed,
            'currentSpeed': 0,
            'newSpeed': 0,
            'expire': 100,
            'encoder': encoder
        }
    ## ENDREGION = Initialization

    ## REGION = Input Logic
    # Determines inputs
    def handle_input(self, args):
        global drivingSpeed
        command = args['button']['command']
        log.debug("MegaPiBot Got command " + command + " speed:" + str(drivingSpeed))
        if command == 'forward':
            self.drive(drivingSpeed, drivingSpeed)
        if command == 'reverse':
            self.drive(-drivingSpeed, -drivingSpeed)
        if command == 'left':
            self.drive(-drivingSpeed/2, drivingSpeed/2)
        if command == 'right':
            self.drive(drivingSpeed/2, -drivingSpeed/2)
        if command == 'close':
            self.move_motor(GRABBER, -grabberSpeed)
        if command == 'open':
            self.move_motor(GRABBER, grabberSpeed)
        if command == 'up':
            self.move_motor(ARM, -armSpeed)
        if command == 'down':
            self.move_motor(ARM, armSpeed)

    # Sets the LEFT_TRACK and RIGHT_TRACK
    # In one simple function
    def drive(self, leftMotorSpeed, rightMotorSpeed):
        global LEFT_TRACK, RIGHT_TRACK
        self.move_motor(LEFT_TRACK, leftMotorSpeed)
        self.move_motor(RIGHT_TRACK, rightMotorSpeed)

    # Update an individual motor with a speed.
    def move_motor(self, motor, speed):
        self.motors[motor]['newSpeed'] = int(speed)
        self.motors[motor]['expire'] = time.time() + motorTime
    ## ENDREGION = Input Logic

    ## REGION = Motor Thread
    # Threaded process for robot
    def main_loop(self):
        self.running = True
        log.debug("MegapiBot Loop starting!")
        try:
            while self.running:
                self.update_motors()
                time.sleep(0.1) # Runs the loop every about every tenth of a second
        except Exception as e:
            print("MegapiBot Loop Error: " + str(e))
            log.critical("MegapiBot Loop Error: " + str(e))

    # Loop through the configured motors
    def update_motors(self):
        for key in self.motors:
            self.update_motor(key)

    # Updates the motor with either a new speed, or stops a stale motor.
    # Key is the motor id in the motors dictonary
    def update_motor(self, motor_key):
        motor = self.motors[motor_key]
        if motor['newSpeed'] != motor['currentSpeed']:
            self.set_motor(motor_key, motor['newSpeed'])
        elif motor['currentSpeed'] != 0 and motor['expire'] < time.time():
            self.set_motor(motor_key, 0)

    # Updates the physical motor from the motor data
    # Sets the speed of the motor
    def set_motor(self, motor_key, speed):
        # make local copy of the motor
        motor = self.motors[motor_key]
        # Announce debug message
        log.debug("Running motor: " + str(motor_key) + " Speed: " + str(speed) + " Encoder: " + str(motor['encoder']) + " Time: " + str(time.time()))
        # Switch between encoder and normal DC motor
        if motor['encoder']:
            self.bot.encoderMotorRun(motor['motor'], speed)
        else:
            self.bot.motorRun(motor['motor'], speed)
        # configure record with updated speed
        motor['currentSpeed'] = speed
        motor['newSpeed'] = speed
        # Set the movement expiration
        motor['expire'] = time.time() + motorTime
        # update the record
        self.motors[motor_key] = motor
    ## ENDREGION = Motor Thread
