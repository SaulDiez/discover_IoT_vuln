from .netdisco.ssdp import *
from .netdisco.util import *
from pprint import pprint

import urllib.request as urllib2
import xmltodict
import json

#print("Scanning SSDP..")
def discSSDP():
    return scan()
#discoveredDict=scan()
#for url in discoveredDict:
#    print(discoveredDict.values())
#pprint(scan())

#ver fin ssdp.py y listar urls y listar jsons
#file = urllib2.urlopen('http://192.168.1.193:1608/')
#data = file.read()
#file.close()
#data = xmltodict.parse(data)

#discUPNPJson = json.dumps(discoveredDict)
#print(data)
#print(discUPNPJson)

