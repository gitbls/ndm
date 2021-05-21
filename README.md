ndm DNS and DHCP Server subnet configuration manager

## Overview

**ndm** greatly simplifies configuring and managing DNS and DHCP services for a small home or business network with prescriptive, but customizable and extensible, configuration. ndm can run on any small Linux system, such as a Raspberry Pi, or any other supported Linux distribution.

While most, if not all routers provide DNS and DHCP services, ndm has some significant advantages over using your router for these services:

* The ndm configuration is **router independent**. You can replace your router and still have exactly the same DNS configuration, and all your computers at their proper IP addresses. Good luck trying to do this if you switch router vendors!
* The ndm configuration is **host independent** as well. If your ndm-hosting system dies, you can quickly and easily recreate your configuration (as long as you've backed up the ndm database).
* ndm lets you **easily assign specific IP addresses** to specific devices. For instance, the system running ndm/DNS/DHCP servers will need a static IP address. You may want to assign specific IP addresses to other devices on your network. Some people find that pre-defining IP addresses for all devices on the network creates a comforting feeling.
* ndm configures **dynamic DNS** for your network. Systems that do not have statically assigned IP addresses are automatically added to DNS. [Don't confuse this with ddns on the internet. That's completely different.]
* **Easily name your own home network domain**.
* The ndm database and configuration is maintained in a **single, portable file**, so it's easy to backup and restore.
* The network configuration and IP address assignments are **easy to manage and view**.

Have questions about ndm? Please don't hesitate to ask in the Issues section of this github. If you don't have a github account (so can't post an issue/question here), please feel free to email me at: [gitbls@outlook.com](mailto:gitbls@outlook.com).

If you find ndm useful, please consider starring it to help me understand how many people are using it. Thanks!

**ndm capabilities include:**

* **Maintain and easily update** DNS and DHCP configuration files and /etc/hosts 
    * ndm eliminates the need to hand-edit DNS or DHCP configuration files
* Easily establish your own **LAN-local domain name**
    * Change the default '.me' with `sudo ndm config --domain newdom.com`
* Devices can either have **statically assigned or dynamic IP addresses**
    * MAC addresses for statically-assigned devices are configured in ndm
    * Devices with dynamically assigned IP addresses are automatically added to DNS when they come onto the network
* **Per-host DHCP attributes** can be set (isc-dhcp-server only)
    * Easily configure for PXE boot, special DNS servers, or other per-host specific customizations
* **Easy-to-use command line** to add/modify/list/delete preconfigured device IP addresses
* **List on the terminal or export the ndm database** in ndm import format (See "Importing a network database" below)
* Building and installing the configuration files is a **simple two-step process** (build followed by install) to enable you to ensure config file correctness and/or do custom updates if desired before the configuration files are moved into the system directories.
* Includes a basic **DNS domain block list** feature
* Leverages **industry-proven** bind9, isc-dhcp-server, or dnsmasq for DNS and DHCP services

With the V2 release, ndm continues to support bind9 for DNS and isc-dhcp-server for DHCP. In addition, ndm now supports dnsmasq for both DNS and DHCP. If you choose to use dnsmasq for one of DNS or DHCP, ndm sets both DNS and DHCP to be served by dnsmasq. In addition, DHCP configuration can be disabled via `--dhcp none`.

**What relevant features are not in V2?**

Since my specific network is fully supported, I'm good :) :) However, there are a few obvious enhancements that I expect to look into. These include:

* Only /24 networks are supported. This includes 192.168.n.* for any 'n'.
* No IPV6 support. A bit more work, but should be done.
* ndm is fully tested and supported on RasPiOS (Stretch and Buster). Other distros may require minor work (config file names/locations). Let me know what OS are important for you.
* Nameserver failover, although this can be done with an external script. See section "Nameserver failover" below.
* chroot configuration for the bind DNS server has been removed. Please let me know if this is important for you.

## Installation on RasPiOS

Installation consists of a few simple steps:

* **Copy ndm** to the system where you are planning to run ndm/DNS/DHCP
* Optionally **install a timeserver** on your LAN
* **Decide** if you're using bind/isc-dhcp-server (more full-featured) or dnsmasq (for both DHCP and DNS). See the section "How do I choose between bind9/isc-dhcp-server and dnsmasq" later in this document.
* **Install** the DHCP and DNS servers
* **Configure ndm** 
* **Add hosts** to the ndm database
* Build, review, **test**, and install the DNS and DHCP configurations

### **Copy ndm to your system**
* `sudo curl -L https://raw.githubusercontent.com/gitbls/ndm/master/EZndmInstaller | bash`
    * EZndmInstaller simply copies the files to /usr/local/bin and then displays some helpful getting started information.
    * If you want to install ndm to a different directory, download EZndmInstaller and start it with `sudo EZndmInstaller /dir/for/install`. 'sudo' only required if needed for /dir/for/install write access.
    * **OR** Copy and execute this bash command
```
for f in ndm ndmdnsbind.py ndmdnsmasq.py ndmdhcpisc.py ndmdhcpnone.py ; do curl -L https://raw.githubusercontent.com/gitbls/ndm/master/$f -o /usr/local/bin/$f ; done
```

### Timeserver installation (optional)

If you don't have a **network time server** on your network, it is generally optimal, but not required, to install and configure *chrony* (or *ntp*) so that your network clients have a time server available.

This can be done on the same system on which you're running ndm/DNS/DHCP:

```
sudo apt-get install chrony
```

sudo edit /etc/chrony/chrony.conf and add these two lines to the end of the file, adjusted as needed for your configuration:

```
allow xx.yy.xx.0/24           # Enables your local subnet to access the server
bindaddress ip.ad.dr.ss       # The IP address of the computer chronyd installed on
```

If you already have a time server on your network, you'll need to know its IP address (which should be a statically assigned IP address).

### Install bind and isc-dhcp-server (or, alternatively, dnsmasq):

* `sudo apt-get update`
* `sudo apt-get install bind9 isc-dhcp-server` **OR** `sudo apt-get install dnsmasq`
* `sudo systemctl stop isc-dhcp-server` &mdash; For some bizarre reason, the installer starts an unconfigured DHCP server. Stop it so it can be configured.
* `sudo systemctl stop bind9` &mdash; Bind9 starts as well, completely unconfigured. Not very useful, so stop it.
* If you installed dnsmasq, it has the same issue, so stop it: `sudo systemctl stop dnsmasq`

I **strongly** recommend that you disable the DHCP server (`sudo systemctl disable isc-dhcp-server`) until you're ready to go live with it.

You'll still be able to start and stop the service, but this will ensure that the service doesn't *accidentally* start after a reboot, possibly wreaking havoc on your network. When you're ready to go live with it you can enable and start it with `sudo systemctl enable --now isc-dhcp-server`.

* sudo edit /etc/default/isc-dhcp-server to set the INTERFACESV4 setting, e.g., INTERFACESv4=eth0

* There are no edits required for /etc/default/bind9 or /etc/default/dnsmasq

### Configure ndm/DNS/DHCP host with static IP Address

Linux provides several different ways to configure the network, and any of them will work, of course, if properly configured. I recommend using *dhcpcd* or *systemd-networkd* to configure the network on the system that is hosting ndm/DNS/DHCP. systemd-networkd is the most lightweight, and easy-to-configure mechanism for the static IP use case. Here are the steps:

* **Enable systemd-networkd:** `sudo systemctl enable systemd-networkd`
* **Disable dhcpcd:** `sudo systemctl disable dhcpcd`
* **Disable NetworkManager if installed:** `sudo systemctl disable NetworkManager`
* **Create /etc/systemd/network/10-eth0.network** as follows. Change the *Address* and *DNS* items to be the desired IP static address. Change the *Gateway* item to be your network gateway address, and edit the *Domains* and *NTP* items as appropriate. See the [systemd-networkd documentation](https://www.freedesktop.org/software/systemd/man/systemd.network.html) for further details:

```
[Match]
Name=eth0

[Network]
DHCP=No
LinkLocalAddressing=no
IPv4LL=false
Address=192.168.42.2/24
Gateway=192.168.42.1
DNS=192.168.42.2
Domains=mydomain.com
NTP=192.168.42.2
```

If you choose to use dhcpcd, sudo edit /etc/dhcpcd.conf to include a static definition for your ethernet (adjusting for your configuration as appropriate):

```
interface eth0
static ip_address=192.168.42.2/24
static routers=192.168.42.1
static domain_name_servers=192.168.42.2
```

Reboot, verify your network configuration, and then proceed with ndm configuration.

### Configure ndm

The examples in this document use subnet 192.168.42.0/24. Adjust this as appropriate for your network configuration. It also assumes that computer *mypi* is at 192.168.42.2 and is running *ntp* or *chrony* (time service) and a mail server as well as ndm/DNS/DHCP.

**NOTE:** ndm does not require a mail server. ndm will default the mail server to your ndm/DNS/DHCP server. If you have a mail server, change it with `ndm config --mxfqdn mymailserver.mydomain.com`

* Create and configure the database

    * **Create** the ndm database, **/etc/dbndm.json**: `sudo ndm config --create` &mdash; This will create the database and add the ndm/DNS/DHCP host to it.
    * One additional configuration command completes the basic configuration. Adjust as needed for your network. *Gateway* and *timeserver* must be given as IP addresses. Similarly, *externaldns* and *dhcpsubnet* are specified as two IP addresses separated by a comma (no space):

```
    sudo ndm config --dns dnsmasq \
           --dhcp dnsmasq \
           --domain mynet.net \
           --gateway ip.ad.dr.es \
           --timeserver ip.ad.dr.es \
           --externaldns 1.1.1.1,1.0.0.1 \
           --dhcprange 192.168.42.xx,192.168.42.yy
```

* Display and review the ndm configuration: `sudo ndm config --list`

* You must also specify which DNS and DHCP servers to use with the `--dns` and `--dhcp` switches. Legal values are
    * **DNS:**&nbsp;&nbsp;&nbsp;`--dns bind` and `--dns dnsmasq`
    * **DHCP:**&nbsp;`--dhcp isc-dhcp-server`, `--dhcp dnsmasq`, or `--dhcp none`
    * Your ndm host is now configured for basic operation!

### Add hosts

Add your hosts, either via a set of ndm commands or by importing a properly formatted network database. See "Importing a network database" and "Day-to-day management tasks" below. Note that ndm will automatically add the hostname of the system on which it is running to the database.

* `sudo ndm add 192.168.42.4 --hostname mypitest --mac nn:nn:nn:nn:nn:nn --note "RPi for testing"`

See below for full details for the add command.

### Build, Install, and Test

* **Build** the DNS and DHCP configuration files into a directory in /tmp: `sudo ndm build`
* **Install** the DNS and DHCP configuration files into the system directories: `sudo ndm install`
* **Start** the DNS and DHCP servers: `sudo systemctl start bind9; sudo systemctl start isc-dhcp-server` OR `sudo systemctl start dnsmasq` **NOTE:** Please read the section "Introducing a new DHCP Server onto the Network" at the end of this README **BEFORE** you start your new DHCP server.
* Resolve any errors identified in the system log

## When do I *need* to do an ndm build/install?

Any changes you make to the `sudo ndm config` settings or add/modify/delete a host require that you do `sudo ndm build` and `sudo ndm install` for them to take effect in the running system. Since the configuration build and install are separate operations, you can use `sudo ndm diff` to view the configuration file changes between the current and possible new version.

## Day-to-day management tasks

### Adding a host and update the running configuration

* `sudo ndm add 192.168.42.3 --mac nn:nn:nn:nn:nn:nn --hostname pc2` &mdash; Adds a new host named *pc2* to the ndm database. *pc2* has IP address 192.168.42.3 and the specified MAC Address. If *pc2* is configured to request an IP address via dhcp, it will always get 192.168.42.3
* `sudo ndm build` &mdash; Builds the updated config files, but doesn't install them into the system
* `sudo ndm diff` &mdash; (optional). Displays the differences between the current in-use config files and the newly-created config files. Use `sudo ndm diff | less` if needed.
* `sudo ndm install` &mdash; Installs the updated config files into the system and stops/restarts the DNS and DHCP servers to load the new configuration

Of course you can add multiple hosts before doing a build and install.

### Adding an external host to /etc/hosts

* `sudo ndm add 12.10.2.1 --hostname example.some.com --hostsonly --nodomain` &mdash; Adds the entry to /etc/hosts. This is useful for names that need to be made available early in the boot process.
    * As with the first example, an `sudo ndm build` and `sudo ndm install` must be performed for this to take effect.

### Adding hosts with multiple network adapters (isc-dhcp-server only)

* `sudo ndm add 192.168.42.12 --mac 4c:01:44:77:11:10 --hostname eerobase --note "eero in wiring closet"` &mdash; Eero sends multiple DHCP requests on different MAC addresses. I found that they can operate using the same IP address, so I use these two commands to force that. The second entry is only in the dhcpd config file, and not present in the DNS zone or /etc/hosts files.
* `sudo ndm add 192.168.42.12 --mac 4c:01:44:77:11:22 --hostname eerobasex --dhcponly` &mdash; This is the second MAC address on the eero. This enables the DHCP server to respond to it, but the hostname is not made visible in DNS. Note that the second MAC address must have a different hostname than the first one.

### Deleting a host

* `sudo ndm delete 192.168.42.17` &mdash; Deletes the entry with IP address 192.168.42.17 from the database.
* As with the first example, an `sudo ndm build` and `sudo ndm install` must be performed.

### Modifying a host

* `sudo ndm modify 192.168.42.3 --note "New server 2018-12-04" --mac mm:mm:mm:mm:mm:mm`
* As with the first example, an `sudo ndm build` and `sudo ndm install` must be performed.

### Changing the IP address for a host

* `sudo ndm reip 192.168.42.7 --newip 192.168.42.3` &mdash; Changes the IP address for all hostnames associated with the old IP address. `sudo ndm build` and `sudo ndm install` must be performed.

## Detailed command information

This section includes some discussion about each command including useful hints.

**add &mdash;** Add a new hostname to the database

You only need to add the host to the database if the host will have a static IP address assigned, or it requires special DHCP handling, such as PXE booting.

To add a simple device to the database, use 

`sudo ndm add 192.168.42.4 --hostname mypitest --mac nn:nn:nn:nn:nn:nn `

The MAC address is necessary so that the DHCP server can assign it a fixed address. It is not necessary for any devices that have dynamically assigned IP addresses from the pool.

The switches to the *add* command provide flexibility and control over the host entry. Every ndm command has help like this available. 

```
bash$ sudo ndm add --help
usage: ndm add [-h] [--cname] [--db DB] [--dhcphostopt DHCPHOSTOPT]
               [--dhcponly] [--hostname HOSTNAME] [--hostsonly] [--mac MAC]
               [--nodhcp] [--nodomain] [--note NOTE] [--zoneonly]
               ip

positional arguments:
  ip                    New host IP address

optional arguments:
  -h, --help            show this help message and exit
  --cname               Put this entry in DNS config files as a CNAME
  --db DB               Specify alternate config file name
  --dhcphostopt DHCPHOSTOPT
                        Name of dhcphostopt to add to this host's DHCP entry
  --dhcponly            Only put this host in dhcpd.conf (no hosts or DNS
                        config entries)
  --hostname HOSTNAME   New host name
  --hostsonly           Only put this host in hosts file (no dhcpd.conf or DNS
                        config entries)
  --mac MAC             New host MAC address
  --nodhcp              Don't add host to dhcpd.conf
  --nodomain            Don't add the domain name to this entry; It's already
                        fully qualified
  --note NOTE           Note text for new hostname
  --zoneonly            Only put thishost in DNS config files (no dhcpd.conf
                        or hosts file)
```

To add a CNAME record, use: `sudo ndm add cnamestring --hostname cnamevalue.mydomain.com. --cname`. (note the trailing ".") This will create a CNAME record for *cnamestring*, and it's value is *cnamevalue.mydomain.com.*

The --note switch is handy for per-device information that you might care about such as:
* Where is the device located?
* When was it put into service?
* Any special information such as: what depends on this host or IP address?

**build &mdash;** Build the DNS and DHCP config files from the database

The files are created in a temporary directory and are not in use until you `sudo ndm install` (which briefly stops/restarts the DHCP and DNS servers). The temporary directory is /tmp/ndm.*username* (typically will be /tmp/ndm.root), but  can be changed with the --tmp switch. If you change the temporary directory for the *build* command, you also must change it for the *diff* and *install* commands.

**config &mdash;** Manage the ndm configuration database

The *config* command controls the site configuration database, and is used to do bulk import of host definitions. See the section "Importing a network database" below for details on bulk importing. An *ndm config* command with no switches defaults to `sudo ndm config --list`.

**delete &mdash;** Delete an entry from the database

deletes a host IP from the database. If an IP address has multiple names associated with it, you can use the --hostname switch to delete a specific hostname. Deleting the last (or only) hostname on an IP address deletes the IP address.

**diff &mdash;** Diff the system config files against the newly-created config

Use the *diff* command to verify the changes in the newly-created config files against the files already installed in the system. Pipe the result into `less` if you'd like to have the output paginated for viewing.

**install &mdash;** Install the configuration files created by the *build* command

installs the generated configuration. **Note:** No running system configuration files are changed until an `sudo ndm install` is done.

The `sudo ndm install --reset` command resets all the DHCP and DNS configurations to the just-initialized state. All dynamic zone definitions are removed, as are all DHCP leases. This is primarily for testing, but can be used with care on live networks. Best practice is to have all hosts with statically-assigned DHCP-requested addresses. 

**list &mdash;** List all entries in the database.

If --dump is specified, the output is in *ndm import* format, which can be loaded into ndm with the `sudo ndm config --importnet` command.

**modify &mdash;** Modify an existing host entry

You must specify the IP address. When renaming the hostname associated with an IP address, use the --newhostname switch. If an IP address has multiple hostnames associated with it, the --hostname switch must be used to specify which hostname to modify.

The --mac and --note switches and the various flags are attached to the hostname. The --dhcphostopt switch is attached to the IP address, so a hostname is not required when changing this setting.

**reip &mdash;** Change the IP address for all hosts assigned to the given IP address.

**show &mdash;** Display an entry or set of entries

The argument can be an IP address (must fully match), part of a MAC address, or part of a host name. In the latter two cases, all matching entries are shown.

## Domain name behavior

When properly configured, you can refer to hosts on your network by their hostname, or by their fully qualified domain name. Both will work. For instance, a host named *server1* in a domain named *mydomain.com* can be refered to as server1, or as server1.mydomain.com.

This behavior requires that all the clients in the network have mydomain.com in their domain search list. ndm sets this up for dynamically-assigned hosts (details are sent via the DHCP response), but if the computer has an IP address assigned without the use of ndm (e.g., by using systemd-networkd or dhcpcd), /etc/resolv.conf must be set manually on such systems.

The DNS database that ndm establishes is completely independent of any DNS database on the public internet. For instance, if you have a public domain *mydomain.com*, then looking up server1.mydomain.com on the public internet will most likely refer to a public IP address, while looking up server1.mydomain.com on your internal network would refer to a private (e.g., non-public) address on your LAN, such as 192.168.42.5.

This is the desired behavior since most routers don't support "hair-pinning" (going out to the internet and coming back in).

## Configuring a dhcphostopt (isc-dhcp-server only)

Use *dhcphostopt* to configure PXE or other host-specific DHCP options. For each dhcphostopt setting, ndm adds the dhcphostopt substitution string to the host entry in the DHCP subnet hosts file.

For example: 

`sudo ndm config --dhcphostopt 'PXE=next-server 192.168.42.3; filename "pxelinux.0";'`

`sudo ndm config --dhcphostopt "DNSX=option domain-name-servers 192.168.42.4, 1.0.0.1;"`

If you want to change the text of a dhcphostopt simply re-enter the command with the new replacement string. Leave the replacement string blank if you want to delete a dhcphostopt (e.g., `ndm config --dhcphostopt "DNSX="`). Don't forget the trailing semicolon as in the examples, as these are required by the DHCP config file syntax.

Apply the dhcphostopt setting as desired to specific hosts:

`sudo ndm modify 192.168.42.17 --dhcphostopt PXE`

`sudo ndm modify 192.168.42.18 --dhcphostopt PXE,DNSX`

If a dhcphostopt has been applied to a host but there is no dhcphosthopt configuration for the specified dhcphostopt, ndm will emit a warning, but continue.

As always, after a host configuration has been modified, do an `sudo ndm build` and `sudo ndm install` to instantiate it onto the running system.

## Using the --bindoptions switch (bind9 only)

ndm generates highly prescriptive configuration files. One of the bind configuration files, named.conf.options, has a section in it named *options*. These options are generated by ndm based on the supplied configuration.

However, these options are a subset of all the options that bind supports. The `--bindoptions` switch lets you provide additional option lines for the *options* section. The `--bindoptions` switch takes an argument, which is a filename. The file contains a list of statements that are inserted into the *options* section.

ndm does NO syntax checking on these statements; They must be syntactically correct bind9 options statements, each ending with a semi-colon. They are inserted into the *options* section **as is**, except that ndm prepends 4 spaces to the lines if they do not start with 4 spaces. This is done for readability in named.conf.options.

[The complete set of bind9 options are listed here.](https://bind9.readthedocs.io/en/latest/reference.html#options-statement-grammar)


## Importing a network database

Use the command `sudo ndm config --import` to import a properly formatted database. The importer does not do much syntax checking, so be sure to check the results very carefully. The import database format is

IPaddr,MACaddr,hostname,flags,Note,dhcphostopt,

For instance

    192.168.42.2,nn:nn:nn:nn:nn:nn,mypi,Pi next to the router,PXE,
    192.168.42.3,nn:nn:nn:nn:nn:nn,mywin,My Windows desktop,,

The flags correspond to the command-line switches of the *add command*. When included in the network database import file, I suggest prefixing them with a plus sign for readability. For example:

192.168.42.5,nn:nn:nn:nn:nn:nn,www,+zoneonly,

* *nodhcp*: Don't put this host in dhcpd.conf. Use this on the second and subsequent hostnames on the same IP address.
* *cname*: This is a CNAME (DNS alias) and goes in the domain zone file only (implies *zoneonly*) (bind9 only)
* *dhcponly*: Only put this host in dhcpd.conf (do not add to /etc/hosts or any DNS files). You might want to use this for a host that has a dhcp-assigned address, but you don't want the hostname in DNS
* *hostsonly*: Only put this host in /etc/hosts (do not add to dhcpd.conf or any DNS files). You can use this for hosts that are outside your domain, but you want DNS to resolve them (e.g., special internet addresses)
* *zoneonly*: Only put this host in the DNS zone file (do not add to dhcpd.conf or /etc/hosts)
* *nodomain*: Don't add the domain name to the host in /etc/hosts. Use this if you have an FQDN name for a host outside your domain.

Once the network database has been successfully imported, do a `sudo ndm build` and `sudo ndm install`.

## Using ndm with multiple LAN subnets or a VPN (bind only)

By default, bind9 is configured to only accept requests from the host on which the name server is running, and any hosts in the subnet specified by --subnet. If you're using multiple LAN subnets or have a VPN installed that will use your DNS server for name services, you must specify the additional subnets using the `sudo ndm config --internals` command. 

For instance, if my VPN provides client IP addresses in subnet 10.42.10.0/24, I would use `sudo ndm config --internals 10.42.10.0/24`, and ndm will add that subnet to the list of subnets allowed to query the name server.

## Nameserver Failover

ndm currently doesn't support (configure) highly available DNS or DHCP servers. However, the complete network database configuration is kept in a single file (/etc/dbndm.json). I use a manual failover technique with a hot standby. My standby checks for updates to the database at regular intervals, and updates it's copy of the database as needed. While the DNS server on the hot standby can always be running, the DHCP server cannot. Only start it if the primary fails.

Here's the script I use, which must be run with sudo:


    #!/bin/bash

    #
    # Prior maindns dbndm.json: /var/local/maindns-dbndm.json
    # Prior hotstandby dbndm.json: /var/local/hotstandby-dbndm.json
    #
    # ** for testing if diff /rpi/maindns/etc/dbndm.json /rpi/maindns/etc/dbndm.json
    if diff /var/local/maindns-dbndm.json /maindns-etc/dbndm.json ##> /dev/null 2&>1
    then
        logger "ndmsync dbndm.json unchanged"
    else
        logger "ndmsync dbndm.json has changed; Updating..."
        [ -f /var/local/hotstandby-dbndm.json ] && rm -f /var/local/hotstandby-dbndm.json
        cp /etc/dbndm.json /var/local/hotstandby-dbndm.json
        cp /maindns-etc/dbndm.json /etc
        [ -f /var/local/maindns-dbndm.json ] && rm -f /var/local/maindns-dbndm.json
        cp /etc/dbndm.json /var/local/maindns-dbndm.json
        # Need to change:
        # dnsip, myip, timeserver, hostfqdn, dnsfqdn, mxfqdn, any dhcphostopts referring to maindns
        myip=$(hostname -I)
        myfqdn="$(hostname).mydomain.me"
        ndm config --dnsip $myip --myip $myip --timeserver $myip
        ndm config --dnsfqdn $myfqdn --hostfqdn $myfqdn --mxfqdn $myfqdn
        #ndm config --dhcphostopt "x1=option domain-name-servers 192.168.42.7, $myip;" #Example only!
        ndm build
        ndm install
        logger "ndmsync dbndm.json updated"
    fi

This is ideal for a network with all hosts having DHCP-server assigned static addresses, and can provide a "hot standby" DNS and DHCP server.

It should work OK on small networks without many dynamically-assigned DHCP addresses. However, if there are new devices joining and leaving the network wanting dynamically-assigned DHCP addresses, there could likely be issues.

On the other hand, if you require 100% availability, that's not possible without more work. Please let me know if you're interested in this; it would help inspire me to do something about it.


## Using ndm with Pi-Hole

This section is relatively old, and may be out of date.

If you want to run ndm and bind/dhcpd on the same system as Pi-Hole, here are the steps. Basic testing has been done with both running on the same system. Pi-Hole generally encourages dnsmasq, so this is only recommended if you have a hankering for a fully transparent, DNS/DHCP subsystem that can be managed with command lines and scripts, rather than editing config files. It's all personal preference!

* Install and configure Pi-Hole per the Pi-Hole documentation
* Install and configure bind, dhcpd, and ndm per this document
* Modify the ndm configuration to use a different TCP port for DNS: `sudo ndm config --dnslistenport newport`. Pi-Hole will listen on port 53 (the default DNS port), so select another port less than 1024.
* `sudo ndm build` and `sudo ndm install` the updated configuration
* Configure any hosts with static IP address as documented above.
* In the Pi-Hole configuration, establish an external DNS server: TBD
* Test. Just like I need to do before this is released :)

Things of note:

* Under piHole advanced DNS settings, clear the "never forward non-fqdns" and "never forward reverse-lookups for IP ranges". 
* In PiHole specify the DNS server as 127.0.0.1#portnum or ipaddr#portnum (use a '#' to separate the IP address and port)
* I have not yet found a way to set domain search for dyn.domain except by editing resolv.conf


## Why use ndm and not Pi-Hole?

Pi-Hole is a great system, and has a ton of features. It's a bit more complex than I prefer: I wanted a simple, lightweight, command-line oriented management utility. If you want a GUI, you should have a look at Pi-Hole.

## How do I choose betwen bind9/isc-dhcp-server and dnsmasq?

Both systems (bind9/isc-dhcp-server and dnsmasq) are great. This is not really a question of one being better than the other. 
By using ndm to configure your DNS and DHCP servers, you'll rarely, if ever, have to interact directly with the DHCP and DNS servers themselves.

I've been using bind/dhcpd since my Linux day 1 20+ years ago, and I've never had a problem with it, other than tending to the configuration files, meaning...I have never had any incentive to change. Rather, I just needed a better tool for managing the configuration, and ndm is it.

If you like dnsmasq...great! ndm supports dnsmasq! There are some features that bind9/isc-dhcp-server support that dnsmasq either doesn't support, or ndm has not yet implemented yet. These are noted in this document.

if you haven't used either DNS/DHCP system on your network and are looking to start, bind9/isc-dhcp-server/ndm has more features implemented. You may find them useful in the fullness of time! 

But, if you'd prefer to use dnsmasq, that's fine, too. ndm works with dnsmasq now.

Lastly, there are other DNS and DHCP servers available on Linux. ndm V2 can easily accomodate these with only a small amount of development. What services are important to you?

## Troubleshooting

ndm's mission is to produce correct configuration files for DNS/DHCP servers. If either of these services have a problem, check the system logs (via the `sudo journalctl` command) for hints as to the cause. Once the service error has been identified, it is generally straightforward from the context to trace the issue back to the incorrect ndm config setting.

Known configuration issues:

* ndm is sometimes unable to determine the host IP address. If ndm cannot determine the host IP address, an error will be printed. You can define these with:`sudo ndm config --dnsip my.ip.ad.dr --myip my.ip.ad.dr` for the static IP address that you have assigned and configured for this host.

* /etc/resolv.conf changes unexpectedly on the ndm/DNS/DHCP server. This might occur if you are using dhcpcd or NetworkManager, and have established alternate network configurations. DNS and DHCP are server services, so the host running them should only have one network configuration, the static IP address. ndm updates /etc/resolvconf.conf so that everything works as expected, but if another subsystem modifies /etc/resolvconf.conf or /etc/resolv.conf, things could be "interesting".

* If you need to ndm to reconfigure resolvconf: `sudo rm -f /etc/resolvconf.conf.ndm` will cause ndm to regenerate a correct /etc/resolvconf.conf. ndm also saves the original /etc/resolvconf.conf in /etc/resolvconf.conf-orig.ndm. The `resolvconf` program uses /etc/resolvconf.conf to generate /etc/resolv.conf. ndm runs resolvconf to generate the correct /etc/resolv.conf based on your ndm name server configuration.

## Introducing a new DHCP Server onto the Network

Without careful planning, it can be VERY VERY BAD to have two DHCP servers enabled on the same network at the same time, as it can lead to multiple hosts with the same IP address. This is especially true if new devices are joining/leaving the network frequently, so typically less of a problem on a home network.

The key issue with bringing up a new and different DHCP server is that having two DHCP servers on the network at the same time can lead to unpredictable behavior (at best) or a disaster.

There are two basic approaches:

* **Cold Turkey:** Shut down the old DHCP server and bring up the new one
* **Simultaneous operation** with **non-overlapping DHCP address pools**

In the **Cold Turkey** approach, do as much testing as possible without bringing the new DHCP server online for any extended period of time. Starting and stopping the DHCP server to validate the configuration file is typically OK (except, as noted, on a very active network with many new devices joining/leaving). Once you have confirmed that the configuration files are correct, you can shut down/disable the old DHCP server and start the new one.

In the **simultaneous operation** approach, make sure that the two DHCP servers are assigning IP Addresses from different, non-intersecting address pools. For instance, if your router is assigning addresses in the 192.168.xx.100-192.168.xx.200 range, you could configure your ndm-powered DHCP server to use .201-.255. The problem with this approach is that you don't know beforehand which DHCP server will respond to a request, but probably OK for a relatively quick test.

With either approach, you may find it desirable to shorten the DHCP lease time during the transition period. Most DHCP servers are configured such that hosts with DHCP-assigned addresses try to renew their lease after half the DHCP lease time has expired. This is really a question of how long you want to wait for all the DHCP-assigned hosts to have their leases renewed by the new server. I typically shorten it to a few hours and monitor the logs carefully. Once I'm satisfied that everything is good, I extend the lease time back to 24 hours (86400 seconds).

Once you've decided on and implemented your transition strategy, you can start the ndm-powered DHCP server. 

The system log is your friend. Use `sudo journalctl | grep dhcp | less` to see all of the DHCP address requests and responses, and `sudo journalctl -f | grep dhcp` to watch the DHCP action in real time. 

When you're satisfied with the operation, reconfigure the ndm DHCP server's address pool if needed (`sudo ndm config --dhcpsubnet`), and then `sudo systemctl restart isc-dhcp-server` (or `sudo systemctl restart dnsmasq` if you're using dnsmasq) to start it.

Don't forget to enable the services to start automatically when you're all set to go!

* `sudo systemctl enable bind9` **AND** `sudo systemctl enable isc-dhcp-server`
* OR `sudo systemctl enable dnsmasq` if you're using dnsmasq

## Distro-specific Notes

This section includes a few notes on using ndm on various Linux distributions

### Supported OS Distros

`ndm` currently supports the following OS Distros:

* Raspbian Stretch
* RasPiOS Buster
* Debian Buster
* Ubuntu (tested on 21.04, other releases *should* work as well)

Any distro not listed above has not been tested and will not work. If your system is "Debian-like", you could try using `sudo ndm config --os debian`. It really depends on the distro, since the location of system configuration files can and does vary across distros. 

### Other distros

`ndm` is mostly distro-independent and can be easily extended. Virtually all the work in supporting an additional distro is in configuring the correct filenames and directories for the bind/named and DHCP config files. Let me know what distro you're interested in!
