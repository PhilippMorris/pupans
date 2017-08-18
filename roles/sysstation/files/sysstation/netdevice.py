import os
import untangle
import tempfile
import uuid


class NetConnection():


    # Get lldp output to lldp_current.xml file or to lldp_normal.xml

    def __init__(self, start):
        if start:
            self.Name = "Null"
            self.Description = "Null"
            self.Port = "Null"
        else:
            tempFileName = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
            xml = self.lldp_info(tempFileName)
            os.remove(tempFileName)
            self.Name = self.get_name(xml)
            self.Description = self.get_descr(xml)
            self.Port = self.get_port(xml)


    def lldp_info(self, file):
        os.system("lldpctl -f xml > " + file)
        xml = untangle.parse(file)
        return xml

    # def lldp_from_file (self, file):
    #     xml = untangle.parse(file)
    #     return xml

    def get_name(self, xmlobject):
        try:
            name = xmlobject.lldp.interface.chassis.name.cdata
            return name
        except:
            return None

    # Get device model

    def get_descr(self, xmlobject):
        try:
            descr = xmlobject.lldp.interface.chassis.descr.cdata
            return descr
        except:
            return None

    # Get device port

    def get_port(self, xmlobject):
        try:
            port = xmlobject.lldp.interface.port.id.cdata
            return port
        except:
            return None

    # Get VLAN
    def get_vlan(self, xmlobject):
        try:
            vlan = xmlobject.lldp.interface.vlan['vlan-id']
            return vlan
        except:
            return None

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


# Refresh station network param class

class RefreshStation(object):
    def get_link_speed(self):
        a = os.popen("ethtool eth0 | grep Speed").read()
        dict = a.split(': ')
        speed = dict[1].split('M')
        return speed[0]

    # Get refresh station link carrier bool (True, False)

    def get_carrier(self):
        a = os.popen("ethtool eth0 | grep Link").read()
        dict = a.split(': ')
        dict1 = dict[1].split("\n")
        if dict1[0] == "yes":
            return True
        else:
            return False
