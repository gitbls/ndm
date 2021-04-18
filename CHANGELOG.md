# Changelog

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

