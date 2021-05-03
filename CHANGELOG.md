# Changelog

	
## V2.2

* ndm now supports Raspbian/RasPiOS, Debian, and Ubuntu
* Rename database item dhcpkey to DNSUpgradeKey, and change to just-in-time creation. If you want to change it, simply edit /etc/dbndm.json and delete the line with DNSUpgradeKey in it.
* Add version numbers to all files
* Add setting of some host flags in 'ndm modify'
* Improve OS type handling. All commands except diff and install can be used on an "unknown" OS, so you can build the config files and move them manually on an NYI-in-ndm OS

## V2.0

* This release is a Major overhaul!
* DNS and DHCP modules are now loadable, and must be in the same directory as ndm. The new installer, EZndmInstaller, places these files in /usr/local/bin by default.
* Existing database automatically upgraded to database format v2
* As before, bind and isc-dhcp-server are supported
* Newly-added: support for dnsmasq for both DNS and DHCP
* On a new install, configuration settings for dnsfqdn, dnsip, hostfqdn, and mxfqdn all default to the system running ndm; can be changed with `ndm config`
* --bindinclude is now --dnsinclude. Upgrades handle the conversion
* --servicewait was unnecessary and has been removed
* host IP address determination improved. Should work 99.9992% of the time
* Versioning established for program (V2.0) and the config database (2)
* New install script provides "getting started" text
* Changing the domain name (`ndm config --domain newdomain`) automatically changes the FQDN for dnsfqdn, hostfqdn, and mxfqdn
* Not yet complete:
    * chroot configuration for bind
    * Support for OS other than RasPiOS (many distros have their own ideas where an app's config files should be)

