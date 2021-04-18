import datetime
import os

#
# DHCP class for isc-dhcp-server
#
# Responsible for managing the ISC DHCP Server database
#
class ndmdhcp():
    def __init__(self, pd):
        self.pd = pd
        self.tmp = pd.tmp
        self.osdetails = { 'raspios': {"dhcpservice":"isc-dhcp-server", "dhcpconfdir":"/etc/dhcp", "dhcpleasedir":"/var/lib/dhcp", "dhcpduser":"root"},\
                           'opensuse-leap': {"dhcpservice":"dhcpd", "dhcpconfdir":"/etc", "dhcpleasedir":"/var/lib/dhcp/db", "dhcpduser":"dhcpd"},\
                           'centos': {"dhcpservice":"dhcpd", "dhcpconfdir":"/etc/dhcp", "dhcpleasedir":"/var/lib/dhcpd", "dhcpduser":"dhcpd"}}
        self.dhsrv = self.osdetails[self.pd.os]['dhcpservice']
        self.dhcpuser = self.osdetails[self.pd.os]['dhcpduser']
        self.dhcpconfdir = self.osdetails[self.pd.os]['dhcpconfdir']
        self.dhcpleasedir = self.osdetails[self.pd.os]['dhcpleasedir']
        self.dhconf = "dhcpd.conf"
        self.dhcpfh = None
        fnsfmt = "{}/{}"
        self.dhfile = fnsfmt.format(self.dhcpconfdir, self.dhconf)
        self.subnetfn = fnsfmt.format(self.dhcpconfdir, "subnet-{}.hosts".format(self.pd.db['cfg']['subnet']))
        self.fnslist = [ self.dhfile, self.subnetfn ]


    def start(self):
        self.pd.xdosystem("systemctl start {}.service".format(self.dhsrv))

    def stop(self):
        self.pd.xdosystem("systemctl stop {}.service".format(self.dhsrv))

    def isrunning(self):
        r = self.pd.xdosystem("systemctl --quiet is-active {}.service".format(self.dhsrv))
        return r.returncode
        
    def resetdyndb(self):
        # Service must be stopped
        print("% Reset DHCP leases database for 'isc-dhcp-server'")
        self.pd.xqdelfile("{}/dhcpd.leases".format(self.dhcpleasedir))
        self.pd.xqdelfile("{}/dhcpd.leases~".format(self.dhcpleasedir))
        return True

    def preinstall(self):
        rfn = ""
        for fn in self.fnslist:
            tmpf = self.pd.xmktmpfn(self.tmp, fn)
            if not os.path.isfile(tmpf): rfn = "{}{} ".format(rfn, os.path.basename(tmpf))
        return rfn
            
    def install(self):
        # dhcp config
        print ("% Install DHCP configuration for 'isc-dhcp-server' from tmp directory '{}' to system directories".format(self.pd.tmp))
        for fn in self.fnslist:
            print("  {}".format(fn))
            self.pd.xqdelfile(self.pd.xmkbakfn(fn))
            self.pd.xqrename(fn, self.pd.xmkbakfn(fn))
            self.pd.xcopy(self.pd.xmktmpfn(self.tmp, fn), fn)
        return True

    def emithost(self, ipaddr, hn):
        # Print DHCP config for this host
        if hn == "": return
        emac = self.pd.db['hosts'][ipaddr]['hostname'][hn]['macaddr']
        eopts = self.pd.db['hosts'][ipaddr]['hostname'][hn]['flags']
        dhcphostopts = self.pd.db['hosts'][ipaddr]['dhcphostopt']
        if (emac != "") and not ("nodhcp" in eopts) and not ("hostsonly" in eopts) and not ("zoneonly" in eopts):
            s1 = "host {} {{\n    hardware ethernet {};\n    fixed-address {};\n".format(hn, emac, ipaddr)
            if dhcphostopts != "":
                els = dhcphostopts.split(',')
                for o in els:
                    if (o in self.pd.db['cfg']['dhcphostopt']) and (self.pd.db['cfg']['dhcphostopt'][o] != ""):
                        s1 = "{}    {}\n".format(s1, self.pd.db['cfg']['dhcphostopt'][o])
                    else:
                        print("% No dhcphostopt config found for option '{}' for host '{}'...ignoring".format(o, hn))
            s1 = '{}    option host-name "{}";\n    ddns-hostname "{}";\n'.format(s1, hn, hn)
            self.subfh.write("{}    }}\n\n".format(s1))

    def prebuild(self):
        return True

    def startbuild(self):
        self.subnetfn = "subnet-{}.hosts".format(self.pd.db['cfg']['subnet'])
        self.subfh = open(self.pd.xmktmpfn(self.tmp, self.subnetfn), 'w')
        self.dhcpfh = open(self.pd.xmktmpfn(self.tmp, self.dhfile), 'w')
        self._writedhcpconf(self.dhcpfh)
        return True

    def endbuild(self):
        self.subfh.close()
        self.dhcpfh.close()
        return True

    def gendnsupdkey(self):
        return True
        if not 'dhcpkey' in self.pd.db['cfg']:
            tsigout = subprocess.check_output("tsig-keygen -a hmac-md5 -r /dev/urandom dhcp-update", shell=True)
            for line in tsigout.decode('utf-8').split("\n"):
                if 'secret' in line:
                    self.pd.db['cfg']['dhcpkey'] = line.split('"')[1]
                    self.pd.dbmodified = True

    def diff(self, fundiff):
        fundiff(self.pd, self.dhfile)
        fundiff(self.pd, self.subnetfn)
        return True

    def chroot(self):
        return False

    def _writedhcpzone(self, fl, zonename):
        fl.write("zone {}. {{\n\
    primary {};\n\
    key dhcp-update;\n\
    }}\n\n".format(zonename, self.pd.db['cfg']['dnsfqdn']))
                
    def _writedhcpconf(self, fh):
        newftime = datetime.datetime.strftime(datetime.datetime.now(), "%c")
        fh.write("# dhcpd.conf created {}\n".format(newftime))
        fh.write("authoritative;\n")
        fh.write("option routers {};\n".format(self.pd.db['cfg']['gateway']))
        fh.write("option subnet-mask 255.255.255.0;\n")
        fh.write("default-lease-time {};\n".format(self.pd.db['cfg']['dhcplease']))
        fh.write("option time-servers {};\n".format(self.pd.db['cfg']['timeserver']))
        fh.write("option domain-name-servers {}, {};\n".format(self.pd.db['cfg']['dnsip'], ', '.join(self.pd.db['cfg']['externaldns'].split(' '))))
        fh.write("ddns-updates on;\nddns-update-style standard;\nignore client-updates;\nupdate-static-leases on;\n")
        fh.write("# What to do if the client sends no hostname: pick first possible string as hostname\n")
        fh.write('ddns-hostname = pick (option fqdn.hostname, option host-name, concat("dhcp-",binary-to-ascii (16,8,"-",substring (hardware,1,6))));')
        fh.write("\n")
        fh.write("key dhcp-update {{\n\
    algorithm hmac-md5;\n\
    secret {};\n\
}}\n\n".format(self.pd.db['cfg']['dhcpkey']))
        self._writedhcpzone(fh, "{}.dhcp".format(self.pd.xipinvert(self.pd.db['cfg']['subnet'])))
        self._writedhcpzone(fh, self.pd.db['cfg']['domain'])
        self._writedhcpzone(fh, "dyn.{}".format(self.pd.db['cfg']['domain']))
        if self.pd.db['cfg']['dhcpglobalopt'] != "": fh.write("{}\n\n".format(self.pd.db['cfg']['dhcpglobalopt']))
        fh.write("subnet {}.0 netmask 255.255.255.0 {{\n".format(self.pd.db['cfg']['subnet']))
        fh.write('    option domain-search "{}", "dyn.{}";\n'.format(self.pd.db['cfg']['domain'], self.pd.db['cfg']['domain']))
        fh.write("    option broadcast-address {}.255;\n".format(self.pd.db['cfg']['subnet']))
        fh.write("    allow duplicates;\n")
        fh.write("    ddns-updates off;\n")
        fh.write("    pool {\n")
        fh.write("        ddns-updates on;\n")
        fh.write("        allow unknown-clients;\n")
        fh.write('        option domain-name "dyn.{}";\n'.format(self.pd.db['cfg']['domain']))
        fh.write('        ddns-rev-domainname "dhcp";\n')
        fh.write("        default-lease-time {};\n".format(self.pd.db['cfg']['dhcplease']))
        fh.write("        max-lease-time {};\n".format(self.pd.db['cfg']['dhcplease']))
        fh.write("        range {};\n".format(self.pd.db['cfg']['dhcpsubnet']))
        fh.write("    }\n}\n")
        fh.write('include "{}/{}";\n'.format(self.dhcpconfdir, self.subnetfn))
        if self.pd.db['cfg']['dhcpinclude'] != "":fh.write('include "{}";\n'.format(self.pd.db['cfg']['dhcpinclude']))
        return True
