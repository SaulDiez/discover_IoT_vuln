#!/usr/bin/env python3

from time import sleep

from zeroconf import IPVersion, ServiceBrowser, ServiceStateChange, Zeroconf, ZeroconfServiceTypes
import json
import httpx

dictMDNS={}
lista = []
def on_service_state_change(
    zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange
) -> None:
    dic = {}
    #checkSameDevices=0
    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info:
            dic["ServiceType"]=info.type
            dic["Name"] = info.name
            dic["Port"] = info.port
            dic["IPv4"] = info.parsed_addresses(version=IPVersion.V4Only)
            dic["Addresses"] = info.parsed_addresses()
            dic["Host"] = info.server

            normalName=dic["Name"].split(" (")[0]
            if len(normalName)<60:
                dic["normalName"] = normalName.split(" -")[0]
            else:
                dic["normalName"] = ""

            normalService=dic["ServiceType"].split("_")[1].split("_")[0].split(".")[0].split("-")[0]
            dic["normalService"] = normalService.upper()

            if info.properties:
                for key, value in info.properties.items():
                    dic[key.decode("utf-8")] = value.decode("utf-8")
            #else:
            #    print("  No properties")

            if dic:
                lista.append(dic)
            '''    if lista:
                    for service in lista:
                        if service["Name"] == dic["Name"]:
                            checkSameDevices=1
                            break
                    if checkSameDevices != 1:
                            lista.append(dic)
                    checkSameDevices = 0
                else:
                    lista.append(dic)
            #print(dic)'''
        #else:
        #    print("  No info")

        dictMDNS["serviciosMDNS"] = lista
        
def discMDNS():
    if lista:#limpia la lista de busquedas pasadas
        lista.clear()
    zeroconf = Zeroconf(ip_version = IPVersion.V4Only)
    services = list(ZeroconfServiceTypes.find(zc=zeroconf))

    print("\nBrowsing %d MDNS service(s), press Ctrl-C to exit...\n" % len(services))
    browser = ServiceBrowser(zeroconf, services, handlers=[on_service_state_change])

    sleep(0.5)
    zeroconf.close()
    #dictMDNSJson = json.dumps(dictMDNS)
    #print(dictMDNS)
    dictMDNSVuln=buscarVulnMDNS(entries=dictMDNS)
    #print(dictMDNSVuln)
    return dictMDNSVuln

def buscarVulnMDNS(entries):
    if len(entries["serviciosMDNS"])>0:
        for item in range(0, len(entries["serviciosMDNS"])):
            client1 = httpx.Client(timeout=30)
            sleep(1)
            print(str(item))
            if entries["serviciosMDNS"][item]["normalName"] != "":
                if entries["serviciosMDNS"][item]["normalName"] == "Kodi":
                    params = {'keyword': entries["serviciosMDNS"][item]["normalName"],
                            'cpeMatchString': 'cpe:/:'+ entries["serviciosMDNS"][item]['normalName'] +':'+ entries["serviciosMDNS"][item]['normalName'],
                            'pubStartDate': '2016-01-01T00:00:00:000 UTC-00:00'
                             }
                else:
                    params = {'keyword': entries["serviciosMDNS"][item]["normalName"],
                            'cpeMatchString': 'cpe:/:'+ entries["serviciosMDNS"][item]['normalName'].split(" ")[0],
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
                    #if r.json()["totalResults"] != '0':
                    entries["serviciosMDNS"][item]["cves"]=r.json()
                else:
                    entries["serviciosMDNS"][item]["cves"]={"totalResults":0}

            sleep(1)
            print(str(item))
            if (len(entries["serviciosMDNS"][item]['normalService']) > 3) and (entries["serviciosMDNS"][item]['normalService'] != "HTTP"):
                params = {'keyword': entries["serviciosMDNS"][item]['normalService'],
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
                    #if r.json()["totalResults"] != '0':
                    entries["serviciosMDNS"][item]["cves"]=r.json()
                else:
                    entries["serviciosMDNS"][item]["cves"]={"totalResults":0}

    
    return entries