from .libWSD_Onvif.util import runWSDiscovery
import httpx
from time import sleep
print("Probe: Running Network Device Discovery ...")

def discWSD():
    return buscarVulnWSD(entries=runWSDiscovery())

def buscarVulnWSD(entries):
    if len(entries["serviciosWSD"])>0:
        for item in range(0, len(entries["serviciosWSD"])):
            client1 = httpx.Client(timeout=30)
            sleep(1)
            params = {'keyword': entries["serviciosWSD"][item]['Server'],
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
                entries["serviciosWSD"][item]["cves"]=r.json()
            else:
                entries["serviciosWSD"][item]["cves"]={"totalResults":0}
    return entries