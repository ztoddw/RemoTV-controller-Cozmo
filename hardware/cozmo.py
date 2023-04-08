
import mod_utils
import time
import _thread as thread
import cozmo
from cozmo.util import degrees, distance_mm, speed_mmps
from cozmo.objects import LightCube1Id, LightCube2Id, LightCube3Id

import tts.tts as tts
import extended_command
import networking
import sys
import os
import schedule
#import extended_command    #imported twice?

#import PIL
from PIL import Image, ImageDraw, ImageFont

canvasFile = "blankCanvas.png"

from shutil import copyfile

import sqlite3 as sl
import math
import random
import urllib.request as urllib2


coz = None
is_headlight_on = False
forward_speed = 75
turn_speed = 50
volume = 100
charging = 0
charge_low = 3.5
charge_high = 4.5

lastBatteryLevelReached = 2    # 1=low, 2=high
lastDockStatus = 1             # 1=docked, 2=roaming

stay_on_dock = 0
robotKey = None

default_anims_for_keys = ["anim_bored_01",  # 0 drat
                          "anim_poked_giggle",  # 1 giggle
                          "anim_pounce_success_02",  # 2 wow
                          "anim_bored_event_02",  # 3 tick tock
                          "anim_bored_event_03",  # 4 pong face
                          "anim_petdetection_cat_01",  # 5 surprised meow
                          "anim_petdetection_dog_03",  # 6 dog reaction
                          "anim_reacttoface_unidentified_02",  # 7 look up
                          "anim_upgrade_reaction_lift_01",  # 8 excited
                          "anim_speedtap_wingame_intensity02_02"  # 9 back up quick
                         ]  


def play_anim(command, args):
    if len(command) > 1:
        try:
            coz.play_anim(command[1]).wait_for_completed()
        except ValueError:
            try:
                coz.play_anim_trigger( getattr(cozmo.anim.Triggers, command[1]) ).wait_for_completed()
            except:           
                pass
        except:
            pass


anims = []
nextAnim = 0

def showAnims():
    global anims
    global nextAnim 
    s = ""
    nextAnim = 0
    allAnims = dir(cozmo.anim.Triggers)
    for i in range(10):
        while True:
            j = random.randrange(len(allAnims))
            if allAnims[j][0] != '_': break
        anims.append( allAnims[j] )
        s += " -- " + str(i) + ":" + anims[i]
    
    networking.sendChatMessage('-- Here are some random animations: ---------------- ' + s \
        + ' ---------------- -- You_can_use_"n"_button/hotkey,_or_".a"_command_in_chat- example: ".a 3" to play #3 animation')


def playAnimListNum(command, args):
    global anims
    if len(anims) == 0:
        return False

    if len(command) > 1 and command[1].isdigit():
        try:
            vAnim = anims[int(command[1])]
            coz.play_anim_trigger( getattr(cozmo.anim.Triggers, vAnim) ).wait_for_completed()
            networking.sendChatMessage("Played: " + vAnim)
        except:           
            pass


def playAnimListNext():
    global nextAnim 
    global anims
    if len(anims) == 0:
        return False
        
    if nextAnim == 10:
        nextAnim = 0
    vAnim = anims[nextAnim]
    nextAnim += 1
    try:
        coz.play_anim_trigger( getattr(cozmo.anim.Triggers, vAnim) ).wait_for_completed()
        networking.sendChatMessage("Played: " + str(nextAnim-1) + ": " + vAnim)
    except:           
        pass
        

jokes = [[1, "My wife told me to stop impersonating a flamingo. I had to put my foot down."]
, [2, "I went to buy some camo pants but couldn't find any."]
, [3, "I failed math so many times at school, I can't even count."]
, [4, "I used to have a handle on life, but then it broke."]
, [5, "I was wondering why the frisbee kept getting bigger and bigger, but then it hit me."]
, [6, "I heard there were a bunch of break-ins over at the car park. That is wrong on so many levels."]
, [7, "I want to die peacefully in my sleep, like my grandfather. Not screaming and yelling like the passengers in his car."]
, [8, "When life gives you melons, you might be dyslexic."]
, [9, "Don't you hate it when someone answers their own questions? I do."]
, [10, "It takes a lot of balls to golf the way I do."]
, [11, "I told him to be himself; that was pretty mean, I guess."]
, [12, "I know they say that money talks, but all mine says is 'Goodbye.'"]
, [13, "My father has schizophrenia, but he's good people."]
, [14, "The problem with kleptomaniacs is that they always take things literally."]
, [15, "I can't believe I got fired from the calendar factory. All I did was take a day off."]
, [16, "Most people are shocked when they find out how bad I am as an electrician."]
, [17, "Never trust atoms; they make up everything."]
, [18, "My wife just found out I replaced our bed with a trampoline. She hit the ceiling!"]
, [19, "I was addicted to the hokey pokey, but then I turned myself around."]
, [20, "I used to think I was indecisive. But now I'm not so sure."]
, [21, "Russian dolls are so full of themselves."]
, [22, "The easiest time to add insult to injury is when you're signing someone's cast."]
, [23, "Light travels faster than sound, which is the reason that some people appear bright before you hear them speak."]
, [24, "My therapist says I have a preoccupation for revenge. We'll see about that."]
, [25, "A termite walks into the bar and asks, 'Is the bar tender here?'"]
, [26, "A told my girlfriend she drew her eyebrows too high. She seemed surprised."]
, [27, "People who use selfie sticks really need to have a good, long look at themselves."]
, [28, "Two fish are in a tank. One says, 'How do you drive this thing?'"]
, [29, "I always take life with a grain of salt. And a slice of lemon. And a shot of tequila."]
, [30, "Just burned 2,000 calories. That's the last time I leave brownies in the oven while I nap."]
, [31, "Always borrow money from a pessimist. They'll never expect it back."]
, [32, "Build a man a fire and he'll be warm for a day. Set a man on fire and he'll be warm for the rest of his life."]
, [33, "I don't suffer from insanity-I enjoy every minute of it."]
, [34, "The last thing I want to do is hurt you; but it's still on the list."]
, [35, "The problem isn't that obesity runs in your family. It's that no one runs in your family."]
, [36, "Today a man knocked on my door and asked for a small donation toward the local swimming pool. I gave him a glass of water."]
, [37, "I'm reading a book about anti-gravity. It's impossible to put down."]
, [38, "'Doctor, there's a patient on line one that says he's invisible.''Well, tell him I can't see him right now.'"]
, [39, "Atheism is a non-prophet organization."]
, [40, "A recent study has found that women who carry a little extra weight live longer than the men who mention it."]
, [41, "The future, the present, and the past walk into a bar. Things got a little tense."]
, [42, "Before you criticize someone, walk a mile in their shoes. That way, when you do criticize them, you're a mile away and you have their shoes."]
, [43, "Last night my girlfriend was complaining that I never listen to her. or something like that."]
, [44, "Maybe if we start telling people their brain is an app, they'll want to use it."]
, [45, "If a parsley farmer gets sued, can they garnish his wages?"]
, [46, "I got a new pair of gloves today, but they're both 'lefts,' which on the one hand is great, but on the other, it's just not right."]
, [47, "I didn't think orthopedic shoes would help, but I stand corrected."]
, [48, "I was riding a donkey the other day when someone threw a rock at me and I fell off. I guess I was stoned off my ass."]
, [49, "People who take care of chickens are literally chicken tenders."]
, [50, "It was an emotional wedding. Even the cake was in tiers."]
, [51, "I just got kicked out of a secret cooking society. I spilled the beans."]
, [52, "What's a frog's favorite type of shoes? Open toad sandals."]
, [53, "Blunt pencils are really pointless."]
, [54, "6:30 is the best time on a clock, hands down."]
, [55, "Two wifi engineers got married. The reception was fantastic."]
, [56, "Just got fired from my job as a set designer. I left without making a scene."]
, [57, "What's the difference between ignorance and apathy? I don't know and I don't care."]
, [58, "One of the cows didn't produce milk today. It was an udder failure."]
, [59, "Adam & Eve were the first ones to ignore the Apple terms and conditions."]
, [60, "Refusing to go to the gym is a form of resistance training."]
, [61, "If attacked by a mob of clowns, go for the juggler."]
, [62, "The man who invented Velcro has died. RIP."]
, [63, "Despite the high cost of living, it remains popular."]
, [64, "A dung beetle walks into a bar and asks, 'Is this stool taken?'"]
, [65, "I can tell when people are being judgmental just by looking at them."]
, [66, "The rotation of Earth really makes my day."]
, [67, "Well, to be Frank with you, I'd have to change my name."]
, [68, "My friend was explaining electricity to me, but I was like, 'Watt?'"]
, [69, "What if there were no hypothetical questions?"]
, [70, "Are people born with photographic memories, or does it take time to develop?"]
, [71, "The world champion tongue twister got arrested. I hear they're going to give him a tough sentence."]
, [72, "Pollen is what happens when flowers can't keep it in their plants."]
, [73, "A book fell on my head the other day. I only have my shelf to blame though."]
, [74, "Communist jokes aren't funny unless everyone gets them."]
, [75, "Geology rocks, but geography's where it's at."]
, [76, "I buy all my guns from a guy called T-Rex. He's a small arms dealer."]
, [77, "My friend's bakery burned down last night. Now his business is toast."]
, [78, "Four fonts walk into a bar. The bartender says, 'Hey! We don't want your type in here!'"]
, [79, "If you don't pay your exorcist, do you get repossessed?"]
, [80, "When the cannibal showed up late to the buffet, they gave him the cold shoulder."]
, [81, "A Mexican magician tells the audience he will disappear on the count of three. He says, 'Uno, dos.' and poof! He disappeared without a tres."]
, [82, "Fighting for peace is like screwing for virginity."]
, [83, "A ghost walked into a bar and ordered a shot of vodka. The bartender said, 'Sorry, we don't serve spirits here.'"]
, [84, "The man who invented knock-knock jokes should get a no bell prize."]
, [85, "I bought the world's worst thesaurus yesterday. Not only is it terrible, it's also terrible."]
, [86, "A blind man walked into a bar. and a table. and a chair."]
, [87, "A Freudian slip is when you say one thing and mean your mother."]
, [88, "I went to a seafood disco last week, but ended up pulling a mussel."]
, [89, "The first time I got a universal remote control, I thought to myself, 'This changes everything.'"]
, [90, "How do you make holy water? You boil the hell out of it."]
, [91, "I saw a sign the other day that said, 'Watch for children,' and I thought, 'That sounds like a fair trade.'"]
, [92, "Whiteboards are remarkable."]
, [93, "I threw a boomerang a couple years ago; I know live in constant fear."]
, [94, "I put my grandma on speed dial the other day. I call it insta-gram."]
, [95, "I have a few jokes about unemployed people, but none of them work."]
, [96, "'I have a split personality,' said Tom, being Frank."]
, [97, "My teachers told me I'd never amount to much because I procrastinate so much. I told them, 'Just you wait!'"]
, [98, "Will glass coffins be a success? Remains to be seen."]
, [99, "Did you hear about the guy whose whole left side got amputated? He's all right now."]
, [100, "The man who survived both mustard gas and pepper spray is a seasoned veteran now."]
, [101, "Have you heard about the new restaurant called 'Karma?' There's no menu-you get what you deserve."]]


    # I'm assuming there are no quote characters in any jokes. use apostrophe (single quote) instead.
    #  hmm, instead of inserting all of them upfront and updating with the duration,
    #  I think I'll just insert them as they are used. Not worrying about duplicates.
    #   hmm, I think I'll just use jokeID in the table instead of the whole text.
    #   I'll create a table upfront of the JokeIDs and texts, to make it easier to query for 
    #   next unused joke (or not used as much as others). Let's just overwrite this whole table every time.

def pickNextJoke(conn) :
    global jokeNum

    # Now to pick next random joke among the least used jokes :

        # First group them to count how many uses per jokeID
    if conn.execute("SELECT name FROM sqlite_master WHERE name='jokesGrouped'").fetchone() is None:
        conn.execute('create table jokesGrouped (jokeID int, numTimesUsed int)')  # STRICT')
    
    conn.execute('delete from jokesGrouped') 

    conn.execute("""insert into jokesGrouped (jokeID, numTimesUsed)
        SELECT a.jokeID, count(b.jokeID) as numTimesUsed
        FROM jokes a left join jokeDurations b on b.jokeID = a.jokeID
      group by a.jokeID""").fetchone()
    
        # Then see what is the least # of times any joke has been used
    leastTimesUsed = conn.execute("SELECT min(numTimesUsed) from jokesGrouped").fetchone()
    
        # then grab all the jokes that have been used that many times
    jokesLeastUsed = conn.execute("SELECT jokeID from jokesGrouped where numTimesUsed=?", leastTimesUsed).fetchall()

        # and pick one at random  :)
    jokeNum = jokesLeastUsed[random.randrange(len(jokesLeastUsed))][0]



# To run in the beginning:

conn = sl.connect('CozData.db')

conn.execute("drop table jokes")    
conn.execute('create table jokes (jokeID int, jokeText text)')  # STRICT')
    # the strict keyword is available in SQLLite vers 3.37.0

conn.executemany("insert into jokes (jokeID, jokeText) values (?, ?)", jokes)

pickNextJoke(conn)

conn.commit()
conn.close()


def TellJoke():
    global jokeNum
    global coz, cozCamOn
    savecozCamOn = cozCamOn 
    if cozCamOn :
        toggleCozCam(['.cam'], None)
    
    thisJoke = jokes[jokeNum - 1][1]
    jokeWords = thisJoke.split()
    print (thisJoke, len(jokeWords))
    
    checkAudioStart()
    jokeStart = time.time()
    act = coz.say_text(thisJoke)   # starts the say_text action
    jokeStart2 = time.time()       # check if there's still any delay, even to this point
    jokeEnd = 0
    
    for i in range(int((len(jokeWords) - 1) / 5) + 1) :
        s, sp = "", ""
        p = i * 5
        for j in range(p, min(p + 5, len(jokeWords))) :
            s += sp + jokeWords[j]
            sp = " "
        
        canv = Image.open(canvasFile)
        drawText(canv, s)
        canv.save("overlay.png")
        canv.close()
        for i in range(30) :
            time.sleep(0.1)
            if act.is_completed: 
                if jokeEnd == 0: jokeEnd = time.time()
                if i > 9: break
        
    act.wait_for_completed()
    if jokeEnd == 0: jokeEnd = time.time()
    
    clearScreen(None, None)

    conn = sl.connect('CozData.db')

    if conn.execute("SELECT name FROM sqlite_master WHERE name='jokeDurations'").fetchone() is None:
        conn.execute('create table jokeDurations (jokeID int, initDur real, dur real, numWords int)')  # STRICT')
            # the strict keyword is available in SQLLite vers 3.37.0

    conn.execute("""insert into jokeDurations (jokeID, initDur, dur, numWords) 
        values (?, ?, ?, ?)""", (jokeNum, jokeStart2 - jokeStart, jokeEnd - jokeStart2, len(jokeWords)))

    pickNextJoke(conn)
    
    conn.commit()
    conn.close()
    cozCamOn = savecozCamOn 


def drawText(canv, s, sz = 50) :
    draw = ImageDraw.Draw(canv)
    sz = int(sz / 1280 * video_module.x_res)    
    fnt = ImageFont.truetype("arial.ttf", sz)
    draw.text((int(video_module.x_res / 4), int(video_module.y_res * 0.7)), s, font=fnt, fill=(0,0,0,255))
    print('drawing text: '+s)


def set_forward_speed(command, args):
    global forward_speed
    if extended_command.is_authed(args['sender']) == 2: # Owner
        if len(command) > 1:
            try:
                forward_speed=int(command[1])
                print("forward_speed set to : %d" % forward_speed)
            except ValueError:
                pass


def set_turn_speed(command, args):
    global turn_speed
    if extended_command.is_authed(args['sender']) == 2: # Owner
        if len(command) > 1:
            try:
                turn_speed=int(command[1])
                print("turn_speed set to : %d" % turn_speed)
            except ValueError:
                pass


def set_volume(command, args):
    global volume
    if extended_command.is_authed(args['sender']) == 2: # Owner
        if len(command) > 1:
            try:
                tmp=int(command[1])
                volume=(tmp % 101)
                coz.set_robot_volume(volume/100)
                print("volume set to : %d" % volume)
            except ValueError:
                pass


def set_charging(command, args):
    global charging
    global low_battery
    if extended_command.is_authed(args['sender']) == 2: # Owner
        if len(command) > 1:
            try: 
                if command[1] == "on":
                    low_battery = 1
                    if coz.is_on_charger:
                        charging = 1
                elif command[1] == "off":
                    low_battery = 0
                    charging = 0
                print("charging set to : %d" % charging)
#                networking.sendChargeState(charging)
            except ValueError:
                pass


def set_stay_on_dock(command, args):
    global stay_on_dock
    if extended_command.is_authed(args['sender']) == 2: # Owner
        if len(command) > 1:
            try: 
                if command[1] == "on":
                    stay_on_dock = 1
                elif command[1] == "off":
                    stay_on_dock = 0
                print("stay_on_dock set to : %d" % stay_on_dock)
            except ValueError:
                pass


def set_colour(command, args):
    global colour 
    if extended_command.is_authed(args['sender']) == 2:
        colour = not colour
        coz.camera.color_image_enabled = colour


def set_annotated(command, args):
    global annotated
    if extended_command.is_authed(args['sender']) == 2:
        annotated = not annotated
    vidLog("")
    vidLog("set annotated to {}".format(annotated))


def set_flipped(command, args):
    global flipped
    if extended_command.is_authed(args['sender']) == 2:
        flipped = not flipped


def setup(robot_config):
    global cozConfig
    cozConfig = robot_config
    global forward_speed, turn_speed, server, volume
    global charge_high, charge_low, stay_on_dock, annotated
    global colour, ffmpeg_location, robotKey
    
        #Used for calibration:
    global cozX1, cozY1, cozX2, cozY2
    global cozScreenX1, cozScreenX2, cozScreenY1, cozScreenY2

    robotKey = robot_config.get('robot', 'robot_key')

    ffmpeg_location = robot_config.get('ffmpeg', 'ffmpeg_location')

    if robot_config.has_option('misc', 'video_server'):
        server = robot_config.get('misc', 'video_server')
    else:
        server = robot_config.get('misc', 'server')

    if robot_config.has_section('cozmo'):
        forward_speed = configGet('int', 'forward_speed')
        turn_speed = configGet('int', 'turn_speed')
        volume = configGet('int', 'volume')
        charge_high = configGet('float', 'charge_high')
        charge_low = configGet('float', 'charge_low')
        stay_on_dock = configGet('bool', 'stay_on_dock')
        send_online_status = configGet('bool', 'send_online_status')
        annotated = configGet('bool', 'annotated')
        colour = configGet('bool', 'colour')
        coz.camera.color_image_enabled = colour
        
        cozX1, cozY1 = (configGet('int','cozX1'), configGet('int','cozY1'))
        cozX2, cozY2 = (configGet('int','cozX2'), configGet('int','cozY2'))
        cozScreenX1, cozScreenY1 = (configGet('int','cozScreenX1'), configGet('int','cozScreenY1'))
        cozScreenX2, cozScreenY2 = (configGet('int','cozScreenX2'), configGet('int','cozScreenY2'))

    else:
        send_online_status = True

    if robot_config.getboolean('tts', 'ext_chat'): #ext_chat enabled, add motor commands
        e = extended_command
        e.add_command('.anim', play_anim)
        #e.add_command('.getAnims', showAnims)
        e.add_command('.a', playAnimListNum)
        e.add_command('.forward_speed', set_forward_speed)
        e.add_command('.turn_speed', set_turn_speed)
        e.add_command('.vol', set_volume)
        e.add_command('.charge', set_charging)
        e.add_command('.stay', set_stay_on_dock)
        e.add_command('.annotate', set_annotated)
        e.add_command('.color', set_colour)
        e.add_command('.colour', set_colour)
        
        e.add_command('.cal', calibrate)
        e.add_command('.clear', clearScreen)
        e.add_command('.cam', toggleCozCam)
        

#    if send_online_status:
#        print("Enabling online status")
#        schedule.repeat_task(10, updateServer)

    coz.set_robot_volume(volume/100) # set volume


def configGet(type, param) :
    if type=='int':
        return cozConfig.getint('cozmo', param)
    if type=='bool':
        return cozConfig.getboolean('cozmo', param)
    if type=='float':
        return cozConfig.getfloat('cozmo', param)


cozCamX, cozCamY, cozCamOn = (1, 0, False)

def toggleCozCam(command, args) :
    #coz.camera.image_stream_enabled = True     #testing
    #return
    
    global cozCamX, cozCamY, cozW, cozH, cozCamOn \
        , canvasFile, doSnapShots, delayCam
    
    cmd = ""
    if len(command) > 1 : cmd = command[1] 
    
    if cmd == 'snap' :
        doSnapShots = True
        if len(command) > 2 :
            cmd = command[2]
            if cmd.count('.') <= 1 and cmd.replace('.','').isnumeric() and (cmd+'.').index('.') < 3 :
                #   All numbers except maybe 1 decimal point at most- and if there is a decimal 
                #   point, it must be 1st, 2nd, or 3rd character.
                #       To get here, it must be a positive number less than 100.
                delaySnap = float(cmd)
        return
    
        # abbreviations for: upper-left, upper-middle, upper-right,
        #   middle-left, full-screen, middle-right, lower-left, etc.
    
    if doSnapShots and len(command) == 1 :
        doSnapShots = False
        return
        
    doSnapShots = False
    cozW, cozH = (int(video_module.x_res * 0.3), int(video_module.y_res * 0.3))
    if len(command) > 2 and command[2] == 'big' :
        cozW, cozH = (int(video_module.x_res * 0.45), int(video_module.y_res * 0.45))
        
    places = {'ul':(0, 10), 'um':(video_module.x_res/2-cozW/2, 0), 'ur':(video_module.x_res-cozW, 0)
        , 'ml':(0, video_module.y_res/2-cozH/2), 'fs':(1, 0), 'mr':(video_module.x_res-cozW, video_module.y_res/2-cozH/2)
        , 'll':(0, video_module.y_res-cozH), 'lm':(video_module.x_res/2-cozW/2, video_module.y_res-cozH), 'lr':(video_module.x_res-cozW, video_module.y_res-cozH)}
        
    if cmd in places.keys() :
        cozCamX, cozCamY = places[command[1]]
        cozCamOn = True
    elif cmd == 'on':
        cozCamOn = True
    elif cmd == 'off':
        cozCamOn = False
    
    elif cmd.count('.') <= 1 \
    and cmd.replace('.','').isnumeric() and (cmd+'.').index('.') < 2 :
        #   To get here, it must be a positive number less than 10.
        delayCam = float(cmd)
    
    else :
        cozCamOn = not cozCamOn 

    if not cozCamOn :  
        time.sleep(0.2)     # wait for cozVid thread to finish if it's in the loop
        clearScreen(None, None)
        
    print("toggled- cozCamOn =", cozCamOn, ", delayCam =", delayCam)
    
    # 3/19/23- leaving the image stream enabled seems to make cozmo slow to respond to commands.
    #coz.camera.image_stream_enabled = cozCamOn
        # Now the cozVid function running an infinite loop in a separate thread will check the 
        #  cozCamOn and doSnapShots flags, and make use of cozCamX, cozCamY, delayCam, and delaySnap.
    

calState = 0
    #These come from / are stored in the config file now.
#cozX1, cozY1, cozX2, cozY2 = (0, 0, 0, 0)
#cozScreenX1, cozScreenY1 = (640, 360)
#cozScreenX2, cozScreenY2 = (440, 500)

def calibrate(command, args):
    global calState 
    global coz, cozX1, cozY1, cozX2, cozY2
    global cozScreenX1, cozScreenX2, cozScreenY1, cozScreenY2
    print (command)
    
    if len(command) > 1 and command[1] in ['0','1','2'] :
        calState = command[1]
    
    if len(command) > 1 and command[1] == '\\' :
        if cozX2 == 0:
            x, y, s = (0, 0, "Not yet calibrated!")
        else :
            x, y = getcozScreenXY()
            s = "Are you right there?"
    elif calState == 0 :
        x, y, s = (cozScreenX1, cozScreenY1, "Drive cozmo to here, then do .cal again.")
    elif calState == 1 :
        cozX1 = coz.pose.position.x
        cozY1 = coz.pose.position.y
        cozX2, cozY2 = 0, 0
        x, y, s = (cozScreenX2, cozScreenY2, "Step 2: Drive to here, then do .cal again.")
    elif calState == 2 :
        cozX2 = coz.pose.position.x
        cozY2 = coz.pose.position.y
        x, y, s = (0, 0, "OK, calibration complete.")
        
        cozConfig.set('cozmo', 'cozX1', str(int(cozX1)))
        cozConfig.set('cozmo', 'cozY1', str(int(cozY1)))
        cozConfig.set('cozmo', 'cozX2', str(int(cozX2)))
        cozConfig.set('cozmo', 'cozY2', str(int(cozY2)))
    
    canv = Image.open(canvasFile)
    if x > 0:
        cozImg = Image.open("CozOutline.png")
        canv.paste(cozImg, (x - int(cozImg.size[0] / 2), y - int(cozImg.size[1] / 2)))
    
    drawText(canv, s, 40)
    canv.save("overlay.png")
    canv.close()
    
    if x == 0 :
        time.sleep(1.5)
        clearScreen(None, None)
        calState = 0
    else :
        calState += 1


def getcozScreenXY() :
    global coz, cozX1, cozY1, cozX2, cozY2
    global cozScreenX1, cozScreenX2, cozScreenY1, cozScreenY2
    cozXNew = coz.pose.position.x
    cozYNew = coz.pose.position.y
        
        # To convert cozmo coordinates to screen coordinates, we need to first
        # find the distance cozmo traveled during calibration, and the angle, from a trig function.
    cozDistFromCalibration = ( (cozX2 - cozX1) ** 2 + (cozY2 - cozY1) ** 2 ) ** 0.5
    cozAngleFromCalibration = math.atan2(cozY2- cozY1, cozX2 - cozX1)
    
        # That distance is proportional to the difference in screen position, and that
        # angle will be offset by the screen calibration angle, when we calculate the new screen coords.
    screenDistFromCalibration = ( (cozScreenX2 - cozScreenX1) ** 2 + (cozScreenY2 - cozScreenY1) ** 2 ) ** 0.5
    screenAngleFromCalibration = math.atan2(cozScreenY2 - cozScreenY1, cozScreenX2 - cozScreenX1)
        
        #So to find new screen coords, based on new Coz coords, we apply the distance factor and angle offset
        # to the distance and angle from the starting Coz calibration position to the new Coz position.
    cozDistToNewPos = ( (cozXNew - cozX1) ** 2 + (cozYNew - cozY1) ** 2 ) ** 0.5
    cozAngleToNewPos = math.atan2(cozYNew - cozY1, cozXNew - cozX1)
    
    newScreenDist = cozDistToNewPos * screenDistFromCalibration / cozDistFromCalibration
    newScreenAngle = cozAngleToNewPos + screenAngleFromCalibration - cozAngleFromCalibration
    
    newScreenX = cozScreenX1 + newScreenDist * math.cos(newScreenAngle)
    newScreenY = cozScreenY1 + newScreenDist * math.sin(newScreenAngle)
    return (int(newScreenX), int(newScreenY))


def clearScreen(command, args):
    copyfile(canvasFile,"overlay.png")



def setup_coz(robot_config):
    cozmo.setup_basic_logging('INFO')
    cozmo.robot.Robot.drive_off_charger_on_connect = False

    try:
        thread.start_new_thread(cozmo.connect, (run,))
    except KeyboardInterrupt as e:
        pass        
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
    
    while not coz:
        try:
           time.sleep(0.5)
           print("not coz")
        except (KeyboardInterrupt, SystemExit):
           sys.exit()

    return


def run(coz_conn):
    global coz
    coz = coz_conn.wait_for_robot()
    coz.enable_stop_on_cliff(True)
    
    try:
        print ('starting cozVid thread')
        thread.start_new_thread(cozVid, ())
    except KeyboardInterrupt as e:
        pass        
    #except cozmo.ConnectionError as e:
    #    sys.exit("A connection error occurred: %s" % e)
    
    while 1:
        time.sleep(1)
        checkLastCmdTime()


lastLogged = 0

def vidLog(txt='') :
    global vidLoopIdx, lastLogged, txtToLog
    
    t = time.time()
    if lastLogged == 0 :
        lastLogged = t
        txtToLog = ''
    
    txtToLog += '\n' + str(vidLoopIdx)+': ' + time.strftime('%H:%M:%S') \
        + str(round(time.time() % 1, 1))[1:] + ': ' + txt
    
    if t > lastLogged + 5 :
        with open("cozVidLoop.txt", "a") as vidLogFile :
            vidLogFile.write(txtToLog+' --- wrote to log')
        lastLogged = t
        txtToLog = ''


doSnapShots, doVidInitSnaps, doVidInitStream = (False, True, True)
lastSnapTime, lastCamTime = 0, 0
movedLift = False

def cozVid() :
    global coz, cozCamOn, cozCamX, cozCamY, cozW, cozH, \
        doSnapShots, doVidInitSnaps, doVidInitStream, movedLift, \
        vidLoopIdx, delayCam, delaySnap, lastSnapTime, lastCamTime
    print ('got in cozVid')
    vidLoopIdx = 0
    delayCam, delaySnap = (0.5, 5)
    with open("cozVidLoop.txt", "w") as f :
        f.write("Starting on " + time.strftime("%m/%d/%y") + " : \n")

    while 1 :
        vidLoopIdx += 1
        vidLog("back to start of loop")
        time.sleep (0.5)
        vidLog("")
        vidLog("waited 0.5")
        
        timeNow = time.time()
    
        if doVidInitSnaps and doVidInitStream : 
            print ("video_module = ", video_module)
            if not video_module : 
                print ('not yet...')       
                continue
                
            toggleCozCam(['.cam','ur'], None)   # a little hack to make coz's cam start out appearing in upper right

        #vidLog("cozCamOn, image_stream_enabled = {}, {}".format(cozCamOn, coz.camera.image_stream_enabled))

        # 3/11/23 Use only overlay, instead of an actual video stream:
        #   (periodically save snapshot to replace the BlankCanvas file. Until Snapshot options' turned off.)
        
        doSnaps = doSnapShots and (doVidInitSnaps or timeNow > lastSnapTime + delaySnap)
        
        vidLog("doVidInitSnaps, doVidInitStream, doSnaps, doSnapShots, lastSnapTime = {}, {}, {}, {}, {}".format( + \
            doVidInitSnaps, doVidInitStream, doSnaps, doSnapShots, lastSnapTime))
        
        if doSnaps :    #try every 5 seconds. (it takes up to a couple of seconds to load from the snapshot url) :(
                #try :
            print ('doing snaps')
            urllib2.urlretrieve("http://192.168.1.21:80/snapshot.cgi?user=admin&pwd=", "snapshot.png") 
            img = Image.open("snapshot.png")
            
                #trying to stream higher than 320x240 makes it lag, and sending higher res image to overlay cuts
                # out part of the image, unless it's resized. 
            print("cropping (zooming in), then resizing to resolution: ", video_module.x_res, video_module.y_res)
            
            w, h = (video_module.x_res, video_module.y_res)
            img = img.crop((max(img.width/2 - w, 0), max(img.height/2 - h, 0), \
                min(img.width/2 + w, img.width), min(img.height/2 + h, img.height)))
            img = img.resize((w, h))
            img.save("snapshot.png")
            img.close
            #time.sleep(0.1)
            copyfile("snapshot.png", canvasFile)
                #except:
                #    pass
            doVidInitSnaps = False
            doVidInitStream = True
            lastSnapTime = time.time()
        
        elif doVidInitStream and not doSnapShots :
            fn = canvasFile.replace(".png", "_{}x{}.png".format(video_module.x_res, video_module.y_res))
            print ('copying '+fn+' to '+canvasFile+' and overlay.png.')
            copyfile(fn, canvasFile)
            copyfile(fn, "overlay.png")
            doVidInitStream = False
            doVidInitSnaps = True
        
        doCoz = (cozCamOn and timeNow > lastCamTime + delayCam)
        
        if doCoz :
                # 3/19/23- leaving the image stream enabled seems to make cozmo slow to respond to commands.
                # 3/20/23- but turning it off right away each time seems to not give it time to get the latest image.
                #  It's supposed to have a new image 15x/second... try sleep
            coz.camera.image_stream_enabled = True
            time.sleep(0.2)
            image = coz.world.latest_image
            coz.camera.image_stream_enabled = False
            doCoz = doCoz and image
            if not doCoz :
                vidLog("coz image seems INvalid !!")
            
        if doCoz:
            vidLog("coz image seems valid")
            if annotated:
                image = image.annotate_image() 
            else:
                image = image.raw_image        
            vidLog("got raw image")

            if cozCamX == 1 :
                canv = Image.open(canvasFile)
                canv.paste(image, (0, 0))
            else :      
                image = image.resize((cozW, cozH))
                canv = Image.open(canvasFile)
                canv.paste(image, (int(cozCamX), int(cozCamY)))
            vidLog("pasted to canvas")
            
            lastCamTime = time.time()
            if movedLift :
                canv.save("afterLiftMove.png")
                vidLog("saved afterLiftMove.png")
                movedLift = False

        elif doSnaps :
            canv = Image.open(canvasFile)
            
        if doCoz or doSnaps  :
            for trynum in range(5) :
                try :
                    canv.save("overlay_temp.png") 
                    if trynum > 0: vidLog('saved overlay_temp.png on try #{}'.format(trynum))
                    break
                except Exception as error :
                    vidLog('Error saving overlay_temp: {}'.format(error))
                    time.sleep(0.02)

            canv.close()
            for trynum in range(5) :
                try :
                    copyfile("overlay_temp.png","overlay.png")
                    if trynum > 0: vidLog('copied on try {}'.format(trynum))
                    break
                except Exception as error :
                    vidLog('Error copying overlay_temp.png to overlay.png: {}'.format(error))
                    time.sleep(0.02)


video_module = None
stoppedAudio = True

def checkLastCmdTime():
    # tw- This function checks if the last command was over 2 mins ago.
    #  If so, and we haven't stopped the audio yet, call stopAudioCapture in the video module.
    
    global video_module, stoppedAudio, lastCommandTime
    
    t = time.time()
    #print (str(round(t,2))+' > '+str(round(lastCommandTime,2) + 120)+'?')

    if not stoppedAudio and lastCommandTime > 0 and t > lastCommandTime + 120 \
    and not video_module.mic_off and not video_module.no_mic:
        networking.sendChatMessage(time.strftime("%H:%M:%S")+': stopping audio.')
        print(time.strftime("%H:%M:%S")+': stopping audio.')
        stoppedAudio = True
        video_module.stopAudioCapture()


def run_video():     

    # Turn on image receiving by the camera
    coz.camera.image_stream_enabled = True

    #coz.say_text( "Go!", in_parallel=True)  #"hey everyone, lets robot!", in_parallel=True)

    while True:
        time.sleep(0.25)

        from subprocess import Popen, PIPE
        from sys import platform

        #Frames to file
        #p = Popen(['ffmpeg', '-y', '-f', 'image2pipe', '-vcodec', 'png', '-r', '25', '-i', '-', '-vcodec', 'mpeg1video', '-qscale', '5', '-r', '25', 'outtest.mpg'], stdin=PIPE)
        
        if not os.path.isfile(ffmpeg_location):
            print("Error: cannot find " + str(ffmpeg_location) + " check ffmpeg is installed. Terminating controller")
            thread.interrupt_main()
            thread.exit()

        while not networking.authenticated:    # 2/18/23 tw- removed for testing
            time.sleep(1)

        ffmpegProc = Popen(['C:\\ffmpeg\\bin\\ffmpeg.exe', '-f', 'image2pipe', '-vcodec', 'png', '-i', '-'
           , '-vcodec', 'mpeg1video', '-b:v', '400k', '-r', '20', '-nostats', '-video_size', '320x240', 'vid.mpg'], stdin=PIPE)
        
        # the original:
        
        #ffmpegProc = Popen([ffmpeg_location, '-nostats', '-y', '-f', 'image2pipe', '-vcodec', 'png'
            #'-t', '7', '-thread_queue_size', '5096', '-r', '25', '-i', '-'
            #, '-vcodec', 'mpeg1video', '-r', '25','-b:v', '400k', "-f","mpegts"
            #, "-headers", "\"Authorization: Bearer {}\"".format(robotKey)
            #, "http://{}:1567/transmit?name={}-video".format(server, networking.channel_id)], stdin=PIPE)
            
                # This works to save to a file. --2/23/23 hmm, not anymore...
            #, 'vid.mpeg'], stdin=PIPE)
            
            # couldn't get the direct command below to even start- errors out right away.
        #ffmpegProc = Popen(ffmpeg_location+' -f image2pipe -video-size 320x240 -r 25 -i -'
        #    +' -nostats -y -vcodec png -f mpegts -vcodec mpeg1video -b:v 400k -r 25' 
        #    +' -headers "Authorization: Bearer {}"'.format(robotKey)
        #    +" http://{}:1567/transmit?name={}-video".format(server, networking.channel_id), stdin=PIPE, stderr=PIPE)
        
            # 2/18/23 tw re-doing it to use same options as ffmpeg.py- new code is below: still not working yet.
            
        try:
            while True:
                if coz:
                    image = coz.world.latest_image
                    if image:
                        if annotated:
                            image = image.annotate_image()  #set annotate=1, does help? no
                        else:
                            image = image.raw_image        # to prevent err below, maybe don't get raw_image? doesn't help
                        
                        image.save(ffmpegProc.stdin, 'PNG')      # tw 2/16/23 - I was getting an error here, but not anymore
                        #image.save('tempimage.png', 'PNG')
                        
                        time.sleep(.04)
                        
                        #if ffmpegproc == 0:
                            # 2/18/23 tw-  try using loop- suggested here: https://stackoverflow.com/questions/61884117/loop-input-on-a-http-url-with-ffmpeg
                            #   But it still doesn't work here.

                            #ffmpegProc = Popen([ffmpeg_location, '-stream_loop', '-1', '-t', '15', '-y'
                            #    , '-framerate', '25', '-video_size', '320x240', '-f', 'image2'
                            #    , '-r', '25', '-i', 'tempImage.png', "-f","mpegts", '-codec:v', 'mpeg1video','-b:v', '400k'
                            #    , '-bf', '0', '-muxdelay', '0.001'
                                
                                #, "-headers", "\"Authorization: Bearer {}\"".format(robotKey)
                                #, "http://{}/transmit?name={}-video".format(server, networking.channel_id)], stdin=PIPE)
                                
                                    # This works to save image to a video, but it doesn't capture when image changes. 
                            #    , 'vid.mpeg'])

                            #if ffmpegproc == 0: break
                
                else:              # I commented out the 'else', to try always doing a delay- didn't help
                    time.sleep(.1)      # tried change .1 to .05- didn't help
            
            ffmpegProc.stdin.close()
            ffmpegProc.wait()
        
        except cozmo.exceptions.SDKShutdown:
            ffmpegProc.stdin.close()
            ffmpegProc.wait()
            pass               


def light_cubes(robot: cozmo.robot.Robot):
    #robot.world.connect_to_cubes()     # guess I burnt out my cubes. not working even w/ new batteries
        
    cube1 = robot.world.get_light_cube(LightCube1Id)  # looks like a paperclip
    cube2 = robot.world.get_light_cube(LightCube2Id)  # looks like a lamp / heart
    cube3 = robot.world.get_light_cube(LightCube3Id)  # looks like the letters 'ab' over 'T'

    if cube1 is not None:
        cube1.set_lights(cozmo.lights.red_light)
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube1Id cube - check the battery.")

    if cube2 is not None:
        cube2.set_lights(cozmo.lights.green_light)
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube2Id cube - check the battery.")

    if cube3 is not None:
        cube3.set_lights(cozmo.lights.blue_light)
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube3Id cube - check the battery.")


def dim_cubes(robot: cozmo.robot.Robot):
    cube1 = robot.world.get_light_cube(LightCube1Id)  # looks like a paperclip
    cube2 = robot.world.get_light_cube(LightCube2Id)  # looks like a lamp / heart
    cube3 = robot.world.get_light_cube(LightCube3Id)  # looks like the letters 'ab' over 'T'

    if cube1 is not None:
        cube1.set_lights_off()
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube1Id cube - check the battery.")

    if cube2 is not None:
        cube2.set_lights_off()
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube2Id cube - check the battery.")

    if cube3 is not None:
        cube3.set_lights_off()
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube3Id cube - check the battery.")

    #robot.world.disconnect_from_cubes()
    

def sing_song(robot: cozmo.robot.Robot):
    # scales is a list of the words for Cozmo to sing
        # tw 2/25/23 Added the actual notes to play
    scales = [["Doe","C2"], ["Ray","D2"], ["Mi","E2"], ["Faw","F2"], ["So","G2"], ["La","A2"], ["Ti","B2"], ["Doe","C3"]]

    # Find voice_pitch_delta value that will range the pitch from -1 to 1 over all of the scales
    voice_pitch = -1.0
    voice_pitch_delta = 2.0 / (len(scales) - 1)

        # Move head and lift down to the bottom, and wait until that's achieved
    robot.move_head(-5) # start moving head down so it mostly happens in parallel with lift
    robot.set_lift_height(0.0).wait_for_completed()
    robot.set_head_angle(degrees(-25.0)).wait_for_completed()

        # Start slowly raising lift and head
    robot.move_lift(0.15)
    robot.move_head(0.15)

        # "Sing" each note of the scale at increasingly high pitch
        #   2/25/23 tw- Ha- I can't tell any difference in pitch.
    for notes in scales:
        robot.say_text(notes[0], voice_pitch=voice_pitch, duration_scalar=0.3).wait_for_completed()
        voice_pitch += voice_pitch_delta
        print(voice_pitch)
        
        robot.play_song(    # tw 2/25/23 Added
            [cozmo.song.SongNote(getattr(cozmo.song.NoteTypes, notes[1]), cozmo.song.NoteDurations.Quarter)]
        ).wait_for_completed()

    robot.move_lift(0)      # tw 2/25/23 Added. lift up/down stopped working after this function- maybe this fixed it
    robot.move_head(0)


def check_battery( coz: cozmo.robot.Robot ):
    global lastBatteryLevelReached      # 1=low, 2=high 
    global lastDockStatus               # 1=docked, 2=roaming
    batt = coz.battery_voltage
    
    if batt < charge_low and lastBatteryLevelReached == 2:
        lastBatteryLevelReached = 1
        chatAndSay("Battery low. Put me on my charger please.")
        showMsgBattery()
    
    if batt > charge_high and lastBatteryLevelReached == 1:
        lastBatteryLevelReached = 2
        chatAndSay("Finished charging. Thank you")
        showMsgBattery()
    
    if coz.is_on_charger:
        if lastDockStatus == 2:
            #timeDocked = time.time()
            chatAndSay("Started charging. Thank you!")
        elif coz.battery_voltage < charge_high:   #and time.time() > timeDocked + 5
            chatAndSay("Oh, I'm not done charging yet.")

        showMsgBattery()
        lastDockStatus = 1
   
    if not coz.is_on_charger:
        lastDockStatus = 2


def chatAndSay(msg):
    networking.sendChatMessage(msg)
    say(msg)
    print(msg)


def showMsgBattery():
    batt = coz.battery_voltage
    msg = "Battery voltage: " + str(round(batt,2))
    if batt > charge_high:
        msg += ' -- Fully charged!'
    else:
        msg += ' Full at: '+str(round(charge_high,2))
    print(msg)
    networking.sendChatMessage(msg)
    
        
lastCommandTime2 = 0
moveIdx = 0
        
def move(args):
    global coz, is_headlight_on, lastCommandTime2, moveIdx, movedLift
    
    command = args['button']['command']
    moveIdx += 1
    mymoveIdx = moveIdx 
    t = time.time()
    vidLog('')
    vidLog('    '+str(mymoveIdx)+': Time: '+str(round(t,2)) + ': received command: '+command+'  last cmd received:' + str(round(lastCommandTime2, 2)))

    if t < lastCommandTime2 + 0.2:   #tw- don't even try to process rapid commands.
        vidLog('    '+str(mymoveIdx)+': cancelled cmd.')
        return False
    
    lastCommandTime2 = t
    CaptureCommand(args['user']['username'], command)
    vidLog('    '+str(mymoveIdx)+': done w/ capture')
    
        # Check this first, since we don't need audio for this.
    if command == 'b':
        showMsgBattery()
        return

    checkAudioStart(args['user']['username'])
    vidLog('    '+str(mymoveIdx)+': done w/ checkAudio')
    
        # Next, check for the 'say stuff' commands, because we don't need 
        # coz to move off his charger for them.
    if checkSayStuff(command) :
        return
    
    vidLog('    '+str(mymoveIdx)+': done with CheckSayStuff')
    
    try:
        if coz.battery_voltage > charge_high or not stay_on_dock:
            vidLog('    '+str(mymoveIdx)+': calling drive off charger')
            act = coz.drive_off_charger_contacts()  #.wait_for_completed()
            vidLog('    '+str(mymoveIdx)+': drive off charger started')
            act_i = 0
            while not act.is_completed: 
                vidLog('    '+str(mymoveIdx)+': checked action status- not complete yet')
                time.sleep(0.1)
                act_i += 0.1
                vidLog('    '+str(mymoveIdx)+': waited '+str(act_i)+' seconds')
            vidLog('    '+str(mymoveIdx)+': done with drive off charger')

        if command == 'w':
            #causes delays #coz.drive_straight(distance_mm(10), speed_mmps(50), False, True).wait_for_completed()
            coz.drive_wheels(forward_speed, forward_speed, forward_speed*4, forward_speed*4 )
            waitAndStop(mymoveIdx)
        elif command == 's':
            #causes delays #coz.drive_straight(distance_mm(-10), speed_mmps(50), False, True).wait_for_completed()
            coz.drive_wheels(-forward_speed, -forward_speed, -forward_speed*4, -forward_speed*4 )
            waitAndStop(mymoveIdx)
            vidLog('    '+str(mymoveIdx)+': called drive_wheels to stop')
        elif command == 'a':
            #causes delays #coz.turn_in_place(degrees(15), False).wait_for_completed()
            coz.drive_wheels(-turn_speed, turn_speed, -turn_speed*4, turn_speed*4 )
            waitAndStop(mymoveIdx)
        elif command == 'd':
            #causes delays #coz.turn_in_place(degrees(-15), False).wait_for_completed()
            coz.drive_wheels(turn_speed, -turn_speed, turn_speed*4, -turn_speed*4 )
            waitAndStop(mymoveIdx)

        #move lift
        elif command == 'q':
            coz.set_lift_height(height=1).wait_for_completed()
            vidLog('    '+str(mymoveIdx)+': Lift up complete')
            movedLift=True
        elif command == 'e':
            coz.set_lift_height(height=0).wait_for_completed()
            vidLog('    '+str(mymoveIdx)+': Lift down complete')
            movedLift=True

        #look up or down
        #-25 (down) to 44.5 degrees (up)
        elif command == 'f':
            #head_angle_action = coz.set_head_angle(degrees(0))
            #clamped_head_angle = head_angle_action.angle.degrees
            #head_angle_action.wait_for_completed()
            coz.move_head(-2.0)
            time.sleep(0.15)
            coz.move_head(0)
        elif command == 'r':
            #head_angle_action = coz.set_head_angle(degrees(44.5))
            #clamped_head_angle = head_angle_action.angle.degrees
            #head_angle_action.wait_for_completed()
            coz.move_head(2.0)
            time.sleep(0.15)
            coz.move_head(0)

        #toggle light
        elif command =='c':
            is_headlight_on = not is_headlight_on
            coz.set_head_light(enable=is_headlight_on)
            time.sleep(0.35)

        elif command =='v':
            video_module.restartVideoCapture()

        #animations from example
        elif command.isdigit():
            animName = default_anims_for_keys[int(command)]
            act = coz.play_anim(name=animName)
                #while a pet animation's playing, do the kitty jig on screen :)
                #For these animations, first turn off coz's overlay cam, if it's on.
            if 'petdetection' in animName and cozCamOn :
                toggleCozCam(['.cam'], None)    
            if 'petdetection_cat' in animName :
                getKitties(7, 0.8, 0)  # runAwayFactor=0 because they don't run away for meowing at them :)
            if 'petdetection_dog' in animName :
                chaseKitties()
            act.wait_for_completed()    # then finish the cozmo animation, if not done yet.
            
        elif command == "n":
            playAnimListNext()
            
        if not command.isdigit() and command not in ["singsong","g","n"]:
            check_battery(coz)

    except cozmo.exceptions.RobotBusy:
        return False
        
    vidLog('    '+str(mymoveIdx)+': done')


def waitAndStop(mymoveIdx) :
    global timeToStopMove
    timeToStopMove = time.time() + 0.5
    vidLog('    '+str(mymoveIdx)+': called drive_wheels')
    time.sleep(0.5)
    vidLog('    '+str(mymoveIdx)+': slept 0.5')
    if timeToStopMove <= time.time() :      #If another command was sent in the meantime, then timeToStopMove 
        coz.drive_wheels(0, 0, 0, 0 )       # will be later, So don't stop it yet. The next move will stop it.
        vidLog('    '+str(mymoveIdx)+': called drive_wheels to stop')



def getKitties(numKitties, dly, runAwayFactor):
    canv = Image.open(canvasFile)
    kit = Image.open("kitty.png")
    
    kittyW = kit.size[0]
    kittyH = kit.size[1]
    maxWidth = (canv.size[0] - kittyW) 
    maxHeight = (canv.size[1] - kittyH) 
    
        # maximum width and height of our starting box will be half the total width and height.
        # and it will start 25% in from the edges. (when runAwayFactor = 0)
        # As runAwayFactor increases, the boxes will break apart toward the corners.
        #  3/10/23: Let's start only 15% in from edges, but start going farther out as runAwayFactor increases.
    mult = 0.15 + 0.02 * runAwayFactor
    boxX = maxWidth * (mult - runAwayFactor * mult / 5)
    boxY = maxHeight * (mult - runAwayFactor * mult / 5)
    
    boxX2 = maxWidth - boxX - maxWidth * mult
    boxY2 = maxHeight - boxY - maxHeight * mult
    
        # But we split the max width/height in two again, because our boxes will expand out, so we 
        #  will "flip a coin" to see which box- on top or bottom- flip coin again to see
        #   if we put on left or on right.
    maxWidth = maxWidth * mult
    maxHeight = maxHeight * mult

       # This was just to make sure ktties were being drawn with top left corner inside the boxes
       # which are going out toward the corners.
    #draw = ImageDraw.Draw(canv)        
    #draw.rectangle([boxX, boxY, boxX + maxWidth, boxY + maxHeight], outline=(255,255,255,255), width=4)
    #draw.rectangle([boxX2, boxY, boxX2 + maxWidth, boxY + maxHeight], outline=(255,255,255,255), width=4)   
    #draw.rectangle([boxX, boxY2, boxX + maxWidth, boxY2 + maxHeight], outline=(255,255,255,255), width=4)
    #draw.rectangle([boxX2, boxY2, boxX2 + maxWidth, boxY2 + maxHeight], outline=(255,255,255,255), width=4)   
    
    #print (boxX, boxY, boxX + maxWidth, boxY + maxHeight)
    #print (boxX2, boxY, boxX2 + maxWidth, boxY + maxHeight)
    #print (boxX, boxY2, boxX + maxWidth, boxY2 + maxHeight)
    #print (boxX2, boxY2, boxX2 + maxWidth, boxY2 + maxHeight)
    
    for i in range(numKitties):
        x1 = random.randrange(int(maxWidth))  
        y1 = random.randrange(int(maxHeight))
        
        # x,y will be top-left corner of the kitty image.
        # Start the boxes at 25% in from the edges, and move them back out towards the corners as runAwayFactor increases.
        # (runAwayFactor starts at 0.) Flip a coin: if heads, then boxX starts out at 25% of maxwidth.
        #   If tails, boxX starts on the right side, from maxWidth minus 25% of maxWidth.
        
        coin1 = random.randrange(2)
        if coin1 == 1 :
            x = boxX + x1
        else :
            x = boxX2 + x1
        
        # Flip a coin again to see if we start from top or from bottom.
        
        coin2 = random.randrange(2)
        if coin2 == 1 :
            y = boxY + y1
        else :
            y = boxY2 + y1

        #print ('runAwayFactor,coin1,coin2,x,y,x1,y1,maxW,maxH = {},{},{},{},{},{},{},{},{}'.format(runAwayFactor,coin1,coin2,x,y,x1,y1,maxWidth,maxHeight))

        canv.paste(kit, (int(x), int(y)))
        if dly > 0 : 
            canv.save("overlay.png")
            time.sleep(dly)
    
    if dly == 0 : 
        canv.save("overlay_temp.png")       # see if this helps the ffmpeg not freeze up- yes, it helps!
        canv.close()
        copyfile("overlay_temp.png","overlay.png")
    else :
        s = 'Now how do we scare away these kitties?'
        drawText(canv, s)
        canv.save("overlay.png")
        canv.close()


def chaseKitties():
    for runAwayFactor in range(6):
        getKitties(20, 0, runAwayFactor)
        time.sleep(0.4)
    clearScreen(None, None)
    

lastCommandTime = 0

def checkAudioStart(user = ''):
    # tw- This is called from the move or say functions, so we only try to restart audio when ready to move or speak.
    #  This function checks if the last command was over 30 seconds ago. 
    #  If so, call restartAudioCapture in the video module.

    global lastCommandTime, video_module, stoppedAudio
   
    t = time.time()
    print ('checking audio restart: t={} lastCmd={}'.format(t, lastCommandTime))
    
    if video_module is not None and t > lastCommandTime + 120 :
      print ('extended_command.is_authed(user) =', extended_command.is_authed(user))
      print ('video_module.mic_off, video_module.no_mic =', video_module.mic_off, video_module.no_mic)
      
      if video_module is not None and not video_module.mic_off and not video_module.no_mic \
      and extended_command.is_authed(user) != 2:        # Don't turn audio back on for Owner commands.
        networking.sendChatMessage(time.strftime("%H:%M:%S")+': Restarting audio...')
        print(time.strftime("%H:%M:%S")+': restarting audio.')
        lastCommandTime = t
        stoppedAudio = False
        video_module.restartAudioCapture()
        #time.sleep(1.5)
        for i in range(15):
            time.sleep(0.1)
            #print(video_module.audio_process.communicate()) #does it work? nope. tries to read from stderr which is closed
    
    if video_module is not None :
        lastCommandTime = t


def checkSayStuff(command):

    try:
        #things to say with TTS disabled

        if command == 'sayhi':
            say( "hi! I'm cozmo!" )
        elif command == 'saywatch':
            say( "watch this" )
        elif command == 'saylove':
            say( "i love you" )
        elif command == 'saybye':
            say( "bye" )
        elif command == 'sayhappy':
            say( "I'm happy" )
        elif command == 'saysad':
            say( "I'm sad" )
        elif command == 'sayhowru':
            say( "how are you?" )

        elif command == "j":
            TellJoke()

        #sing song example
        elif command == "singsong":
            print( "singing song" )
            sing_song( coz )

        elif command == "g":
            showAnims()
            
        else :
            return False
        
        return True
        
    except cozmo.exceptions.RobotBusy:
        return False


def say(message):
    try:
        checkAudioStart()
        coz.say_text(message, duration_scalar=0.75)
    except cozmo.exceptions.RobotBusy:
        return False


def CaptureCommand(user, cmd):
    conn = sl.connect('CozData.db')
    #conn.execute("drop table userCmdHistory")

    if conn.execute("SELECT name FROM sqlite_master WHERE name='userCmdHistory'").fetchone() is None:
        conn.execute('create table userCmdHistory (cmdDate date, user text, hour int, cmd text, num int)')  # STRICT')
            # the strict keyword is available in SQLLite vers 3.37.0
            # I got syntax error, so I guess this python version has older SQLLite

    conn.execute("""create unique index if not exists indexUserCmdHistory on userCmdHistory 
        (cmdDate, user, hour, cmd)""")

    tm = time.localtime()
    Upsert(conn, time.strftime('%x', tm), user, tm.tm_hour, tm.tm_min, time.strftime('%H:%M:%S', tm), cmd)
    conn.commit()
    conn.close()


def Upsert(conn, vDate, vUser, vHour, vMinute, vTime, vCmd):  # upsert = update or insert :)
    # activity will be a string of length 30 showing either '-' or 'X' for each 2 minute interval
    #  to tell if there was activity in that 2 min interval.
    
    # On conflict, append to the end of the current value of activity, starting from the n-th characters of act,
    #  where n = 1 past the current length of activity.
    #  i.e., if old value of activity = '--XX', and act = '------X', then append '--X' to the end 
    #  of the old value.  So new value is '--XX--X'.
    
    act = '-' * int(vMinute / 2) + 'X'
    conn.execute("""insert into userCmdHistory (cmdDate, user, hour, earliestTime, latestTime, cmd, num, activity) 
        values (?, ?, ?, ?, ?, ?, 1, ?)
        on conflict (cmdDate, user, hour, cmd) do update 
        set num = num + 1, activity = ifnull(activity,'') || substr(excluded.activity, ifnull(length(activity), 0) + 1)
            , latestTime = ?
    """, (vDate,vUser,vHour,vTime,vTime,vCmd,act,vTime))
