
import random
from PIL import Image

def test1():
    for i in range(9):
        coin = random.randrange(2)
        print ('coin flip = '+str(coin))

def test2():
    kit = Image.open("kitty.png")
    
    kittyW = kit.size[0]
    kittyH = kit.size[1]

        # Split the max width/height in two, because box will expand out- half
        #  the time we will them on top or on left- other half of the time they
        #  go on bottom or on right.

    maxWidth = (1280 - kittyW) / 2 
    maxHeight = (720 - kittyH) / 2
    
    runAwayFactor = 0
    
    for i in range(7):
        # x,y will be top-left corner of the kitty image.
        
        x = random.randrange(int(maxWidth))  
        y = random.randrange(int(maxHeight))
        
        # Start the box at 25% in from the edges, and move it back out towards the edges
        #  (runAwayFactor starts at 0, so we flip a coin: if heads, then this will start out at 25% of maxwidth.
        #   If tails, this will start on the right side, from maxWidth minus 25% of maxWidth.
        #   As runAwayFactor increases, the strips expand out towards the edges.
        
        coin1 = random.randrange(2)
        if coin1 == 1 :
            x = maxWidth * (0.25 - runAwayFactor * 0.05) + x
        else :
            x = maxWidth - maxWidth * (0.25 - runAwayFactor * 0.05) - x
        
        # Flip a coin again to see if we start from top or from bottom.
        
        coin2 = random.randrange(2)
        if coin2 == 1 :
            y = maxHeight * (0.25 - runAwayFactor * 0.05) + y
        else :
            y = maxHeight - maxHeight * (0.25 - runAwayFactor * 0.05) - y

        print ('coin flips = '+str(coin1)+', '+str(coin2))
        print ('x,y,maxW,maxH,runAwayFac = {},{},{},{},{}'.format(x,y,maxWidth,maxHeight,runAwayFactor))

        
test2()
