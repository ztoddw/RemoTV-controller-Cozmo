import requests
import time
import traceback
import ssl
import sys
import json
import logging
import networking

if (sys.version_info > (3, 0)):
    import urllib.request as urllib2
    from urllib.error import HTTPError
else:
    import urllib2
    from urllib2 import HTTPError

log = logging.getLogger('RemoTV.robot_util')

terminateLocked=None

def terminate_controller():
    log.info('Attempting to terminate controller...')
    if terminateLock != None:
        terminateLock.acquire()
    
    # Should we try to restart the controller here?


# TODO : Think about rewriting this, and using request.

def getWithRetry(url, secure=True):
    for retryNumber in range(2000):
        try:
            log.debug("GET %s", url)
            ctx = ssl.create_default_context()
            if secure:      # 2/19/23 tw- added context- see https://docs.python.org/3.7/library/ssl.html#ssl.SSLContext.check_hostname
                #ctx.verify_mode = ssl.CERT_REQUIRED     # but still didn't work.
                #ctx.check_hostname = True
                #ctx.load_default_certs()
                
                import requests as r        # 2/19/23 tw- try this- it WORKED!
                ca_f = r.certs.where()
                response = urllib2.urlopen(url, cafile=ca_f).read()  # 2/19/23 tw- added cafile parameter
            else:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                response = urllib2.urlopen(url, context=ctx).read()
            break
        except:
            log.exception("could not open url %s", url)
            #traceback.print_exc()
            time.sleep(2)

    return response.decode('utf-8')

def sendChatMessage(message):
    networking.sendChatMessage(message)

