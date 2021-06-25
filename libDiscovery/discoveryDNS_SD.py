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
            if len(normalName)<40:
                dic["normalName"] = normalName
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
    print(dictMDNS)
    dictMDNSVuln=buscarVulnMDNS(entries=dictMDNS)
    return dictMDNSVuln

def buscarVulnMDNS(entries):
    if len(entries["serviciosMDNS"])>0:
        for item in range(0, len(entries["serviciosMDNS"])):
            sleep(1)
            print(str(item))
            params = {'keyword': entries["serviciosMDNS"][item]["normalName"],
                     'cpeMatchString': 'cpe:/:'+ entries["serviciosMDNS"][item]['normalName'] +':'+ entries["serviciosMDNS"][item]['normalName'],
                     'pubStartDate': '2016-01-01T00:00:00:000 UTC-00:00'
                     }
            exct=0
            try:
                r = httpx.get('https://services.nvd.nist.gov/rest/json/cves/1.0', params=params)
            except httpx.ReadTimeout as exc:
                exct=1
                print(f"An error occurred while requesting {exc.request.url!r}.")
            if exct == 0:
                if r.json()["totalResults"] != '0':
                    entries["serviciosMDNS"][item]["cves"]=r.json()
            sleep(1)
            print(str(item))
            params = {'keyword': entries["serviciosMDNS"][item]['normalService'],
                     'pubStartDate': '2016-01-01T00:00:00:000 UTC-00:00'
                     }
            exct=0           
            try:
                r = httpx.get('https://services.nvd.nist.gov/rest/json/cves/1.0', params=params)
            except httpx.ReadTimeout as exc:
                exct=1
                print(f"An error occurred while requesting {exc.request.url!r}.")
            if exct == 0:
                if r.json()["totalResults"] != '0':
                    entries["serviciosMDNS"][item]["cves"]=r.json()

    
    return entries