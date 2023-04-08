
CozScreenX1, CozScreenY1 = (640, 360)
cozScreenX2, CozScreenY2 = (440, 500)

def getCozScreenXY() :
    #global coz, cozX1, cozY1, cozX2, cozY2
    global CozScreenX1, CozScreenX2  #, CozScreenY1, CozScreenY2
    
    screenDistFromCalibration = (cozScreenX2 - CozScreenX1) ** 2 + (CozScreenY2 - cozScreenY1) ** 2 


getCozScreenXY()
