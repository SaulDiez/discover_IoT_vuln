#!/usr/bin/env python3

from time import sleep

from zeroconf import IPVersion, ServiceBrowser, ServiceStateChange, Zeroconf, ZeroconfServiceTypes
import json

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

    sleep(1)
    zeroconf.close()
    dictMDNSJson = json.dumps(dictMDNS)
    print(dictMDNS)

#start_browserMDNS()
    return dictMDNS
#    try:
#        while True:
#            sleep(0.1)
#    except KeyboardInterrupt:
#        pass
#    finally:
#        zeroconf.close()
