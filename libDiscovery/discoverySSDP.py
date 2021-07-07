from .netdisco.ssdp import *
from .netdisco.util import *
from pprint import pprint

import urllib.request as urllib2
import xmltodict
import json
import httpx
from time import sleep
#print("Scanning SSDP..")
def discSSDP():
    return buscarVulnUPnP(entries=scan())

def buscarVulnUPnP(entries):
    if len(entries["dispositivosUPNP"])>0:
        for item in range(0, len(entries["dispositivosUPNP"])):
            client1 = httpx.Client(timeout=30)
            sleep(1)
            if entries["dispositivosUPNP"][item]['normalName'] == "Kodi":
                params = {'keyword': entries["dispositivosUPNP"][item]['normalName'],
                         'cpeMatchString': 'cpe:/:'+ entries["dispositivosUPNP"][item]['normalName'] +':'+ entries["dispositivosUPNP"][item]['normalName'] +':'+ entries["dispositivosUPNP"][item]['normalVersion'],
                         'pubStartDate': '2016-01-01T00:00:00:000 UTC-00:00'
                         }
                exct=0
                try:
                    r = client1.get('https://services.nvd.nist.gov/rest/json/cves/1.0', params=params)
                    print(r.url)
                except:
                    exct=1
                    print("An error occurred while requesting.")
                if exct == 0:
                    entries["dispositivosUPNP"][item]["cves"]=r.json()
                else:
                    entries["dispositivosUPNP"][item]["cves"]={"totalResults":0}
            else:
                params = {'keyword': entries["dispositivosUPNP"][item]['normalName'],
                         'cpeMatchString': 'cpe:/:'+ entries["dispositivosUPNP"][item]['normalName'].split(" ")[0],
                         'pubStartDate': '2016-01-01T00:00:00:000 UTC-00:00'
                         }
                exct=0
                try:
                    r = client1.get('https://services.nvd.nist.gov/rest/json/cves/1.0', params=params)
                    print(r.url)
                except:
                    exct=1
                    print("An error occurred while requesting.")
                if exct == 0:
                    entries["dispositivosUPNP"][item]["cves"]=r.json()
                else:
                    entries["dispositivosUPNP"][item]["cves"]={"totalResults":0}
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

