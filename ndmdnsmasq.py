import datetime
import os

#
# DNS class for dnsmasq. If dnsmasq selected, it is for both DNS and DHCP
#
# Responsible for managing the dnsmasq configuration file
# Also maintains /etc/hosts
#
class ndmdns():
    def __init__(self, pd):
        # Sort out filenames here
        self.pd = pd
        self.tmp = pd.tmp
        self.etc = "/etc"
        self.dnsrv = "dnsmasq"
        fnsfmt = "{}/{}"
        hfn = "hosts"
        self.hfh = None
        self.xhfile = fnsfmt.format(self.etc, hfn)
        self.configfile = "/etc/dnsmasq.conf"
        self.cflist = [self.configfile, self.xhfile]
        self.cfh = None

    def start(self):
        self.pd.xdosystem("systemctl start {}.service".format(self.dnsrv))

    def stop(self):
        self.pd.xdosystem("systemctl stop {}.service".format(self.dnsrv))

    def isrunning(self):
        r = self.pd.xdosystem("systemctl --quiet is-active {}.service".format(self.dnsrv))
        return r.returncode
        
    def resetdyndb(self):
        # Service must be stopped
        # dnsmasq doesn't support dynamic DNS in the same manner than bind9 does so nothing to do here?
        return True

    def emithost(self, ipaddr, hn):
        if hn == "": return
        emac = self.pd.db['hosts'][ipaddr]['hostname'][hn]['macaddr']
        eopts = self.pd.db['hosts'][ipaddr]['hostname'][hn]['flags']
        # hosts file
        if not ("zoneonly" in eopts) and not ("dhcponly" in eopts):
            if ("nodomain" in eopts):
                s1 = "{:<15} {:<40}\n".format(ipaddr, hn)
            else:
                s2 = "{}.{}".format(hn, self.pd.db['cfg']['domain'])
                s1 = "{:<15} {:<40} {}\n".format(ipaddr, s2, hn)
            self.hfh.write(s1)

    def emitcname(self, ipaddr, hn):
        self.cfh.write("cname={},{}\n".format(ipaddr, hn))
        return True

    def prebuild(self):
        return True

    def startbuild(self):
        newdatesn = self._gendatesn()
        self.pd.xqdelfile(self.pd.xmktmpfn(self.tmp,self.configfile)) 
        self.cfh = open(self.pd.xmktmpfn(self.tmp, self.configfile), 'w')
        self.pd.dnsmasqfh = self.cfh
        self.hfh = open(self.pd.xmktmpfn(self.tmp, "hosts"), 'w')
        self._doheaders(newdatesn)
        return True

    def endbuild(self):
        self._writeblocklist()
        if self.pd.db['cfg']['dnsinclude'] != "":
            self.cfh.write("\n# DNS include file\nconf-file={}\n".format(self.pd.db['cfg']['dnsinclude']))
        if self.pd.db['cfg']['dhcpinclude'] != "":
            self.cfh.write("# DHCP include file\nconf-file={}\n".format(self.pd.db['cfg']['dhcpinclude']))
        self.hfh.close()
        self.cfh.close()

    def preinstall(self):
        rfn = ""
        for fn in self.cflist:
            tmpf = self.pd.xmktmpfn(self.tmp, fn)
            if not os.path.isfile(tmpf): rfn = "{}{} ".format(rfn, os.path.basename(tmpf))
        return rfn
        
    def install(self):
        print ("% Installing DNS configuration from tmp directory '{}' to system directories".format(self.pd.tmp))
        for fn in self.cflist:
            print("  {}".format(fn))
            self.pd.xqdelfile(self.pd.xmkbakfn(fn))
            self.pd.xqrename(fn, self.pd.xmkbakfn(fn))
            self.pd.xcopy(self.pd.xmktmpfn(self.tmp, fn), fn)
        self._doresolvconf()
        return True

    def gendnsupdkey(self):
        return True

    def diff(self, fundiff):
        fundiff(self.pd, self.configfile)
        fundiff(self.pd, "/etc/hosts")

    def chroot(self):
        return False

    def _writeblocklist(self):
        # Generate the file of blocked domains
        fh = self.cfh
        if self.pd.db['cfg']['blockdomains'] != "":
            fh.write("\n# DNS-blocked domains\n")
            for i in self.pd.db['cfg']['blockdomains'].split(' '):
                fh.write("address=/{}/127.0.0.1\n".format(i.strip()))

    def _gendatesn(self):
        newdatesn = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d")
        # Get current serial number from current active zonefile
        try:
            with open(self.configfile) as f: line = f.readline()
        except:
            line = "# 2019041901 mydomain.net"
        try:
            cursn = line.split()[1][-2:]  # last 2 digits of s/n in file
            t1 = int(cursn) +1
            fdatesn = line.split()[1][0:8] # first 8 digits of s/n in file
        except:
            t1 = 1
            cursn = fdatesn = "20190419"
        if t1 > 99 or newdatesn != fdatesn: t1 = 1
        newdatesn = newdatesn + "{:02d}".format(t1)
        return newdatesn

    def _doheaders(self, newdatesn):
        newftime = datetime.datetime.strftime(datetime.datetime.now(), "%c")
        edns = ""
        #
        # Initial lines of dnsmasq.conf
        #
        # domain=, mx-host, port
        #
        flh = self.cfh
        flh.write("# dnsmasq configuration built on {}\n\n".format(datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S")))
        flh.write("# DNS server configuration\n")
#        flh.write("bind-interfaces\n")
        flh.write("no-resolv\n")
        flh.write("no-poll\n")
        flh.write("cache-size=10000\n")
        flh.write("domain={}\n".format(self.pd.db['cfg']['domain']))
        flh.write("local=/{}/\n".format(self.pd.db['cfg']['domain']))
        flh.write("expand-hosts\n")
        flh.write("mx-host={}\n".format(self.pd.db['cfg']['mxfqdn']))
        if self.pd.db['cfg']['dnslistenport'] != "53": flh.write("port={}\n".format(self.pd.db['cfg']['dnslistenport']))
        flh.write("interface={}\n".format(self.pd.db['cfg']['netdev']))
        if self.pd.db['cfg']['dhcp'] == "none":
            flh.write("no-dhcp-interface={}\n".format(self.pd.db['cfg']['netdev']))
        else:
            flh.write("#dhcp-authoritative\n")
        # flh.write("#all-servers\n")
        for edns in self.pd.db['cfg']['externaldns'].split():
            flh.write("server={}\n".format(edns.strip()))
        # hosts file
        flh = self.hfh
        flh.write("#/etc/hosts created {}\n#\n".format(newftime))
        flh.write("# hosts         This file describes a number of hostname-to-address\n")
        flh.write("#               mappings for the TCP/IP subsystem.  It is mostly\n")
        flh.write("#               used at boot time, when no name servers are running.\n")
        flh.write("#               On small systems, this file can be used instead of a\n")
        flh.write("#               name server.\n# Syntax:\n#    \n")
        flh.write("# IP-Address    {:<40} Short-Hostname\n#\n".format("Fully-Qualified-Hostname"))
        return True

    def _doresolvconf(self):
        if not os.path.isfile("/etc/resolvconf.conf"): return True #Skip if not needed
        if not os.path.isfile("/etc/resolvconf.conf.ndm"):
            print("% Saving /etc/resolvconf.conf as /etc/resolvconf.conf.ndm")
            self.pd.xcopy("/etc/resolvconf.conf", "/etc/resolvconf.conf.ndm")
            print("% Writing new /etc/resolvconf.conf")
            with open("/etc/resolvconf.conf", 'w') as rcf:
                rcf.write("nameservers=127.0.0.1\ndomain={}\nsearch_domains={}\n".format(self.pd.db['cfg']['domain'], self.pd.db['cfg']['domain']))
            print("% Running resolvconf to create new /etc/resolv.conf")
            r = self.pd.xdosystem("resolvconf -u")
            for line in r.stdout.decode('utf-8'):
                if line != "": print (line)
#
# DHCP class for dnsmasq
#
# Responsible for managing the dnsmasq DHCP data 
#
class ndmdhcp():
    def __init__(self, pd):
        self.pd = pd
        self.tmp = pd.tmp
        # leases file is /var/lib/misc/dnsmasq.leases
        self.leases = "/var/lib/misc/dnsmasq.leases"
        self.dhsrv = "dnsmasq"
        fnsfmt = "{}/{}"

    def start(self):
        self.pd.xdosystem("systemctl start {}.service".format(self.dhsrv))

    def stop(self):
        self.pd.xdosystem("systemctl stop {}.service".format(self.dhsrv))

    def isrunning(self):
        r = self.pd.xdosystem("systemctl --quiet is-active {}.service".format(self.dhsrv))
        return r.returncode
        
    def resetdyndb(self):
        # Service must be stopped
        self.pd.xqdelfile(self.leases)
        return True

    def preinstall(self):
        # Handled by DNS
        return ""

    def install(self):
        # Handled by DNS 
        return True

    def emithost(self, ipaddr, hn):
        # Print DHCP config for this host
        if hn == "": return
        emac = self.pd.db['hosts'][ipaddr]['hostname'][hn]['macaddr']
        eopts = self.pd.db['hosts'][ipaddr]['hostname'][hn]['flags']
        if (emac != "") and not ("nodhcp" in eopts) and not ("hostsonly" in eopts) and not ("zoneonly" in eopts):
            self.pd.dnsmasqfh.write("dhcp-host={},{},{}\n".format(emac,ipaddr,hn))
        return True

    def prebuild(self):
        return True

    def startbuild(self):
        self._writedhcpconf(self.pd.dnsmasqfh)
        return True

    def endbuild(self):
        # File close handled by DNS
        return True

    def diff(self, fundiff):
        return True

    def chroot(self):
        return True

    def gendnsupdkey(self):
        return True

    def _writedhcpconf(self, fh):
        rze = self.pd.db['cfg']['dhcpsubnet'].split(" ")
        fh.write("\n# DHCP server configuration\n")
        fh.write("dhcp-range={},{},{}\n".format(rze[0],rze[1],self.pd.db['cfg']['dhcplease']))
        fh.write("dhcp-option=option:router,{}\n".format(self.pd.db['cfg']['gateway']))
        fh.write("dhcp-option=option:ntp-server,{}\n".format(self.pd.db['cfg']['timeserver']))
        fh.write("\n# DHCP hosts\n")
