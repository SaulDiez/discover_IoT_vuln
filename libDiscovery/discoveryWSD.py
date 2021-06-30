from .libWSD_Onvif.util import runWSDiscovery
import httpx
from time import sleep
print("Probe: Running Network Device Discovery ...")

def discWSD():
    return buscarVulnWSD(entries=runWSDiscovery())

def buscarVulnWSD(entries):
    if len(entries["serviciosWSD"])>0:
        for item in range(0, len(entries["serviciosWSD"])):
            sleep(1)
            params = {'keyword': entries["serviciosWSD"][item]['Server'],
                         'pubStartDate': '2016-01-01T00:00:00:000 UTC-00:00'
                         }
            exct=0
            try:
                r = httpx.get('https://services.nvd.nist.gov/rest/json/cves/1.0', params=params)
                print(r.url)
            except httpx.ReadTimeout as exc:
                exct=1
                print(f"An error occurred while requesting {exc.request.url!r}.")
            if exct == 0:
                entries["serviciosWSD"][item]["cves"]=r.json()
    return entries