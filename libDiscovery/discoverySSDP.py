from .netdisco.ssdp import *
from .netdisco.util import *
from pprint import pprint

import urllib.request as urllib2
import xmltodict
import json
import httpx
#print("Scanning SSDP..")
def discSSDP():
    return buscarVuln(entries=scan())

def buscarVuln(entries):
    if len(entries["dispositivosUPNP"])>0:
        for item in range(0, len(entries["dispositivosUPNP"])):
            params = {'keyword': entries["dispositivosUPNP"][item]['normalName'],
                     'cpeMatchString': 'cpe:/:'+ entries["dispositivosUPNP"][item]['normalName'] +':'+ entries["dispositivosUPNP"][item]['normalName'] +':'+ '17.0'#entries["dispositivosUPNP"][item]['normalVersion']
                     }
            r = httpx.get('https://services.nvd.nist.gov/rest/json/cves/1.0', params=params)
            entries["dispositivosUPNP"][item]["cves"]=r.json()
        strdsfsd="https://services.nvd.nist.gov/rest/json/cves/1.0?keyword=kodi&cpeMatchString=cpe:/:kodi:kodi:17.0"

    return entries
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

