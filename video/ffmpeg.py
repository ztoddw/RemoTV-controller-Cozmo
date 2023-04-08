#   TODO :  Look at making it so the ffmpeg process toggles a boolean, that is 
# used to update the server with online state appropriately. 
from video.ffmpeg_process import *

import audio_util
import networking, watchdog, subprocess, shlex

import schedule, extended_command
import atexit, os, sys, logging

log = logging.getLogger('RemoTV.video.ffmpeg')

import robot_util, time, signal

robotKey=None
server=None
no_mic=True
no_camera=True
print ('1:set mic_off=False')
mic_off=False

        # tw 3/10/23 using lists now. (4 video options in the config file now) initialize the lists:
video_input_formats, video_input_options, video_output_options, video_devices, x_res_list, y_res_list = \
    ([None] * 20, [None] * 20, [None] * 20, [None] * 20, [None] * 20, [None] * 20)

#x_res_list[0], y_res_list[0] = (320, 240)
#x_res_list[1], y_res_list[1] = (320, 240)
#x_res_list[2], y_res_list[2] = (1280, 720)
#x_res_list[3], y_res_list[3] = (1280, 720)


ffmpeg_location = None
v4l2_ctl_location = None

audio_hw_num = None
audio_device = None
audio_codec = None
audio_channels = None
audio_bitrate = None
video_framerate = 25
audio_sample_rate = None
video_codec = None
video_bitrate = None
video_filter = ''

audio_input_format = None
audio_input_options = None
audio_output_options = None

video_start_count = 0

brightness=None
contrast=None
saturation=None

old_mic_vol = 50
mic_vol = 50

def setup(robot_config):
    global robotKey, no_mic, mic_off, no_camera
    global stream_key, server
    global x_res_list, y_res_list, x_res, y_res

    global ffmpeg_location, v4l2_ctl_location

    global audio_hw_num, audio_device, audio_codec, audio_channels, audio_bitrate
    global audio_sample_rate, video_codec, video_bitrate, video_framerate, video_filter
    global video_devices, audio_input_format, audio_input_options
    
    global audio_output_options, video_input_formats, \
        video_input_options, video_output_options, chosen_video_option

    global brightness, contrast, saturation

    robotKey = robot_config.get('robot', 'robot_key')

    if robot_config.has_option('misc', 'video_server'):
        server = robot_config.get('misc', 'video_server')
    else:
        server = robot_config.get('misc', 'server')
 
    no_mic = robot_config.getboolean('camera', 'no_mic')
    mic_off = robot_config.getboolean('camera', 'mic_off')
    no_camera = robot_config.getboolean('camera', 'no_camera')

    ffmpeg_location = robot_config.get('ffmpeg', 'ffmpeg_location')
    v4l2_ctl_location = robot_config.get('ffmpeg', 'v4l2-ctl_location')

    if not no_camera:
        if robot_config.has_option('camera', 'brightness'):
            brightness = robot_config.get('camera', 'brightness')
        if robot_config.has_option('camera', 'contrast'):
            contrast = robot_config.get('camera', 'contrast')
        if robot_config.has_option('camera', 'saturation'):
            saturation = robot_config.get('camera', 'saturation')
       
        video_codec = robot_config.get('ffmpeg', 'video_codec')
        video_bitrate = robot_config.get('ffmpeg', 'video_bitrate')        
        if robot_config.has_option('ffmpeg', 'video_framerate'):
            video_framerate = robot_config.get('ffmpeg', 'video_framerate')
        
        for i in range(20) :             #tw 3/14/23- added this- multiple (up to 20) video options in the config file now.
            if robot_config.has_option('camera', 'camera_device{}'.format(i+1)) :
                video_devices[i] = robot_config.get('camera', 'camera_device{}'.format(i+1))
                video_input_formats[i] = robot_config.get('ffmpeg', 'video_input_format{}'.format(i+1))
                video_input_options[i] = robot_config.get('ffmpeg', 'video_input_options{}'.format(i+1))
                video_output_options[i] = robot_config.get('ffmpeg', 'video_output_options{}'.format(i+1))
                x_res_list[i] = robot_config.getint('camera', 'x_res{}'.format(i+1))
                y_res_list[i] = robot_config.getint('camera', 'y_res{}'.format(i+1))

        chosen_video_option = int(robot_config.get('ffmpeg', 'StartingVideoOption')) - 1
        print (chosen_video_option, x_res_list)
        
        x_res = x_res_list[chosen_video_option]
        y_res = y_res_list[chosen_video_option]
        print ("x_res, y_res = ", x_res, y_res)

        if robot_config.has_option('ffmpeg', 'video_filter'):
            video_filter = robot_config.get('ffmpeg', 'video_filter')
            video_filter = '-vf %s' % video_filter

        if robot_config.getboolean('tts', 'ext_chat'):
            extended_command.add_command('.video', videoChatHandler)
            extended_command.add_command('.brightness', brightnessChatHandler)
            extended_command.add_command('.contrast', contrastChatHandler)
            extended_command.add_command('.saturation', saturationChatHandler)
        
    if not no_mic:
        if robot_config.has_option('camera', 'mic_num'):
            audio_hw_num = robot_config.get('camera', 'mic_num')
        else:
            log.warn("controller.conf is out of date. Consider updating.")
            audio_hw_num = robot_config.get('camera', 'audio_hw_num')
        
        if robot_config.has_option('camera', 'mic_device'):
            audio_device = robot_config.get('camera', 'mic_device')
        else:
            audio_device = robot_config.get('camera', 'audio_device')

        audio_codec = robot_config.get('ffmpeg', 'audio_codec')
        audio_bitrate = robot_config.get('ffmpeg', 'audio_bitrate')        
        audio_sample_rate = robot_config.get('ffmpeg', 'audio_sample_rate')
        audio_channels = robot_config.get('ffmpeg', 'audio_channels')
        audio_input_format = robot_config.get('ffmpeg', 'audio_input_format')
        audio_input_options = robot_config.get('ffmpeg', 'audio_input_options')
        audio_output_options = robot_config.get('ffmpeg', 'audio_output_options')

        if robot_config.getboolean('tts', 'ext_chat'):
            print('Adding audio chat handler')
            extended_command.add_command('.audio', audioChatHandler)
            if audio_input_format == "alsa":
                extended_command.add_command('.mic', micHandler)

        # resolve device name to hw num, only with alsa
        if audio_input_format == "alsa":
            if audio_device != '':
                temp_hw_num = audio_util.getMicByName(audio_device.encode('utf-8'))
                if temp_hw_num != None:
                    audio_hw_num = temp_hw_num       

        # format the device for hw number if using alsa
        if audio_input_format == 'alsa':
            audio_device = 'hw:' + str(audio_hw_num)


def start():
    global no_mic   #tw 3/3/23 added
    global mic_off  #tw 3/3/23 added
    
    log.debug("start(): networking.internetStatus = %s", networking.internetStatus)
    if not no_camera:
        log.debug("start().2: networking.internetStatus = %s", networking.internetStatus)
        watchdog.start("FFmpegCameraProcess", startVideoCapture)
    
        #tw 3/26/23- let's just not turn on audio at first until someone sends a command. (see cozmo.py)
    #if not no_mic and not mic_off:
    #    watchdog.start("FFmpegAudioProcess", startAudioCapture)


# startFFMPEG starts the ffmpeg command string passed in command, and stores procces in the global
# variable named after the string passed in process. It registers an atexit function pass in atExit
# and uses the string passed in name as part of the error messages.

def startFFMPEG(command, name, atExit, process):
    try:
        if sys.platform.startswith('linux') or sys.platform == "darwin":
            ffmpeg_process=subprocess.Popen(command, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        else: 
            ffmpeg_process=subprocess.Popen(command, stderr=subprocess.PIPE, shell=True)
        
        globals()[process] = ffmpeg_process
        
    except OSError: # Can't find / execute ffmpeg
        log.critical("ERROR: Can't find / execute ffmpeg, check path in conf")
        robot_util.terminate_controller()
        return()

    if ffmpeg_process != None:
        try:
            atexit.unregister(atExit) # Only python 3
        except AttributeError:
            pass
        atexit.register(atExit)
        ffmpeg_process.wait()

        if ffmpeg_process.returncode > 0:
            log.debug("ffmpeg exited abnormally with code {}".format(ffmpeg_process.returncode))
            error = ffmpeg_process.communicate()
            log.debug("ffmpeg {} error message : {}".format(name, error))
            try:
                log.error("ffmpeg {} : {}".format(name, error[1].decode().split('] ')[1:]))
            except IndexError:
                pass
        else:
            log.debug("ffmpeg exited normally with code {}".format(ffmpeg_process.returncode))

        atexit.unregister(atExit)


def stopFFMPEG(ffmpeg_process):
    try:
        if sys.platform.startswith('linux') or sys.platform == "darwin":
            os.killpg(os.getpgid(ffmpeg_process.pid), signal.SIGTERM)
        else:
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(ffmpeg_process.pid)])

    except OSError: # process is already terminated
        pass


def startVideoCapture():
    global video_process
    global video_start_count
    global x_res_list, y_res_list, chosen_video_option

    while not networking.authenticated:
        time.sleep(1)

    video_start_count += 1
    log.debug("Video start count : %s", video_start_count)

#    if video_start_count % 10 == 0:
#    server refresh

    # set brightness
    if (brightness is not None):
        v4l2SetCtrl("brightness", brightness)

    # set contrast
    if (contrast is not None):
        v4l2SetCtrl("contrast", contrast)

    # set saturation
    if (saturation is not None):
        v4l2SetCtrl("saturation", saturation)

    log.debug("networking.internetStatus = %s", networking.internetStatus)
    
    if networking.internetStatus:
    
            # tw 3/9/23: for my IP cam, I gotta take out -f and -framerate and -video_size.
       videoCommandLine = '{ffmpeg}'
       
       chosenVideo = video_input_formats[chosen_video_option]
       
       if chosenVideo != "":
           videoCommandLine += ' -f {input_format}'
           
       if chosenVideo not in ("", "lavfi") :
           videoCommandLine += ' -framerate {framerate}'
       
       if chosenVideo not in ("lavfi","mjpeg",""):
           videoCommandLine += ' -video_size {xres}x{yres}'

       videoCommandLine += (' -r {framerate} {in_options} -i {video_device} {video_filter}'
                        ' -f mpegts -codec:v {video_codec} -b:v {video_bitrate}k -bf 0'
                        ' -muxdelay 0.001 {out_options}'
                        ' -headers "Authorization: Bearer {robotKey}"'
                        ' http://{server}/transmit?name={channel}-video')
                        
       videoCommandLine = videoCommandLine.format(ffmpeg=ffmpeg_location,
                            input_format=chosenVideo,
                            framerate=video_framerate,
                            in_options=video_input_options[chosen_video_option],
                            video_device=video_devices[chosen_video_option], 
                            video_filter=video_filter,
                            video_codec=video_codec,
                            video_bitrate=video_bitrate,
                            out_options=video_output_options[chosen_video_option],
                            server=server,
                            channel=networking.channel_id,
                            xres=x_res_list[chosen_video_option], 
                            yres=y_res_list[chosen_video_option],
                            robotKey=robotKey)

       log.info("videoCommandLine : %s", videoCommandLine)
       startFFMPEG(videoCommandLine, 'Video',  atExitVideoCapture, 'video_process')

    else:
       log.debug("No Internet/Server : sleeping video start for 15 seconds")
       time.sleep(15)


def atExitVideoCapture():
    global video_process
    stopFFMPEG(video_process)
    video_process = None


def stopVideoCapture():
    global video_process
    if video_process != None:
        watchdog.stop('FFmpegCameraProcess')
        stopFFMPEG(video_process)
        video_process = None

 
def restartVideoCapture(): 
    stopVideoCapture()
    log.debug("restartVideoCapture: networking.internetStatus = %s", networking.internetStatus)
    watchdog.start("FFmpegCameraProcess", startVideoCapture)


def startAudioCapture():
    global audio_process

    while not networking.authenticated:
        time.sleep(1)

    audioCommandLine = '{ffmpeg} -f {audio_input_format}'
    if audio_input_format != "avfoundation":
        audioCommandLine += ' -ar {audio_sample_rate} -ac {audio_channels}'
    audioCommandLine += (' {in_options} -i {audio_device} -f mpegts'
                         ' -codec:a {audio_codec}  -b:a {audio_bitrate}k'
                         ' -muxdelay 0.001 {out_options}'
                         ' -headers "Authorization: Bearer {robotKey}"'
                         ' http://{server}/transmit?name={channel}-audio')

    audioCommandLine = audioCommandLine.format(ffmpeg=ffmpeg_location,
                            audio_input_format=audio_input_format,
                            audio_sample_rate=audio_sample_rate,
                            audio_channels=audio_channels,
                            in_options=audio_input_options,
                            audio_device=audio_device,
                            audio_codec=audio_codec,
                            audio_bitrate=audio_bitrate,
                            out_options=audio_output_options,
                            server=server,
                            channel=networking.channel_id,
                            robotKey=robotKey)
                            
    log.info("audioCommandLine : %s", audioCommandLine)
    startFFMPEG(audioCommandLine, 'Audio',  atExitAudioCapture, 'audio_process')

    
def atExitAudioCapture():
    global audio_process
    stopFFMPEG(audio_process)
    audio_process = None


def stopAudioCapture():
    global audio_process
    if audio_process != None:
        watchdog.stop('FFmpegAudioProcess')
        stopFFMPEG(audio_process)
        audio_process = None


def restartAudioCapture():
    global mic_off
    stopAudioCapture()
    
    if not mic_off:
        watchdog.start("FFmpegAudioProcess", startAudioCapture)


def videoChatHandler(command, args):
    global video_process, video_bitrate
    global chosen_video_option, video_devices, x_res_list, y_res_list, \
      video_input_formats, video_output_options, x_res, y_res

    if len(command) > 1:
        if True:  #extended_command.is_authed(args['sender']) == 2: # Owner  #3/25/23 make available to all
            if 'start' in command[1]:       #tw 3/4/23- added this - for start or restart
                if len(command) > 2 and command[2].isdigit() :      #tw 3/10/23- added this
                    chosen_video_option = int(command[2])
                    x_res = x_res_list[chosen_video_option]
                    y_res = y_res_list[chosen_video_option]

                    
            if command[1] == 'start':
                print("in .video start)")
                if video_process: print("video_process.returncode = " + str(video_process.returncode))
                if not video_process or not video_process.returncode == None:
                    log.debug("videoChatHandler: networking.internetStatus = %s", networking.internetStatus)
                    watchdog.start("FFmpegCameraProcess", startVideoCapture)
                    

            elif command[1] == 'stop':
                stopVideoCapture()
                
            elif command[1] == 'restart':
                restartVideoCapture()

            elif command[1] == 'bitrate':
                if len(command) > 1:
                    if len(command) == 3:
                        try:
                            int(command[2])
                            video_bitrate = command[2]
                            restartVideoCapture()
                        except ValueError: # Catch someone passing not a number
                            pass
                    networking.sendChatMessage(".Video bitrate is %s" % video_bitrate)

            elif command[1] == 'framerate':             # tw- 3/3/23 added framerate subcommand
                if len(command) > 1:
                    if len(command) == 3:
                        try:
                            int(command[2])
                            video_framerate = command[2]
                            restartVideoCapture()
                        except ValueError: # Catch someone passing not a number
                            pass
                    networking.sendChatMessage(".Video framerate is %s" % video_framerate)
        else:
            networking.sendChatMessge("command only available to owner")


def v4l2SetCtrl(control, level):
    command = "{v4l2_ctl} -d {device} -c {control}={level}".format(
            v4l2_ctl=v4l2_ctl_location,
            device=video_device,
            control=control,
            level=str(level)
    )
    os.system(command)
    log.info("{control} set to {level}".format(control=contrl, level=level))


def brightnessChatHandler(command, args):
    global brightness
    if len(command) > 1:
        if extended_command.is_authed(args['sender']): # Moderator
            try:
                new_brightness = int(command[1])
            except ValueError:
                exit() #Not a number    
            if new_brightness <= 255 and new_brightness >= 0:
                brightness = new_brightness
                v4l2SetCtrl("brightness", brightness)


def contrastChatHandler(command, args):
    global contrast
    if len(command) > 1:
        if extended_command.is_authed(args['sender']): # Moderator
            try:
                new_contrast = int(command[1])
            except ValueError:
                exit() #not a number
            if new_contrast <= 255 and new_contrast >= 0:
                contrast = new_contrast
                v4l2SetCtrl("contrast", contrast)


def saturationChatHandler(command, args):
    if len(command) > 2:
        if extended_command.is_authed(args['sender']): # Moderator
            try:
                new_saturation = int(command[1])
            except ValueError:
                exit() #not a number
            if new_saturation <= 255 and new_saturation >= 0:
                saturation = new_saturation
                v4l2SetCtrl("saturation", saturation)


def audioChatHandler(command, args):
    global audio_process
    global audio_bitrate
    global mic_off

    if len(command) > 1:
        if extended_command.is_authed(args['sender']) == 2: # Owner
            if command[1] == 'start':
                print ('3:set mic_off=False')
                mic_off = False        # tw 2/24/23 re-enabled
                print('in chat handler, starting audio')
                if True: #audio_process.returncode != None:       # tw 3/3/23- took out conditional, not sure why here
                    watchdog.start("FFmpegAudioProcess", startAudioCapture)
            elif command[1] == 'stop':
                print ('4:set mic_off=True')
                mic_off = True         # tw 2/24/23 added
                stopAudioCapture()
            elif command[1] == 'restart':
                stopAudioCapture()
                print ('5:set mic_off=False')
                mic_off = False        # tw 2/24/23 re-enabled
                watchdog.start("FFmpegAudioProcess", startAudioCapture)
                
            elif command[1] == 'bitrate':
                if len(command) > 1:
                    if len(command) == 3:
                        try:
                            int(command[2])
                            audio_bitrate = command[2]
                            restartAudioCapture()
                        except ValueError: # Catch someone passing not a number
                            pass
                    networking.sendChatMessage(".Audio bitrate is %s" % audio_bitrate)


# Handles setting the mic volume level.
def micHandler(command, args):
    global old_mic_vol
    global mic_vol

    if extended_command.is_authed(args['sender']) == 2: # Owner
        if len(command) > 1:
            if command[1] == 'mute':
                networking.sendChatMessage(".Warning: Mute may not actually mute mic, use .audio stop to ensure mute")
                # Mic Mute
                old_mic_vol = mic_vol
                mic_vol = 0
            elif command[1] == 'unmute':
                # Mic Unmute
                mic_vol = old_mic_vol
            elif command[1] == 'vol':
                try:
                    new_vol = int(command[2])
                except ValueError:
                    log.debug("Not a valid volume level %s" % command[2])

                mic_vol = new_vol % 101

            log.info("Setting volume to %d" % mic_vol)
            os.system("amixer -c {} sset 'Mic' '{}%'".format(audio_hw_num, mic_vol))
            networking.sendChatMessage(".mic volume is %s" % mic_vol)

