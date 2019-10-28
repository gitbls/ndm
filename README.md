ndm Bind9 and isc-dhcp-server subnet configuration management

## Overview

**ndm** dramatically simplifies the configuration and management of DNS (bind9, also referred to as bind or dns) and DHCP (isc-dhcp-server, also referred to as dhcpd) services for a small home or business network with a prescriptive, but customizable and extensible, configuration. ndm can run on any small Linux box, such as a Raspberry Pi, or any other supported Linux distribution. While most, if not all routers provide DNS and DHCP services, ndm has some significant advantages over using your router for these services:

* The ndm configuration is router-independent. You can replace your router and still have exactly the same DNS configuration, and all your computers at their proper IP addresses.
* The ndm configuration is host independent as well. If your Linux box dies, you can quickly and easily recreate your configuration (as long as you've backed up the ndm database). (You do backup, don't you?).
* Speaking of proper addresses, ndm lets you easily assign specific IP addresses to specific devices. For instance, the system running ndm/bind/dhcpd will need a fixed IP address. You may want to assign specific IP addresses to other devices on your network. Some people find that pre-defining the IP addresses of all devices on the network creates a comforting feeling.
* ndm fully configures dynamic dns for your network. Systems that do not have statically assigned IP addresses are automatically added to dns.
* Easily name your own home network domain
* The ndm configuration is maintained in a single, portable file, so it's easy to backup and restore.

**ndm capabilities include**

* Maintain and easily update dns and dhcpd configuration files and /etc/hosts 
    * ndm eliminates the need to hand-edit any dns or dhcp config files
* Easily establish your own local domain name
    * The easily-changed default is '.me'
* Devices can either have statically assigned or dynamic IP addresses
    * Devices with dynamically assigned IP addresses are automatically added to dns when they come onto the network
* Per-host dhcp attributes can be set
    * Easily configure for PXE boot, special dns servers, or other per-host specific customizations.
* Preconfigured device IP addresses can be added, modified, listed, or deleted from the command line
* List or export the ndm database in an ndm import format (See "Importing a network database" below)
* Building and installing the configuration files is a two-step process to enable you to ensure their correctness and/or do custom updates if desired
* Includes a basic blocked dns domain list feature
* Leverages industry-proven bind9 and isc-dhcp-server for dns and dhcp services
* Can provide dns and dhcp services for Pi-Hole (See section "Using ndm with Pi-Hole")

**What relevant features are not in V1?**

Since my specific network is fully supported, I'm good :) :) However, there are a few obvious enhancements that I expect to look into. These include:

* Only /24 networks are supported. This includes 192.168.n.* for any 'n'. 
* No IPV6 support
* V1 is only tested and supported on two Linux distros: Raspberry Pi with Raspbian Stretch and openSUSE Leap 15
* Nameserver failover. Looking into it.

## Installing on Raspbian

Review the sections at the end of the document to learn about installing on other Distros. Perform the following steps for Raspbian:

* Copy ndm to your system somewhere in your path. I use /usr/local/bin. The ndm database is **/etc/dbndm.json**

* If you don't have a network time server on your network, install and configure chrony or ntp so that your network clients have a time server available. `sudo apt-get install chrony`. If you already have a time server on your network, you'll need to know it's IP address.

* Install bind and isc-dhcp-server:

    * `sudo apt-get update`
    * `sudo apt-get install bind9 isc-dhcp-server`
    * `sudo systemctl stop isc-dhcp-server` - For some bizarre reason, the installer starts an unconfigured dhcp server. Stop it so it can be configured.

* Edit /etc/default/isc-dhcp-server to set the INTERFACESV4 setting, e.g., INTERFACESv4=eth0

* Linux provides several different ways to configure the network, and any of them will work, of course, if properly configured. I recommend using dhcpcd or systemd-networkd to configure the network on the system that is hosting bind/dhcpd/ndm. systemd-networkd is the most lightweight, and easy-to-configure mechanism for the static IP use case. Here are the steps:

    * Enable systemd-networkd: `sudo systemctl enable systemd-networkd`
    * Disable dhcpcd: `sudo systemctl disable dhcpcd`
    * If you have installed NetworkManager, disable it: `sudo systemctl disable NetworkManager`
    * Create /etc/systemd/network/10-eth0.network as follows (this file can be downloaded URLURLhere). Change the *Address* and *DNS* items to be the desired IP static address. Change the *Gateway* item to be your network gateway address, and edit the *Domains* and *NTP* items as appropriate. See the [systemd-networkd documentation](https://www.freedesktop.org/software/systemd/man/systemd.network.html) for further details:

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
* If you choose to use dhcpcd, sudo edit /etc/dhcpcd.conf to include a static definition for your ethernet (adjusting for your configuration as appropriate):

```
interface eth0
static ip_address=192.168.42.2/24
static routers=192.168.42.1
static domain_name_servers=192.168.42.2
```


* Reboot, verify your network configuration, and then proceed with creating the ndm configuration.

## Creating the ndm configuration

Create the database and configure it. The examples in this document use subnet 192.168.42.0/24. Adjust this as appropriate for your network configuration. It also assumes that computer mypi is at 192.168.42.2 and is running ntp (time service) and a mail server as well as dns/dhcp/ndm.

* Create and configure the database

    * Create the ndm database, /etc/dbndm.json: `ndm config --create --myip 192.168.42.2`. See the "Troubleshooting" section for details on why you need to provide the host's IP address.
    * The remainder of these commands establish the configuration. Adjust as needed for your network. *Subnet*, *gateway*, *externaldns*, and *timeserver* must be given as IP addresses. Likewise, the *dhcpsubnet* must be provided as a range of IP addresses on your network. *dnsfqdn* and *mxfqdn* must be provided as fully qualified domain names (hostname.domain).
 
        * `ndm config --subnet 192.168.42 --dhcpsubnet "192.168.42.64 192.168.42.128"`
        * `ndm config --gateway 192.168.42.1 --timeserver 192.168.42.2 --externaldns 1.1.1.1,1.0.0.1 `
        * `ndm config --domain mydomain.com --dnsfqdn mypi.mydomain.com --mxfqdn mypi.mydomain.com`

    * Display the ndm configuration: `ndm config --list`

* Add your hosts, either via a set of ndm commands or by importing a properly formatted network database. See "Importing a network database" and "Day-to-day management tasks" below. Note that ndm will automatically add the hostname of the system on which it is running to the database.

    * `ndm add 192.168.42.4 --hostname mypitest --mac nn:nn:nn:nn:nn:nn --note "RPi for testing"`

* Build the dns and dhcpd site files: `ndm build --site`
* Install the dns and dhcpd site files: `ndm install --site`
* Build /etc/hosts, your domain's zone files, and the dhcpd blocked host list: `ndm build`
* Install those files: `ndm install`
* Start bind and dhcpd: `systemctl start bind9; systemctl start isc-dhcp-server`
* Resolve any errors identified in the system log

## When do I need to do an ndm build/install?

Changes to the settings for *dhcplease*, *dnsfqdn*, *dnsip*, *dnslistenport*, *domain*, *externaldns*, *gateway*, *myip*, *subnet*, or *timeserver* require an `ndm build --site`, `ndm install --site`, and `ndm install` for them to take effect.

Changes to the ndm host database with `ndm add`, `ndm delete`, or `ndm modify` require an `ndm build` and `ndm install` for them to take effect.

## Day-to-day management tasks

### Adding a host

* `ndm add 192.168.42.3 --mac nn:nn:nn:nn:nn:nn --hostname printserver` - Adds a new host named *printserver* to the ndm database. *printserver* has IP address 192.168.42.3 and the specified MAC Address. If *printserver* is configured to request an IP address via dhcp, it will always get 192.168.42.3
* `ndm build` - Builds the updated config files (but doesn't install them into the system)
* `ndm diff` - (optional). Displays the differences between the current in-use config files and the newly-created config files.
* `ndm install` - Installs the updated config files into the system and stops/starts bind and dhcpd

### Adding an external host to /etc/hosts

* `ndm add 12.10.2.1 --hostname example.some.com --hostsonly --nodomain` - Adds the entry to /etc/hosts. This is useful for names that need to be made available early in the boot process.
    * As with the first example, an `ndm build` and `ndm install` must be performed.

* `ndm add 192.168.42.12 --mac 4c:01:44:77:11:10 --hostname eerobase --note "eero in wiring closet"` - Eero sends multiple dhcp requests on different MAC addresses. I found that they can use the same IP address, so I use these two commands to force that. The second entry is only in the dhcpd config file, and not present in the dhcp zone or /etc/hosts files.
    * `ndm add 192.168.42.12 --mac 4c:01:44:77:11:22 --hostname eerobasex --dhcponly` - This is the second MAC address on the eero. This enables the dhcp server to respond to it, but the hostname is not made visible in dns.


### Deleting a host

* `ndm delete 192.168.42.17` - Deletes the entry with IP address 192.168.42.17 from the database.
* As with the first example, an `ndm build` and `ndm install` must be performed.

### Modifying a host

* `ndm modify 192.168.42.3 --note "New server 2018-12-04" --mac mm:mm:mm:mm:mm:mm`
* As with the first example, an `ndm build` and `ndm install` must be performed.

## Detailed command information

This section includes some discussion about each command including useful hints.

**add - **Add a new hostname to the database

You only need to do this if the host will have a fixed IP address, or it requires special DHCP handling, such as PXE booting.

To add a simple device to the database, use 

`ndm add 192.168.42.4 --hostname mypitest --mac nn:nn:nn:nn:nn:nn `

The MAC address is necessary so that dhcpd can assign it a fixed address. It is not necessary for any devices that have dynamically assigned IP addresses from the pool.

The switches to the *add* command provide flexibility and control over the host entry. Every ndm command has help like this available. 

```
bash$ ndm add --help
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
                        Name of dhcphostopt to add to this host's dhcp entry
  --dhcponly            Only put this host in dhcpd.conf (no hosts or DNS
                        config entries)
  --hostname HOSTNAME   New host name
  --hostsonly           Only put this host in hosts file (no dhcpd.conf or DNS
                        config entries)
  --mac MAC             New host MAC address
  --nodhcp              Don't add host to dhcpd.conf
  --nodomain            Don't add the domain name to this entry; It's already
                        fully qualified
  --note NOTE           Note text to add to flags for entry
  --zoneonly            Only put thishost in DNS config files (no dhcpd.conf
                        or hosts file)
```

To add a CNAME record, use: `ndm add cnamestring --hostname cnamevalue.mydomain.com. --cname`. (note the trailing ".") This will create a CNAME record for *cnamestring*, and it's value is *cnamevalue.mydomain.com.*

**build - **Build the dns and dhcp config files from the database

The *build* command has two forms: with the --site switch, and without it. If --site is provided, ndm builds the site-level  bind configuration files, the dhcpd configuration file, and generates a new dhcp-key. The files are created in a temporary directory and are not in use until you `ndm install --site` (and stop/restart dhcp and dns servers). The temporary directory is /tmp/ndm.*username*, but  can be changed with the --tmp switch. If you change the temporary directory for the *build* command, you also must change it for the *diff* and *install* commands.

**config - **Manage the ndm configuration database

The *config* command controls the site configuration database, and is used to do bulk import of host definitions. See the section "Importing a network database" below for details on bulk importing. An *ndm config* command with no switches defaults to `ndm config --list`.

**delete - **Delete an entry from the database

deletes a host from the database

**diff -** Diff the system config files against the newly-created config

Use the *diff* command to verify the changes in the newly-created config files against the files already in the system. As with the *build* and *install* commands, if --site is provided, the site-level bind and dhcp config files will be diffed. Without --site, the bind zone config files and dhcp blocked domain config will be diffed.

**install - **Install the configuration files created by the *build* command

installs the generated configuration. `install --site` installs new dhcp and bind site files and dhcp-key. Typically you'll do a `build --site` and `install --site` initially, and then very infrequently. See the section above "When is an ndm build/install needed?". Note: No running system configuration files are changed until an *ndm install* is done.

The `install --reset` command resets all the dhcp and bind configurations to the just-initialized state. All dynamic zone definitions are removed, as are all DHCP leases. This is primarily for testing, but can be used with care on live networks. Best is to have all hosts with statically-assigned DHCP-requested addresses. 

**list - **List all entries in the database.

If --dump is specified, the output is in *ndm import* format, which can be loaded into ndm with the `ndm config --importnet` command.

**modify - **Modify an existing host entry

You must specify the IP address. When renaming the hostname associated with an IP address, use the --newhostname switch. If an IP address has multiple hostnames associated with it, the --hostname switch must be used to specify which hostname to modify.

The --mac and --note switches and the various flags are attached to the hostname. The --dhcphostopt switch is attached to the IP address, so a hostname is not required when changing this setting.

**show - **Display an entry or set of entries

The argument can be an IP address (must fully match), part of a MAC address, or part of a host name. In the latter two cases, all matching entries are shown.

## Domain name behavior

When properly configured, you can refer to hosts on your network by their hostname, or by their fully qualified domain name. Both will work. For instance, a host named 'server1' in a domain named 'mydomain.com' can be refered to as server1, or as server1.mydomain.com

The dns database that ndm sets up is completely independent of any dns database on the public internet. For instance, if you have a public domain 'mydomain.com', then looking up server1.mydomain.com on the public internet would most likely refer to a public IP addrress, while looking up server1.mydomain.com on your internal network would refer to a private (e.g., non-public) address, such as 192.168.42.5.

## Configuring a dhcphostopt

Use *dhcphostopt* to configure PXE or other host-specific DHCP options. For each dhcphostopt setting, ndm adds the dhcphostopt substitution string to the host entry in the dhcp subnet hosts file.

For example: 

`ndm config --dhcphostopt 'PXE=next-server 192.168.42.3; filename "pxelinux.0";'`

`ndm config --dhcphostopt "DNSX=option domain-name-servers 192.168.42.4, 1.0.0.1;"`

If you want to change the text of a dhcphostopt simply re-enter the command with the new replacement string. Leave the replacement string blank if you want to delete a dhcphostopt (e.g., `ndm config --dhcphostopt "DNSX="`). Don't forget the trailing semicolon as in the examples, as these are required by the dhcp config file syntax.

Apply the dhcphostopt setting as desired to specific hosts:

`ndm modify 192.168.42.17 --dhcphostopt PXE`

`ndm modify 192.168.42.18 --dhcphostopt PXE,DNSE`

If a dhcphostopt has been applied to a host but there is no dhcphosthopt configuration for the specified dhcphostopt, ndm will warn you, but continue.

As always, after a host configuration has been modified, do an `ndm build` and `ndm install`.

## Importing a network database

Use the command `ndm config --import` to import a properly formatted database. The importer does not do much syntax checking, so be sure to check the results very carefully. The import database format is

IPaddr,MACaddr,hostname,flags,Note,dhcphostopt,

For instance

`192.168.42.2,nn:nn:nn:nn:nn:nn,mypi,Pi next to the router,PXE,`
`192.168.42.3,nn:nn:nn:nn:nn:nn,mywin,My Windows desktop,,`

The flags correspond to the command-line switches of the *add command*. When included in the network database import file, I suggest prefixing them with a plus sign for readability. For example:

192.168.42.5,nn:nn:nn:nn:nn:nn,www,+zoneonly,

* *nodhcp*: Don't put this host in dhcpd.conf. Use this on the second and subsequent hostnames on the same IP address.
* *cname*: This is a CNAME (dns alias) and goes in the domain zone file only (implies *zoneonly*)
* *dhcponly*: Only put this host in dhcpd.conf (do not add to /etc/hosts or any dns files). You might want to use this for a host that has a dhcp-assigned address, but you don't want the hostname in dns
* *hostsonly*: Only put this host in /etc/hosts (do not add to dhcpd.conf or any dns files). You can use this for hosts that are outside your domain, but you want dns to resolve them (e.g., special internet addresses)
* *zoneonly*: Only put this host in the dns zone file (do not add to dhcpd.conf or /etc/hosts)
* *nodomain*: Don't add the domain name to the host in /etc/hosts. Use this if you have an FQDN name for a host outside your domain.

Once the network database has been successfully imported, do a `ndm build` and `ndm install`.

## Using ndm with multiple LAN subnets or a VPN

By default, the name server is configured to only accept requests from the host on which the name server is running, and any hosts in the subnet specified by --subnet. If you're using multiple LAN subnets or have a VPN installed that will use your DNS server for name services, you must specify the additional subnets using the `ndm config --internals` command. 

For instance, if my VPN provides client IP addresses in subnet 10.42.10.0/24, I would use `ndm config --internals 10.42.10.0/24`, and ndm will add that subnet to the list of subnets allowed to query the name server.

## Using ndm with Pi-Hole

If you want to run ndm and bind/dhcpd on the same system as Pi-Hole, here are the steps. Basic testing has been done with both running on the same system.

* Install and configure Pi-Hole per the Pi-Hole documentation
* Install and configure bind, dhcpd, and ndm per this document
* Modify the ndm configuration to use a different TCP port for dns: `ndm config --dnslistenport newport`. Pi-Hole will listen on port 53 (the default dns port), so select another port less than 1024.
* `ndm build --site` and `ndm install --site` the updated configuration
* Configure any hosts with static IP address as documented above.
* In the Pi-Hole configuration, establish an external dns server: TBD
* Test. Just like I need to do before this is released :)

Things of note

* Under piHole advanced DNS settings, clear the "never forward non-fqdns" and "never forward reverse-lookups for IP ranges". 
* In PiHole specify the DNS server as 127.0.0.1#portnum or ipaddr#portnum (use a '#' to separate the IP address and port)
* I have not yet found a way to set domain search for dyn.domain except by editing resolv.conf


## Why use bind9 and isc-dhcp-server and not dnsmasq...or Pi-Hole?

Both systems (bind9/isc-dhcp-server and dnsmasq) are great. This is most definitely not a question of one being better than the other. I've been using bind/dhcpd since my Linux day 1 (20+ years ago), and I've never had a problem with it, other than tending to the configuration files, meaning...I have never had any incentive to change. Rather, I just needed a better tool for managing the configuration, and ndm is it.

If you like dnsmasq, great! If you'd like to use ndm with dnsmasq, let me know...it will provide me with inspiration to do make it happen.

On the other hand, if you haven't used either dns/dhcpd system and are looking to start, I would argue that bind/dhcpd/ndm is much easier to configure than dnsmasq for the home/small business network.

But, if you'd prefer to use dnsmasq, that's fine, too. It's all good.

As far as Pi-Hole, it's fantastic as well, and has a lot of great features. It's big more complex than I wanted. I prefer solutions that are small and simple. If that's not what you want, you're probably better served with dnsmasq and Pi-Hole.

## Troubleshooting

ndm's function and purpose is to produce correct configuration files for bind and dhcpd. If either of these services have a problem, check the system logs (via the `journalctl` command) for hints as to the cause. Once the service error has been identified, it is generally straightforward from the context to trace the issue back to the incorrect ndm config setting.

Known configuration issues:

* Name resolution doesn't work as expected after the first build/install has been completed - This is typically caused by either dnsip or myip being incorrectly set to 127.0.0.1 instead of the actual host IP address. To correct:

    * Check ndm settings: `ndm config`
    * If dnsip and/or myip are set to 127.0.0.1, correct them: `ndm config --dnsip my.ip.ad.dr --myip my.ip.ad.dr` for the fixed IP address that you have statically assigned and configured for this host.
    * Why is this? There isn't a good way to reliably get the hosts's IP address if the name service is not fully configured. The only ways that I've found either require internet access, other knowledge about the network, installing additional Python packages, or parsing command output. If there's a Pythonic way to reliably get the host's ethernet adapter real IP address, please let me know!

* /etc/resolv.conf changes unexpectedly. This might occur if you are using dhcpcd or NetworkManager, and have established alternate network configurations. DNS and DHCP are server services, so the host running them should only have one network configuration, the static IP address.

## Distro-specific Notes

This section includes a few notes on using ndm on various Linux distributions

### Raspbian Stretch and later

Raspbian Stretch, Buster, and later are fully-supported by ndm as documented above.

### OpenSuse Leap

OpenSuse Leap is supported, but there are configuration settings that ndm does not do automatically, as it does for Raspbian. 

#### Installation steps

* Install named and dhcpd: `zypper in named; zypper in dhcpd`
* Make the following yast configuration changes
    * Edit /etc/sysconfig/dhcpd to set DHCPD_INTERFACE to the name of your network interface.
    * ?? What about the     DHCPD config files? ???
    * Edit /etc/sysconfig/named and set NAMED_CONF_INCLUDE_FILES to "/etc/ndm-bind-blocked.conf /etc/named.conf"
    * Edit /etc/sysconfig/network/config. These two settings can be made to the config file or on the yast2 | Network Settings | Hostname/DNS page.
        * Set NETCONFIG_DNS_STATIC_SERVERS to the local system's IP addresses: "127.0.0.1 192.168.42.2". Adjust the 2nd IP address for that of your own system.
        * Set NETCONFIG_DNS_STATIC_SEARCHLIST to "mydomain.com dyn.mydomain.com". Adjust mydomain.com to be the same as ndm's domain setting (view with `ndm config`)
* `chown root.named /var/lib/named/master`
* `chmod 2775 /var/lib/named/master`

Caution: Do not use the yast2 DHCP Server or DNS Server configurators in conjunction with ndm. These two configuration methods are blissfully unaware of each other.

### Other distros

ndm is mostly distro-independent and can be easily extended. Virtually all the work in supporting an additional distro is in configuring the correct filenames and directories for the bind/named and dhcp config files. Let me know what distro you're interested in!
