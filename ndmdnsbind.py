import datetime
import os
#
# DNS class for Bind9 DNS server
# Responsible for managing the Bind9 database and /etc/hosts
#
class ndmdns():
    def __init__(self, pd):
        # Sort out filenames here
        self.pd = pd
        self.tmp = pd.tmp
        self.etc = "/etc"
        self.resolvconf = "name_servers=127.0.0.1\ndomain={}\nsearch_domains={}\nsearch_domains_append=dyn.{}\n"
        self.osdetails = { 'raspios':       { "bindservice":"bind9", "bindconfdir":"/etc/bind", "bindzonedir":"/etc/bind",\
                                              "bindconffn":"named.conf.options", "bindrundir":"/var/cache/bind", "binduser":"bind" },\
                           'debian':        { "bindservice":"bind9", "bindconfdir":"/etc/bind", "bindzonedir":"/etc/bind",\
                                              "bindconffn":"named.conf.options", "bindrundir":"/var/cache/bind", "binduser":"bind" },\
                           'centos':        { "bindservice":"named", "bindconfdir":"/etc", "bindzonedir":"/var/named/master",\
                                              "bindconffn":"named.conf", "bindrundir":"/var/named", "binduser":"named" }}
#                           'opensuse-leap': { "bindservice":"named", "bindconfdir":"/etc", "bindzonedir":"/var/lib/named/master",\
#                                              "bindconffn":"named.conf", "bindrundir":"/var/lib/named", "binduser":"named" },\
        self.dnsrv = self.osdetails[self.pd.os]['bindservice']
        self.zdir = self.osdetails[self.pd.os]['bindzonedir']
        self.nofile = self.osdetails[self.pd.os]['bindconffn']
        self.bindconfdir = self.osdetails[self.pd.os]['bindconfdir']
        self.bindrundir = self.osdetails[self.pd.os]['bindrundir']
        self.binduser = self.osdetails[self.pd.os]['binduser']
        fnsfmt = "{}/{}"
        hfn = "hosts"
        zfn = "db.{}".format(self.pd.db['cfg']['domain'])
        rzfn = "db.{}".format(pd.db['cfg']['subnet'])
        bzfn = "db.ndm-blocked.zone"
        blfn = "ndm-bind-blocked.conf"
        dyfn = "db.dyn.{}".format(self.pd.db['cfg']['domain'])
        rdyfn = "db.{}.dhcp".format(self.pd.db['cfg']['subnet'])

        xhfile = fnsfmt.format(self.etc, hfn)
        xzfile = fnsfmt.format(self.zdir, zfn)
        xrzfile = fnsfmt.format(self.zdir, rzfn)
        xbzfile = fnsfmt.format(self.zdir, bzfn)
        xdynfile = fnsfmt.format(self.zdir, dyfn)
        xrdynfile = fnsfmt.format(self.zdir, rdyfn)
        self.xnofile = fnsfmt.format(self.bindconfdir, self.nofile)
        xblfile = fnsfmt.format(self.bindconfdir, blfn)
                                  #full-file-spec, file-handle, dont-delete-unless
        self.dnsfns = { 'hosts':        [xhfile,    None, False],\
                        'domzone':      [xzfile,    None, False],\
                        'revdomzone':   [xrzfile,   None, False],\
                        'blockzone':    [xbzfile,   None, False],\
                        'blockinclude': [xblfile,   None, False],\
                        'dynzone':      [xdynfile,  None, True],\
                        'revdynzone':   [xrdynfile, None, True]}

        # indexes into dnsfns
        self.ffs = 0       #Full file spec
        self.fh = 1        #File handle
        self.dontdel = 2   #Don't delete unless reset

    def start(self):
        self.pd.xdosystem("systemctl start {}.service".format(self.dnsrv))

    def stop(self):
        self.pd.xdosystem("systemctl stop {}.service".format(self.dnsrv))

    def isrunning(self):
        r = self.pd.xdosystem("systemctl --quiet is-active {}.service".format(self.dnsrv))
        return r.returncode
        
    def resetdyndb(self):
        # Service must be stopped already
        print("% Reset dynamic DNS configuration for 'bind9'")
        self.pd.xqdelfile(self.dnsfns['dynzone'][self.ffs])
        self.pd.xqdelfile("{}.jnl".format(self.dnsfns['dynzone'][self.ffs]))
        self.pd.xqdelfile(self.dnsfns['revdynzone'][self.ffs])
        self.pd.xqdelfile("{}.jnl".format(self.dnsfns['revdynzone'][self.ffs]))
        return True

    def emithost(self, ipaddr, hn):
        if hn == "": return
        emac = self.pd.db['hosts'][ipaddr]['hostname'][hn]['macaddr']
        eopts = self.pd.db['hosts'][ipaddr]['hostname'][hn]['flags']
        # domain forward file
        if not ("hostsonly" in eopts) and not ("dhcponly" in eopts):
            s1 = "{:<15} IN A     {}\n".format(hn, ipaddr)
            self.dnsfns['domzone'][self.fh].write(s1)
        # domain reverse file
        if (self.pd.db['cfg']['subnet'] in ipaddr) and not ("hostsonly" in eopts) and not ("zoneonly" in eopts) and not ("dhcponly" in eopts):
            self.dnsfns['revdomzone'][self.fh].write("{:<3} IN PTR {}.{}.\n".format(ipaddr.split('.')[3], hn, self.pd.db['cfg']['domain']))
        # hosts
        if not ("zoneonly" in eopts) and not ("dhcponly" in eopts):
            if ("nodomain" in eopts):
                s1 = "{:<15} {:<40}\n".format(ipaddr, hn)
            else:
                s2 = "{}.{}".format(hn, self.pd.db['cfg']['domain'])
                s1 = "{:<15} {:<40} {}\n".format(ipaddr, s2, hn)
            self.dnsfns['hosts'][self.fh].write(s1)

    def emitcname(self, ipaddr, hn):
        self.dnsfns['domzone'][self.fh].write("{:<15} IN CNAME {}\n".format(ipaddr, hn))

    def prebuild(self):
        if not os.path.isfile("/sbin/tsig-keygen") and not os.path.isfile("/usr/sbin/tsig-keygen"):
            self.pd.xperrorexit("? Cannot find /sbin/tsig-keygen")

    def startbuild(self):
        newdatesn = self._gendatesn()
        for i in self.dnsfns:                      # delete old tmp files and open new files for writing
            self.pd.xqdelfile(self.pd.xmktmpfn(self.tmp,self.dnsfns[i][self.ffs]))
            self.dnsfns[i][self.fh] = open(self.pd.xmktmpfn(self.tmp, self.dnsfns[i][self.ffs]), 'w')
        self._doheaders(newdatesn)
        self._writebindconf()
        # Write blocked-domain.zone
        self._writezheader(self.dnsfns['blockzone'][self.fh], self._gendatesn(), datetime.datetime.strftime(datetime.datetime.now(), "%c"), "")
        self.dnsfns['blockzone'][self.fh].write("@      IN A       127.0.0.1\n*      IN A       127.0.0.1\n")
        # Write dynamic forward and reverse zones
        self._writezheader(self.dnsfns['dynzone'][self.fh], self._gendatesn(),\
                           datetime.datetime.strftime(datetime.datetime.now(), "%c"),\
                           "dyn.{}".format(self.pd.db['cfg']['domain']))
        self._writezheader(self.dnsfns['revdynzone'][self.fh], self._gendatesn(),\
                           datetime.datetime.strftime(datetime.datetime.now(), "%c"),\
                           "{}.dhcp".format(self.pd.xipinvert(self.pd.db['cfg']['subnet'])))
        return True

    def endbuild(self):
        rze = self.pd.db['cfg']['dhcpsubnet'].split(" ")
        slow = rze[0].split('.')[3]
        shigh = rze[1].split('.')[3]
        self.dnsfns['revdomzone'][self.fh].write("\n$GENERATE {}-{} $ CNAME $.{}.dhcp.\n".format(slow, shigh, self.pd.xipinvert(self.pd.db['cfg']['subnet'])))
        for i in self.dnsfns:
            self.dnsfns[i][self.fh].close()
        self._writeblocklist()

    def preinstall(self):
        rfn = ""
        for fn in self.dnsfns:
            tmpf = self.pd.xmktmpfn(self.tmp, self.dnsfns[fn][self.ffs])
            if not os.path.isfile(tmpf): rfn = "{}{} ".format(rfn, os.path.basename(tmpf))
        return rfn
            
    def install(self):
        print ("% Install DNS configuration for 'bind9' from tmp directory '{}' to system directories".format(self.pd.tmp))
        for i in self.dnsfns:
            if not self.dnsfns[i][self.dontdel] or not os.path.isfile(self.dnsfns[i][self.ffs]):
                print("  {}".format(self.dnsfns[i][self.ffs]))
                self.pd.xqdelfile(self.pd.xmkbakfn(self.dnsfns[i][self.ffs]))
                self.pd.xqrename(self.dnsfns[i][self.ffs], self.pd.xmkbakfn(self.dnsfns[i][self.ffs]))
                self.pd.xcopy(self.pd.xmktmpfn(self.tmp, self.dnsfns[i][self.ffs]), self.dnsfns[i][self.ffs])
        os.chmod(self.zdir, 0o2775)
        # Handle named.conf/named.conf.options
        if not os.path.isfile("{}.orig".format(self.xnofile)):
            self.pd.xqrename(self.xnofile, "{}.orig".format(self.xnofile))
        flist = [self.xnofile] #In case more are invented ;)
        for fn in flist:
            print("  {}".format(fn))
            self.pd.xqdelfile(self.pd.xmkbakfn(fn))
            self.pd.xqrename(fn, self.pd.xmkbakfn(fn))
            self.pd.xcopy(self.pd.xmktmpfn(self.tmp, fn), fn)
        self._doresolvconf()
        return True

    def gendnsupdkey(self):
        if not 'dhcpkey' in self.pd.db['cfg']:
            r = self.pd.xdosystem("tsig-keygen -a hmac-md5 -r /dev/urandom dhcp-update")
            for line in r.stdout.decode('utf-8').split("\n"):
                if 'secret' in line:
                    self.pd.db['cfg']['dhcpkey'] = line.split('"')[1]
                    self.pd.dbmodified = True
                    break
        return True

    def diff(self, fundiff):
        for i in self.dnsfns:
            fundiff(self.pd, self.dnsfns[i][self.ffs])
        return True

    def chroot(self):
        # From https://wiki.debian.org/Bind9
        # NOT VETTED / TESTED in new config
        if os.path.isdir("/var/bind9/chroot"): self.pd.xperrorexit("? chroot appears to already be established")
        # Change /etc/default/bind9 OPTIONS="-u bind -t /var/bind9/chroot"
        self.pd.xdosystem('sed -i \'s/OPTIONS="-u bind"/OPTIONS="-u bind -t \/var\/bind9\/chroot"/\' /etc/default/bind9')
        for dir in [ "etc", "dev", "var/cache/bind", "var/run/named" ]:
            self.pd.xdosystem("mkdir -p /var/bind9/chroot/{}".format(dir))
        os.chmod("/var/bind9/chroot/etc", 0o2775)    # Needed for dynamic updates (.jnl files)
        self.pd.xdosystem("mknod /var/bind9/chroot/dev/null c 1 3 ; chmod 666 /var/bind9/chroot/dev/null")
        self.pd.xdosystem("mknod /var/bind9/chroot/dev/random c 1 8 ; chmod 666 /var/bind9/chroot/dev/random")
        self.pd.xdosystem("mknod /var/bind9/chroot/dev/urandom c 1 9 ; chmod 666 /var/bind9/chroot/dev/urandom")
        self.pd.xdosystem("mv /etc/bind /var/bind9/chroot/etc")
        self.pd.xdosystem("ln -s /var/bind9/chroot/etc/bind /etc/bind")
        self.pd.xdosystem("cp /etc/localtime /var/bind9/chroot/etc/")
        #    self.pd.xdosystem("chown bind:bind /var/bind9/chroot/etc/bind/rndc.key") # Not needed. Done during bind install
        for dir in [ "cache/bind", "run/named" ]:
            self.pd.xdosystem("chmod 775 /var/bind9/chroot/var/{}; chgrp bind /var/bind9/chroot/var/{}".format(dir, dir))
        if os.path.isdir("/etc/rsyslog.d"):
            if not os.path.isfile("/etc/rsyslog.d/bind-chroot.conf"):
                self.pd.xdosystem('echo "\$AddUnixListenSocket /var/bind9/chroot/dev/log" > /etc/rsyslog.d/bind-chroot.conf')
        return True

    def _writezheader(self, fl, newdatesn, newftime, origin):
        # Writes the zone header in a zone file
        sorigin = "$ORIGIN {}.\n".format(origin) if origin != "" else ""
        sdomain = "{}.".format(origin) if origin != "" else "@"
        szname = origin if origin != "" else self.pd.db['cfg']['domain']
        headstrings = ["; {} {} created {}\n".format(newdatesn, szname, newftime),\
                   "$TTL	86400    ; 24 hours. could have been written as 24h or 1d\n",\
                   sorigin,\
                   "{}  IN    SOA {}. root.{}. (\n".format(sdomain, self.pd.db['cfg']['hostfqdn'], self.pd.db['cfg']['domain']),\
                   "		     {} ; serial\n".format(newdatesn),\
                   "		     28800      ; refresh 8H\n",\
                   "		     7200       ; retry   2H\n",\
                   "		     604800     ; expire  1W\n",\
                   "		     86400      ; minimum 1D\n",\
                   "		     )\n",\
                   "       IN NS      {}.\n".format(self.pd.db['cfg']['dnsfqdn']),\
                   "       IN MX      10 {}.\n".format(self.pd.db['cfg']['mxfqdn'])]
        for s1 in headstrings:
            if s1 != "": fl.write(s1)

    def _writeblocklist(self):
        # Generate the file of blocked domains
        with open(self.pd.xmktmpfn(self.tmp, self.dnsfns['blockinclude'][self.ffs]), 'w') as flb:
            flb.write("// These domains are configured by ndm to be blocked by DNS\n\n")
            if self.pd.db['cfg']['blockdomains'] != "":
                for els in self.pd.db['cfg']['blockdomains'].split(' '):
                    flb.write('zone "{}" {{ type master; forwarders {{ }}; notify no; file "{}"; }};\n'.format(els.strip(), self.dnsfns['blockzone'][self.ffs]))

    def _writezonedef(self, fl, zonename, zonefile):
        # Write the zone definition in named.conf.options
        fl.write('\nzone "{}" in {{\n\
     type master;\n\
     file "{}";\n\
     allow-update {{ key dhcp-update; }};\n\
     forwarders {{ }};\n\
     notify no;\n\
}};\n'.format(zonename, zonefile))

    def _writebindconf(self):
        # Writes named.conf.options, which has bind config info and zone declarations
        if self.pd.db['cfg']['externaldns'] != "":
            odns = ""
            for edns in self.pd.db['cfg']['externaldns'].split():
                odns = "{} {};".format(odns, edns.strip()) if odns != "" else "{};".format(edns.strip())
        else:
            odns = "1.1.1.1; 1.0.0.1;"
        with open(self.pd.xmktmpfn(self.tmp, self.nofile), 'w') as fl:
            sinternals = "" if self.pd.db['cfg']['internals'] == "" else "{};".format(self.pd.db['cfg']['internals'])
            fl.write('\n\
// Consider adding the 1918 zones here, if they are not used in your\n\
// organization\n\
//include "/etc/bind/zones.rfc1918";\n\
\n\
    acl internals {{ 127.0.0.0/8; {}.0/24; {} }};\n\
\n\
options {{\n\
    directory "{}";\n\
    pid-file "/var/run/named/named.pid";\n\
    session-keyfile "/var/run/named/session.key";\n\
    listen-on port {} {{ {}; 127.0.0.1; }};\n\
    listen-on-v6 {{ none; }};\n\
    allow-query {{ internals; }};\n\
    allow-query-cache {{ internals; }};\n\
    allow-recursion {{ internals; }};\n\
    forwarders {{ {} }};\n\
}};\n\n'.format(self.pd.db['cfg']['subnet'], sinternals, self.bindrundir, self.pd.db['cfg']['dnslistenport'], self.pd.db['cfg']['myip'], odns))
            fl.write('\n\
key dhcp-update {{\n\
    algorithm hmac-md5;\n\
    secret "{}";\n\
}};\n\
\n\
logging {{\n\
	category lame-servers {{ null; }};\n\
	category edns-disabled {{ null; }};\n\
	category resolver {{ null; }}; // this will kill resolver error msgs\n\
}};\n\
\n\
controls {{\n\
	 inet 127.0.0.1 allow {{ localhost; }} keys {{ rndc-key; }};\n\
}};\n\n\
include "{}/rndc.key";\n'.format(self.pd.db['cfg']['dhcpkey'], self.bindconfdir))
            # Domain and reverse domain statements
            self._writezonedef(fl, "{}.in-addr.arpa".format(self.pd.xipinvert(self.pd.db['cfg']['subnet'])), "{}/db.{}".format(self.zdir, self.pd.db['cfg']['subnet']))
            self._writezonedef(fl, "{}".format(self.pd.db['cfg']['domain']), "{}/db.{}".format(self.zdir, self.pd.db['cfg']['domain']))
            self._writezonedef(fl, "{}.dhcp".format(self.pd.xipinvert(self.pd.db['cfg']['subnet'])), "{}/db.{}.dhcp".format(self.zdir, self.pd.db['cfg']['subnet']))
            self._writezonedef(fl, "dyn.{}".format(self.pd.db['cfg']['domain']), "{}/db.dyn.{}".format(self.zdir, self.pd.db['cfg']['domain']))
            fl.write('\ninclude "{}";\n'.format(self.dnsfns['blockinclude'][self.ffs]))  # Include db.ndm-blocked
            if self.pd.db['cfg']['dnsinclude'] != "": fl.write('\ninclude "{}";\n'.format(self.pd.db['cfg']['dnsinclude']))  # site-local include

    def _gendatesn(self):
        newdatesn = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d")
        # Get current serial number from current active zonefile
        try:
            with open(self.dnsfns['domzone'][self.ffs]) as f: line = f.readline()
        except:
            line = "; 2019041901 mydomain.net"
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
        # dns forward zone
        self._writezheader(self.dnsfns['domzone'][self.fh], newdatesn, newftime, self.pd.db['cfg']['domain'])
        # dns reverse zone
        self._writezheader(self.dnsfns['revdomzone'][self.fh], newdatesn, newftime, "{}.in-addr.arpa".format(self.pd.xipinvert(self.pd.db['cfg']['subnet'])))
        # hosts file
        flh = self.dnsfns['hosts'][self.fh]
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
                rcf.write(self.resolvconf.format(self.pd.db['cfg']['domain'], self.pd.db['cfg']['domain'], self.pd.db['cfg']['domain']))
                print("% Running resolvconf to create new /etc/resolv.conf")
                r = self.pd.xdosystem("resolvconf -u")
                for line in r.stdout.decode('utf-8'):
                    if line != "": print (line)
