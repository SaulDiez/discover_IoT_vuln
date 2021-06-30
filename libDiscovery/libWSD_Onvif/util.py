from xml.dom import minidom
from io import StringIO
import random
import socket
import httpx
#import time	deberia ser necesaria
import uuid
import os
import re

from urllib.parse import urlparse
from .onvif2 import ONVIFCamera
from zeep.transports import Transport

try:
    import netifaces
except ImportError:
    netifaces = None

from .namespaces import *

from .scope import Scope
from .qname import QName
from .soapenvelope import SoapEnvelope
from .proberesolvematch import ProbeResolveMatch

import json

#comprueba el tipo de mensaje (probe o hello) a mandar. Solo lo llama runWSDiscovery 
def envelopeWSDiscovery(types=None, action=None):
    env = SoapEnvelope()
    env.setTo(ADDRESS_ALL)
    env.setMessageId(uuid.uuid4().urn)
    env.setTypes(types)
    env.setEPR("epr")
    if action is ACTION_HELLO:
        strProbe = createHelloAsProbeMessage(env)
    else:
        strProbe = createProbeMessage(env)
    return strProbe

#obtiene el valor del tipo sin el prefijo. Solo lo llama getQNameFromValue 
def getNamespaceValue(node, prefix):
    while node is not None:
        if node.nodeType == minidom.Node.ELEMENT_NODE:
            attr = node.getAttributeNode("xmlns:" + prefix)
            if attr is not None:
                return attr.nodeValue
        node = node.parentNode
    return ""

#pone un valor por defecto para el tipo. Solo lo llama getQNameFromValue
def getDefaultNamespace(node):
    while node is not None:
        if node.nodeType == minidom.Node.ELEMENT_NODE:
            attr = node.getAttributeNode("xmlns")
            if attr is not None:
                return attr.nodeValue
        node = node.parentNode
    return ""

#obtiene la lista de los tipos sin prefijo. Solo lo llama getTypes 
def getQNameFromValue(value, node):
    vals = value.split(":")
    ns = ""
    if len(vals) == 1:
        localName = vals[0]
        ns = getDefaultNamespace(node)
    else:
        localName = vals[1]
        ns = getNamespaceValue(node, vals[0])
    return QName(ns, localName)

#reformatea espacios en listas para los nodos. Lo llama getTypes, getScopes, getXAddrs
def _parseSpaceSeparatedList(node):
    if node.childNodes:
        return [item.replace('%20', ' ') for item in node.childNodes[0].data.split()]
    else:
        return []

#devuleve lista de los tipos de dispositivo a partir del nodo.
def getTypes(typeNode):
    return [getQNameFromValue(item, typeNode) for item in _parseSpaceSeparatedList(typeNode)]

#devuleve lista de los scopes de dispositivo a partir del nodo.
def getScopes(scopeNode):
    matchBy = scopeNode.getAttribute("MatchBy")
    return [Scope(item, matchBy) for item in _parseSpaceSeparatedList(scopeNode)]

#devuleve la dirección para comunicarse con el dispositivo.
def getXAddrs(xAddrsNode):
    return _parseSpaceSeparatedList(xAddrsNode)

#crea la estructura inicial del mensaje SOAP/XML
def createSkelSoapMessage(soapAction):
    doc = minidom.Document()

    envEl = doc.createElementNS(NS_S, "s:Envelope")

    envEl.setAttribute("xmlns:a", NS_A)  # minidom does not insert this automatically
    envEl.setAttribute("xmlns:d", NS_D)
    envEl.setAttribute("xmlns:s", NS_S)

    doc.appendChild(envEl)

    headerEl = doc.createElementNS(NS_S, "s:Header")
    envEl.appendChild(headerEl)

    addElementWithText(doc, headerEl, "a:Action", NS_A, soapAction)

    bodyEl = doc.createElementNS(NS_S, "s:Body")
    envEl.appendChild(bodyEl)

    return doc

#modifica el mensaje para ser tipo Probe y devuelve el mensaje en formato String.
def createProbeMessage(env):
    doc = createSkelSoapMessage(ACTION_PROBE)

    bodyEl = getBodyEl(doc)
    headerEl = getHeaderEl(doc)

    addElementWithText(doc, headerEl, "a:MessageID", NS_A, env.getMessageId())
    addElementWithText(doc, headerEl, "a:To", NS_A, env.getTo())

    if len(env.getReplyTo()) > 0:
        addElementWithText(doc, headerEl, "a:ReplyTo", NS_A, env.getReplyTo())

    probeEl = doc.createElementNS(NS_D, "d:Probe")
    bodyEl.appendChild(probeEl)
    addTypes(doc, probeEl, env.getTypes())
    addScopes(doc, probeEl, env.getScopes())

    return getDocAsString(doc)

#modifica el mensaje para ser tipo Hello y devuelve el mensaje en formato String.
def createHelloAsProbeMessage(env):
    doc = createSkelSoapMessage(ACTION_HELLO)

    bodyEl = getBodyEl(doc)
    headerEl = getHeaderEl(doc)

    addElementWithText(doc, headerEl, "a:MessageID", NS_A, env.getMessageId())

    if len(env.getRelatesTo()) > 0:
        addElementWithText(doc, headerEl, "a:RelatesTo", NS_A, env.getRelatesTo())
        relatesToEl = headerEl.getElementsByTagNameNS(NS_A, "RelatesTo")[0]
        relatesToEl.setAttribute("RelationshipType", "d:Suppression")

    addElementWithText(doc, headerEl, "a:To", NS_A, env.getTo())

    appSeqEl = doc.createElementNS(NS_D, "d:AppSequence")
    appSeqEl.setAttribute("InstanceId", env.getInstanceId())
    appSeqEl.setAttribute("MessageNumber", env.getMessageNumber())
    headerEl.appendChild(appSeqEl)

    helloEl = doc.createElementNS(NS_D, "d:Hello")
    addTypes(doc, helloEl, env.getTypes())
    addScopes(doc, helloEl, env.getScopes())
    # not very useful functions. Non standard hello message
    addEPR(doc, helloEl, env.getEPR())
    addXAddrs(doc, helloEl, env.getXAddrs())

    addElementWithText(doc, helloEl, "d:MetadataVersion", NS_D, env.getMetadataVersion())

    bodyEl.appendChild(helloEl)

    return getDocAsString(doc)

#devuelve el elemento body del mensaje SOAP/XML
def getBodyEl(doc):
    return doc.getElementsByTagNameNS(NS_S, "Body")[0]

#devuelve el elemento header del mensaje SOAP/XML
def getHeaderEl(doc):
    return doc.getElementsByTagNameNS(NS_S, "Header")[0]

#devuelve todo el Envelope del mensaje SOAP/XML
def getEnvEl(doc):
    return doc.getElementsByTagNameNS(NS_S, "Envelope")[0]

#añade el valor del prefijo del tipo para la referencia xmlns
def addNSAttrToEl(el, ns, prefix):
    el.setAttribute("xmlns:" + prefix, ns)

#convierte doc en string
def getDocAsString(doc):
    stream = StringIO()
    stream.write(doc.toprettyxml())
    return stream.getvalue()

#añade elemento en un nodo del mensaje
def addElementWithText(doc, parent, name, ns, value):
    el = doc.createElementNS(ns, name)
    text = doc.createTextNode(value)
    el.appendChild(text)
    parent.appendChild(el)

#añade el tipo para la referencia xmlns
def addTypes(doc, node, types):
    if types is not None and len(types) > 0:
        envEl = getEnvEl(doc)
        typeList = []
        prefixMap = {}
        for type_ in types:
            ns = type_.getNamespace()
            localname = type_.getLocalname()
            if prefixMap.get(ns) == None:
                prefix = "tds"  # getRandomStr() dn:nvt y wsdp:Device tdn tds
                prefixMap[ns] = prefix
            else:
                prefix = prefixMap.get(ns)
            addNSAttrToEl(envEl, ns, prefix)
            typeList.append(prefix + ":" + localname)
        addElementWithText(doc, node, "d:Types", NS_D, " ".join(typeList))

#añade el scope para la referencia xmlns
def addScopes(doc, node, scopes):
    if scopes is not None and len(scopes) > 0:
        addElementWithText(doc, node, "d:Scopes", NS_D, " ".join([x.getQuotedValue() for x in scopes]))
        if scopes[0].getMatchBy() is not None and len(scopes[0].getMatchBy()) > 0:
            node.getElementsByTagNameNS(NS_D, "Scopes")[0].setAttribute("MatchBy", scopes[0].getMatchBy())

#añade el discovery para la referencia xmlns
def addXAddrs(doc, node, xAddrs):
    if xAddrs is not len(xAddrs) > 0:
        addElementWithText(doc, node, "d:XAddrs", NS_D, " ".join([x for x in xAddrs]))

#añade la direccion para la referencia xmlns
def addEPR(doc, node, epr):
    eprEl = doc.createElementNS(NS_A, "a:EndpointReference")
    addElementWithText(doc, eprEl, "a:Address", NS_A, epr)
    node.appendChild(eprEl)

# -------------HACER LLAMADA CON EL MENSAJE----------------

#    def _sendMsg(self, msg):
# ---->   data = createMessage(msg.getEnv())
# print(data)
#        if msg.msgType() == Message.UNICAST:
#            self._uniOutSocket.sendto(data, (msg.getAddr(), msg.getPort()))
#        else:
#            for sock in self._multiOutUniInSockets.values():
#                sock.sendto(data.encode(), (msg.getAddr(), msg.getPort()))

# --------------OBTENER RESPUESTA Y PARSEAR PROBEMATCHES--------------

#devuelve el mensaje en formato SoapEnvelope a partir del mensaje match recibido
def parseEnvelope(data, ipAddr):
    try:
        dom = minidom.parseString(data)
    except Exception as ex:
        # print >> sys.stderr, 'Failed to parse message from %s\n"%s": %s' % (ipAddr, data, ex)
        return None

    if dom.getElementsByTagNameNS(NS_S, "Fault"):
        # print >> sys.stderr, 'Fault received from %s:' % (ipAddr, data)
        return None

    soapAction = dom.getElementsByTagNameNS(NS_A, "Action")[0].firstChild.data.strip()
    if soapAction == ACTION_PROBE_MATCH:
        return parseProbeMatchMessage(dom)

#mete los valores de AppSequence del header del match en la variable SoapEnvelope
def _parseAppSequence(dom, env):
    nodes = dom.getElementsByTagNameNS(NS_D, "AppSequence")
    if nodes:
        appSeqNode = nodes[0]
        env.setInstanceId(appSeqNode.getAttribute("InstanceId"))
        env.setSequenceId(appSeqNode.getAttribute("SequenceId"))
        env.setMessageNumber(appSeqNode.getAttribute("MessageNumber"))

#convierte el mensaje SOAP/XML del match a formato SoapEnvelope
def parseProbeMatchMessage(dom):
    env = SoapEnvelope()
    env.setAction(ACTION_PROBE_MATCH)

    env.setMessageId(dom.getElementsByTagNameNS(NS_A, "MessageID")[0].firstChild.data.strip())
    env.setRelatesTo(dom.getElementsByTagNameNS(NS_A, "RelatesTo")[0].firstChild.data.strip())
    env.setTo(dom.getElementsByTagNameNS(NS_A, "To")[0].firstChild.data.strip())

    _parseAppSequence(dom, env)

    pmNodes = dom.getElementsByTagNameNS(NS_D, "ProbeMatch")
    for node in pmNodes:
        epr = node.getElementsByTagNameNS(NS_A, "Address")[0].firstChild.data.strip()

        types = []
        typeNodes = node.getElementsByTagNameNS(NS_D, "Types")
        if len(typeNodes) > 0:
            types = getTypes(typeNodes[0])

        scopes = []
        scopeNodes = node.getElementsByTagNameNS(NS_D, "Scopes")
        if len(scopeNodes) > 0:
            scopes = getScopes(scopeNodes[0])

        xAddrs = []
        xAddrNodes = node.getElementsByTagNameNS(NS_D, "XAddrs")
        if len(xAddrNodes) > 0:
            xAddrs = getXAddrs(xAddrNodes[0])

        mdv = node.getElementsByTagNameNS(NS_D, "MetadataVersion")[0].firstChild.data.strip()

        env.getProbeResolveMatches().append(ProbeResolveMatch(epr, types, scopes, xAddrs, mdv))
        env.setTypes(types)
        env.setScopes(scopes)
        env.setEPR(epr)
        env.setXAddrs(xAddrs)
        env.setMetadataVersion(mdv)

    return env

#muestra informacion del SoapEnvelope dado
def showDeviceInfo(env):
    print("-----------------------------")
    print("MessageId: %s" % env.getMessageId())
    print("RelatesTo: %s" % env.getRelatesTo())
    print("To: %s" % env.getTo())
    print("Action: %s" % env.getAction())
    # print("InstanceId: %s" % env.getInstanceId()) 		No se tiene en cuenta
    # print("MessageNumber: %s" % env.getMessageNumber())No se tiene en cuenta
    # print("Reply To: %s" % env.getReplyTo())			No se tiene en cuenta
    # print("SequenceId: %s" % env.getSequenceId()) 		No se tiene en cuenta
    print("Relationship Type: %s" % env.getRelationshipType())
    print("Types: %s" % env.getTypes())
    print("Scopes: %s" % env.getScopes())
    print("EPR: %s" % env.getEPR())
    print("xaddr: %s" % env.getXAddrs())
    print("Metadata Version: %s" % env.getMetadataVersion())
    print("Server version: %s" % env.getServer())
    print("-----------------------------")
#    print("Probe Matches: %s" % env.getProbeResolveMatches())
#    print("-----------------------------")

#ejecuta el descubrimiento WebServices. 1 mensaje probe y otro hello
def runWSDiscovery():

    env = None
    listWSDevices = []
    actionMessage = ""
    #ttype = QName(NS_NET, "NetworkVideoTransmitter")
    ttype = QName(NS_DEV, "Device")
    checkSameDevices = 0

    for x in range(0, MULTICAST_UDP_REPEAT*2):
        if x < MULTICAST_UDP_REPEAT:
            actionMessage = ACTION_PROBE
        else:
            actionMessage = ACTION_HELLO
        # TODO For each transmission of such a message, the value of the [message id] property MUST be the same.
        msg = envelopeWSDiscovery(types=[ttype], action=actionMessage)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # s.setsockopt socket.IP_MULTICAST_TTL es 1 por defecto, es decir para misma subnet
        
        t = round((MULTICAST_UDP_MIN_DELAY + ((MULTICAST_UDP_MAX_DELAY - MULTICAST_UDP_MIN_DELAY) * random.random()))/1000, 2)
        s.settimeout(t*4) #cambiar a 1 o mas si es necesario por timeout
        print(t)
        if msg is not None:
#            for intento in range(0, 4):
            s.sendto(msg.encode(), (MULTICAST_IPV4_ADDRESS, MULTICAST_PORT))
#            s.settimeout(1)
        try:
            while True:
                data, addr = s.recvfrom(BUFFER_SIZE)
                #s.close() # echar OJo aqui
                #print(addr, data)
                env = parseEnvelope(data, addr)
                if not listWSDevices:
                    r = httpx.post(env.getXAddrs()[0], content=MSG_DEV.encode()) # mensaje para obtener servidor SOAP
                    if r.status_code == 200:
                        env.setServer(r.headers['server'])
                        url = urlparse(env.getXAddrs()[0])# anadir HOSTNAME Y PORT
                    listWSDevices.append(env)# anade servicio
                else:
                    for device in listWSDevices:
                        if env.getXAddrs() == device.getXAddrs():
                            checkSameDevices = 1
                            break
                    if checkSameDevices != 1:
                        r = httpx.post(env.getXAddrs()[0], content=MSG_DEV.encode()) # mensaje para obtener servidor SOAP
                        if r.status_code == 200:
                            env.setServer(r.headers['server'])
                        listWSDevices.append(env)# anade servicio
                    checkSameDevices = 0
        except socket.timeout:
            print("End TimeOut")
            s.close()
            pass

    dictWSD= {}
    listWSD= []
#    print("Typ: %s" % listWSDevices[0].getTypes())
# SACO MAS DATOS DEL PUERTO DEL SERVICIO ONVIF y guardo todo en diccionario
    if listWSDevices:
        for device in listWSDevices:
            dicDev={}
            dicDev["Types"]= device.getTypesList()
            dicDev["Scopes"]= device.getScopesList()
            dicDev["EPR"]= device.getEPR()
            dicDev["XAddrs"]= device.getXAddrs()
            dicDev["IPv4"]=re.findall(r'(?:\d{1,3}\.)+(?:\d{1,3})',device.getXAddrs()[0])[0]
            dicDev["Server"]= device.getServer().replace("/"," ")

            listWSD.append(dicDev)#la lista matiene los cambios durante el bucle
            print(os.path.abspath(os.getcwd()))
            pathWSDL=os.path.abspath("libDiscovery/libWSD_Onvif/onvif2/wsdl")
            if "onvif" in device.getScopes().__repr__():#averiguo si es onvif

                mycam = ONVIFCamera(urlparse(device.getXAddrs()[0]).hostname, urlparse(device.getXAddrs()[0]).port, '', '', wsdl_dir=pathWSDL)

                media2_service = mycam.create_media_service()
                dev_service = mycam.create_devicemgmt_service()

                dev_info=dev_service.GetDeviceInformation()
                dicDev["Manufacturer"]= dev_info.Manufacturer
                if dev_info.Model == "IPC":
                    dicDev["Model"]= "IP Camera"
                else:
                    dicDev["Model"]= dev_info.Model
                dicDev["FirmwareVersion"]= dev_info.FirmwareVersion
                dicDev["SerialNumber"]= dev_info.SerialNumber
                dicDev["HardwareId"]= dev_info.HardwareId
                
                cap_info = dev_service.create_type('GetCapabilities')
                cap_info.Category = "All"
                uridev = dev_service.GetCapabilities(cap_info)
                
                if (uridev.Media.StreamingCapabilities.RTP_TCP is False) and (uridev.Media.StreamingCapabilities.RTP_RTSP_TCP is False):#quiza al reves
                    dicDev["StreamSetup"] = []#poner dispositivo onvif
                else:
                    #es camara onvif y protocolo rtp y/o rtsp
                    checkmulti="RTP-Unicast"
                    if uridev.Media.StreamingCapabilities.RTPMulticast:
                        checkmulti="RTP-Multicast"
                    profiles = media2_service.GetProfiles()# obtengo perfiles para obtener uri
                    listStream=[]
                    for profile in profiles:
                        o = media2_service.create_type('GetStreamUri')
                        o.StreamSetup= {
                            "Stream": checkmulti,
                            "Transport": {"Protocol": "RTSP"},
                        }
                        o.ProfileToken = profile.token
                        uri = media2_service.GetStreamUri(o)
                        dic = {'token': profile.token, 'rtsp': uri}# saco la uri y puerto 554 incluido

                        #dicToken={'ProfileToken': profile.token, 'Transport': checkmulti, 'Protocol': "RTSP", 'Encoding': profile.VideoEncoderConfiguration.Encoding, 'Uri': dic["rtsp"]["Uri"]}
                        listStream.append({'ProfileToken': profile.token, 'Transport': checkmulti, 'Protocol': "RTSP", 'Encoding': profile.VideoEncoderConfiguration.Encoding, 'Uri': dic["rtsp"]["Uri"]})
                        dicDev["StreamSetup"] = listStream
                        
#            for typeList in range(len(device.getTypes())):
#                print("Types: %s" % device.getTypes()[typeList].getNamespace())
#                print("Types: %s" % device.getTypes()[typeList].getLocalname())
#            for scopeList in range(len(device.getScopes())):
#                print(device.getScopes()[scopeList].getValue())
#            for addrList in range(len(device.getXAddrs())):
#                print("{}".format(device.getXAddrs()[addrList]))

            showDeviceInfo(device)
    dictWSD["serviciosWSD"] = listWSD
    #print(dictWSD)
    #print(dictWSD["serviciosWSD"][0]["Types"][0]["localname"])recorre diccionario y listas
    y = json.dumps(dictWSD)
    print(y)
    return dictWSD


