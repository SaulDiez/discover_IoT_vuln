BUFFER_SIZE = 65507
APP_MAX_DELAY = 500  # miliseconds
DP_MAX_TIMEOUT = 5000  # 5 seconds

_NETWORK_ADDRESSES_CHECK_TIMEOUT = 5

MULTICAST_PORT = 3702
MULTICAST_IPV4_ADDRESS = "239.255.255.250"

MULTICAST_UDP_REPEAT = 4
MULTICAST_UDP_MIN_DELAY = 50
MULTICAST_UDP_MAX_DELAY = 150    #250
MULTICAST_UDP_UPPER_DELAY = 500

NS_A = "http://schemas.xmlsoap.org/ws/2004/08/addressing"
NS_D = "http://schemas.xmlsoap.org/ws/2005/04/discovery"
NS_S = "http://www.w3.org/2003/05/soap-envelope"
NS_DEV = "https://schemas.xmlsoap.org/ws/2006/02/devprof"
NS_NET = "http://www.onvif.org/ver10/network/wsdl"

ACTION_HELLO = "http://schemas.xmlsoap.org/ws/2005/04/discovery/Hello"
ACTION_PROBE = "http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe"
ACTION_PROBE_MATCH = "http://schemas.xmlsoap.org/ws/2005/04/discovery/ProbeMatches"

ADDRESS_ALL = "urn:schemas-xmlsoap-org:ws:2005:04:discovery"

MSG_DEV = """<?xml version="1.0"encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
 <SOAP-ENV:Body>
 <tds:GetDeviceInformation/>
 </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
