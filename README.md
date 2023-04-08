Updates on 4/8/23:

For Windows pc, for a Cozmo robot. Main files (video/ffmpeg.py, controller.py, extended_commands.py, networking.py, robot_util.py) were modified, and untested with other robot types.

Note: The Cozmo SDK works only with Python up to Python version 3.7.9.
Your best option for video capture (or at least the best that worked for me) is using your pc's integrated webcam. Review the controller.conf file for different options that I tried. You might need to change or add video / audio settings in that file.

After you get your remo.tv key and install the cozmo sdk (see instructions for cozmo for windows: http://cozmosdk.anki.com/docs/install-windows.html#install-windows), you might also need to install these:

pip install socketIO-client configparser
pip3 install --user cozmo[camera]
pip3 install --user --upgrade cozmo
ffmpeg

You need a mobile phone to connect to your Cozmo, which phone needs to connect to your pc using one of these:
Android Debug Bridge (if using android phone)
ITunes (if using i-phone)

I spent a while figuring out how to get to get the python code to connect to remo.tv without SSL errors- finally did these steps (along with code changes) to resolve them:

1. Found the path for the certifs using this python code:
import requests as r
print(r.certs.where())

In my case this was at:    C:\Users\user\AppData\Roaming\Python\Python37\site-packages\certifi\

2. Added cert into for remo.tv (retrieved from browser lock symbol) to the cert file.


Features I added with my code changes:

1. Copy from the "Cozmo hotkeys.txt" file and paste into the JSON code box for the "Edit buttons" feature on your robot page. See description text in that file for what the hotkeys do- it should show up on your robot page also.

2. I could not get the "type=cozmo_vid" option in the controller.conf file to work, so I used the ffmpeg option to use my laptop's integrated webcam as the main camera source, and captured cozmo's 1st person camera view to be shown as an overlay. (So run_video() is not used.) The controller.conf file allows multiple video options which can be selected using the ".video restart" command (See below) -- the "StartingVideoOption" option in controller.conf tells which option is selected to start with.  Review and change the camera_device options in controller.conf according to your own camera devices you will use.  Use "ffmpeg -sources" at a command line to view your audio and video sources connected to your pc.

3. More extended chat commands: (in addition to those already documented)

.video restart [1-n] :  restart your video using the video option # you give it.  It's zero-based for this command.  In the controller.conf file it's 1-based, so will be off by 1.

.cam [on | off]  : turn on or off cozmo's 1st person camera view, as an overlay.

.cam n  : Set delay between cozmo's 1st person camera captures. See note above. n is # of seconds- must be a positive # < 10.

.cam snap  : turn full screen snapshot on.  You can use ".cam" to turn off. -- this is hard-coded to capture a snapshot from specific local lip address (as from an ip camera).  To use this, after setting up your camera to broadcast to a local ip, enter that ip in the cozVid function.

.cam snap n  : turn full screen snapshot on, and set delay between snapshot captures. See note above. n is # of seconds- must be a positive # < 100.

.cam [ul | um | ur | ml | mr | ll | lm | lr | fs] [big]  : Turn on cozmo's 1st person cam view as overlay in upper-left, upper-middle, upper-right, middle-left, middle-right, lower-left, lower-middle, lower-right, or full-screen. If "big" is included, the overlay is shown bigger.

.a [1-9]  : execute a specific animation (after using "g" hotkey) with your Cozmo


## remo.tv is an open telerobotics platform designed for controling and sharing control of robots online in real time.
## WARNING: This software is currently under development, so you may encounter frequent issues as updates are made. You can check out the [wiki](https://docs.remo.tv) for a more indepth view of what's currently supported.
This controller software is designed to run on your robot and will connect with our development server. It's tuned to support Raspberry Pi based robots, however there is extensive support for other hardware configurations.

## Basic setup
If this is your first time working with a Raspberry Pi or Linux, we recommend following our [initialization tutorial](https://docs.remo.tv/en/stable/controller/getting_started.html) to get started.

## Installing remotv control scripts on a Raspberry Pi

If doing things manually isn't your style, we made an [optional guided installation](https://docs.remo.tv/en/stable/controller/guided_installation.html) script that handles mostly everything for you.

The RasPi will need the following things install so it can talk to your motors and talk to the internet. Make sure you don’t get any errors in the console when doing the step below. If you have an issue, you can run this line again, and that will usually fix it!

1. Install the required software libraries and tools. Make sure you don’t get any errors in the console when doing the step below. If you have an issue, you can run this line again, and that will usually fix it!

   ```sh
   sudo apt update
   sudo apt upgrade -y
   sudo apt install ffmpeg python-serial python-dev libgnutls28-dev espeak python-smbus python-pip git
   ```

2. Download the remotv control scripts from our github

   ```sh
   git clone https://github.com/remotv/controller.git ~/remotv
   ```

3. Install python requirements

   ```sh
   sudo python -m pip install -r ~/remotv/requirements.txt
   ```

4. Open the new `remotv` directory

   ```sh
   cd remotv
   ```

5. Copy `controller.sample.conf` to `controller.conf`

   ```sh
   cp controller.sample.conf controller.conf
   ```

## Configure the controller

1. Edit the `controller.conf` file created in the previous section.
   ```sh
   nano controller.conf
   ```
2. Configure the `[robot]` section

   - `owner` should be the username you have registered the robot under on the remo.tv site.
   - `robot_key` is the API key for your robot that you made on the site.
      - Your API key is LONG. It should look something like `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6InJib3QtNTVjZjJmMjUtNjBhNS00ZDJkLTk5YzMtOGZmOGRiYWU4ZDQ1IiwiaWF0IjoxNTczNTExMDA2LCJzdWIiOiIifQ.LGXSBSyQ4T4X5xU_w3QJD6R3lLjrrkw_QktOIDzRW5U`. If it is not this long, you have not copied the full key.
   - `turn_delay` is only used by the `motor_hat` and `mdd10`. This changes how long your bot turns for. I suggest you leave this at the default value until after you bot is moving.
   - `straight_delay` is only used by the `motor_hat` and `mdd10`. This changes how long your bot turns for. I suggest you leave this at the default value until after you bot is moving.
   - `type` should be the hardware type for the motor controller of your bot. Available types are currently.
     - `adafruit_pwm`
     - `cozmo`
     - `gopigo2`
     - `gopigo3`
     - `l298n`
     - `maestro-serv`
     - `max7219`
     - `mc33926`
     - `mdd10`
     - `motor_hat`
     - `motozero`
     - `none`
     - `owi_arm`
     - `pololu`
     - `serial_board`
     - `telly`
     - `thunderborg`
     - `megapi_board`
   - Configure your hardwares section. Each hardware type can have their own section it the controller. Look through the file for a section named the same as your hardware controller. If the section exists, read through it and adjust the variable as required.

3. Configure the `[camera]` section
   - `no-mic` This allows the microphone to be disabled.
   - `no-camera` This allows the camera to be disabled.
   - `type` This sets the audio / video handler to use. Currently only ffmpeg and ffmpeg-arecord are supported.
   - `x_res` Sets the resolution for the x axis.
   - `y_res` Sets the resolution for the y axis.
   - `camera_device` Sets the device name for the camera.
   - `audio_hw_num` Set the audio hardware number for the microphone.
4. Configure the `[tts]` section
   - `tts_volume` This is the volume level you want your bot to start with.
   - `anon_tts` This allows you to enable or disable anonymous users access to your bots TTS features.
   - `filter_url_tts` This option allows URLs pasted into chat to be blocked from the TTS function.
   - `ext_chat` This enables or disables the extended chat functions.
   - `hw_hum` This is the ALSA hardware number for your pi. 0 is the first sound card and should work for most bots.
   - `type` should be the type of TTS software you are using. The currently supported TTS types are. espeak was installed in the previous steps, and makes a good default tts.
     - `espeak`
     - `fesitval`
     - `pico`
     - Amazon Polly (`polly`)
     - `cozmo_tts`
     - `google_cloud`

## Setting up your start_robot file on the Raspberry Pi

1. Copy the `start_robot` script to your home directory.

   ```sh
   cp ~/remotv/scripts/start_robot ~
   ```

2. Add the startup script to the `crontab`

   ```sh
   crontab -e
   ```

   Note: If you accidently use the wrong editor try

   ```sh
   EDITOR=nano crontab -e
   ```

3. Insert the following text at the bottom

   ```sh
   @reboot /bin/bash /home/pi/start_robot
   ```

   Example:

   ```sh
   # Edit this file to introduce tasks to be run by cron.
   #
   # Each task to run has to be defined through a single line
   # indicating with different fields when the task will be run
   # and what command to run for the task
   #
   # To define the time you can provide concrete values for
   # minute (m), hour (h), day of month (dom), month (mon),
   # and day of week (dow) or use '*' in these fields (for 'any').#
   # Notice that tasks will be started based on the cron's system
   # daemon's notion of time and timezones.
   #
   # Output of the crontab jobs (including errors) is sent through
   # email to the user the crontab file belongs to (unless redirected).
   #
   # For example, you can run a backup of all your user accounts
   # at 5 a.m every week with:
   # 0 5 * * 1 tar -zcf /var/backups/home.tgz /home/
   #
   # For more information see the manual pages of crontab(5) and cron(8)
   #
   # m h  dom mon dow   command

   @reboot /bin/bash /home/pi/start_robot
   ```

4. Now just plug in the Camera and USB Speaker and reboot

   ```sh
   sudo reboot
   ```

# Hardware Compatibility

The following hardware is supported.

- Adafruit Motor Hat
- Adafruit PWM / Servo Hat
- Anki Cozmo
- Cytron MDD10 10 Amp Motor Driver
- GoPiGo 2
- GoPiGo 3
- L298N Dual Motor Controller
- Pololu Maestro Servo Controller (experimental)
- MAX7219 SPI Led Driver
- MotoZero 4 Motor Controller
- MQTT Publish commands to a local MQTT Broker
- OWI 535 Robotic Arm (USB controller)
- Serial Based controllers (Parallaxy or Arduinos)
- PiBorg ThunderBorg Motor Driver
- Pololu Dual MC33926 Motor Driver (experimental)
- Pololu DRV8835 Dual Motor Driver
- MegaPi by Makeblock

Missing something? You can add it, open source! Instructions for adding new hardware can be found [here.](https://docs.remo.tv/en/stable/controller/hardware/extending.html)

## Chat Commands

When `ext_chat` is enabled, the following chat commands are available. To use, just type them into the chat box on your bots page. These chat commands have no effect on how the site behaves, they only affect the bot. There are some functions that duplicate functions on the site. These changes are not saved and are lost on reboot.

- `.devmode X` Set dev mode. In dev mode, only the owner can drive. If demode is set to mods, your local mods can also drive [on|off|mods].
- `.anon control X` Sets if anonymous users can drive your bot [on|off].
- `.anon tts X` Sets if anonymous users messages are passed to TTS [on|of].
- `.anon X` Sets both anonymous control and tts access [on|off].
- `.tts X` Mute the bots TTS [mute|unmute]
- `.ban NAME` Ban user NAME from controlling your bots
- `.unban NAME` remove user NAME from the ban list
- `.timeout NAME` Timeout user NAME from controlling your bots for 5 minutes
- `.untimeout NAME` remove user NAME from the timeout list.
- `.brightness X` set the camera brightness [0..255]
- `.contrast X` set the camera contrast [0..255]
- `.saturation X` set the camera saturation [0..255]
- `.stationary` Toggles stationary mode on and off. When enabled, forward / backward commands will be blocked.

Hardware modules can have their own hardware specific TTS commands.

# Instructions for Specific Hardware Configurations

## Cozmo

For Anki Cozmo on Mac or Linux, please see the intructions [here](https://docs.remo.tv/en/stable/controller/hardware/cozmo.html).
For Windows instructions, please see the instructions [here](https://docs.remo.tv/en/stable/controller/hardware/cozmo-win.html).

## GoPiGo3

For GoPiGo3, you will need to install the gopigo3 python module (which is different than older versions). It will need to be installed with the installation script from Dexter. Also, `PYTHONPATH` needs to be set to `/home/pi/Dexter/GoPiGo3/Software/Python`

Refer to this:
https://github.com/DexterInd/GoPiGo3

```sh
sudo git clone http://www.github.com/DexterInd/GoPiGo3.git /home/pi/Dexter/GoPiGo3
sudo bash /home/pi/Dexter/GoPiGo3/Install/install.sh
sudo reboot
```

## Adafruit Motor Hat

Install [motor HAT software](https://learn.adafruit.com/adafruit-dc-and-stepper-motor-hat-for-raspberry-pi/installing-software):

## Adafruit PWM / Servo Hat

Install [PWM / Servo hat software](https://learn.adafruit.com/adafruit-16-channel-pwm-servo-hat-for-raspberry-pi/using-the-python-library)

## Pololu Maestro Servo Controller

Install [Maestro Servon controller library](https://github.com/FRC4564/Maestro) into the hardware/ subdirectory.

## Pololu DRV8835 Motor Driver

Install [DRV8835 Motor Driver library](https://github.com/pololu/drv8835-motor-driver-rpi)

## Pololu MC33926 Motor Driver

Install [MC33926 Motor Driver library](https://github.com/pololu/dual-mc33926-motor-driver-rpi)

# Check out the [Wiki](https://docs.remo.tv) for more information

# A note about the Raspi Cam Module

Sometimes enabling the Raspberry Pi Camera module in `raspi-config` doesn't completely load the kernel drivers for it. If you don't see `/dev/video0` on your system, or `controller.py` complains about not finding it, then do the following:

1. Enable the kernel module for your current session:

```sh
sudo modprobe bcm2835-v4l2
```

2. Tell the operating system to load the kernel module at boot going forward:

```sh
sudo cat 'bcm2835-v4l2' >> /etc/modules
```

Now you should see `video0` if you do `ls /dev/ | grep video`
