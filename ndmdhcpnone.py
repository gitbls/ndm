import datetime
import os

#
# DHCP class for none
#
# Responsible for managing the dnsmasq DHCP data 
#
class ndmdhcp():
    def __init__(self, pd):
        self.pd = pd

    def start(self):
        return True

    def stop(self):
        return True

    def isrunning(self):
        return False
        
    def resetdyndb(self):
        return True

    def emithost(self, ipaddr, hn):
        return True

    def prebuild(self):
        return True

    def startbuild(self):
        return True

    def endbuild(self):
        return True

    def preinstall(self):
        return ""

    def install(self):
        return True

    def diff(self, fundiff):
        return True

    def chroot(self):
        return True

    def gendnsupdkey(self):
        return True

