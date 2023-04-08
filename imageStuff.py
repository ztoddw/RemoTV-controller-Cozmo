
from PIL import Image #,ImageFont,ImageDraw
import urllib.request as urllib2
#from urllib.error import HTTPError
import time

print(time.time())
url = "http://192.168.1.21:80/snapshot.cgi?user=admin&pwd="
urllib2.urlretrieve(url, "testImg.png")
print(time.time())

img = Image.open("testImg.png")
img = img.resize((320,240))
img.save ("testImg.png") 
img.close()



"""
canv = Image.open("BlankCanvas.png")
s = "Two fish went into a bar"

draw = ImageDraw.Draw(canv)
fnt = ImageFont.truetype("arial.ttf", 50)
draw.text((250, 600), s, font=fnt, fill=(0,0,0,255))
print(s)

canv.save("test.png")



kit = Image.open("kitty.png")

for i in range(1,5):
    print (i, kit.size, canv.size)
    canv.paste(kit, (50*i, 50*i))

canv.save("test.png")

"""
