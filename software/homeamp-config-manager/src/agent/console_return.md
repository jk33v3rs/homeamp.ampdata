root@archivesmp /etc/nginx/conf.d # 


# First, check what's actually broken with the yunohost admin interface
sudo yunohost tools diagnosis run




# Reinstall/repair the YunoHost admin interface
sudo yunohost tools postinstall --help




# Check if we need to re-run initial configuration
sudo cat /etc/yunohost/installed




# If YunoHost thinks it's not configured, run postinstall
sudo yunohost tools postinstall --domain archivesmp.site --password <admin-password>




# Or if it's already installed, force regenerate all configs
sudo yunohost tools regen-conf --force --dry-run




# See what would be regenerated
sudo yunohost tools regen-conf --force




# Specifically for nginx and SSOwat
sudo yunohost tools regen-conf nginx ssowat --force




# Make sure all domains are properly registered in YunoHost's internal config
# Re-add the main domain if needed
sudo yunohost domain add archivesmp.site 2>/dev/null || echo "Domain already exists"




# Set it as main domain explicitly
sudo yunohost domain main-domain --new-domain archivesmp.site




# Regenerate domain configurations
sudo yunohost domain cert-install archivesmp.site --force --self-signed




# Force regenerate everything
sudo yunohost tools regen-conf --force




# Reload services
sudo systemctl reload nginx
sudo systemctl restart yunohost-api
usage: yunohost tools
                      {rootpw,maindomain,postinstall,update_norefresh,update,upgrade,shell,basic-space-cleanup,shutdown,reboot,regen-conf,versions,migrations}
                      ...
                      [-h]
yunohost tools: error: argument {rootpw,maindomain,postinstall,update_norefresh,update,upgrade,shell,basic-space-cleanup,shutdown,reboot,regen-conf,versions,migrations}: invalid choice: 'diagnosis' (choose from 'rootpw', 'maindomain', 'postinstall', 'update_norefresh', 'update', 'upgrade', 'shell', 'basic-space-cleanup', 'shutdown', 'reboot', 'regen-conf', 'versions', 'migrations')
usage: yunohost tools postinstall [-h] [-d DOMAIN] [-u USERNAME] [-F FULLNAME] [-p PASSWORD] [--ignore-dyndns]
                                  [--dyndns-recovery-password [PASSWORD]] [--force-diskspace] [--i-have-read-terms-of-services]


YunoHost post-install


options:
  -h, --help            show this help message and exit
  -d DOMAIN, --domain DOMAIN
                        YunoHost main domain
  -u USERNAME, --username USERNAME
                        Username for the first (admin) user. For example 'camille'
  -F FULLNAME, --fullname FULLNAME
                        The full name for the first (admin) user. For example 'Camille Dupont'
  -p PASSWORD, --password PASSWORD
                        YunoHost admin password
  --ignore-dyndns       If adding a DynDNS domain, only add the domain, without subscribing to the DynDNS service
  --dyndns-recovery-password [PASSWORD]
                        If adding a DynDNS domain, subscribe to the DynDNS service with a password, used to later recover the domain if
                        needed
  --force-diskspace     Use this if you really want to install YunoHost on a setup with less than 10 GB on the root filesystem
  --i-have-read-terms-of-services
                        Automatically reply to the terms of services prompt, for example for non-interactive installations
-bash: syntax error near unexpected token `newline'
Warning: The ssh configuration has been manually modified, but you need to explicitly specify category 'ssh' with --force to actually apply the changes.
Success! The configuration would have been updated for category 'postfix'
Success! The configuration would have been updated for category 'dovecot'
Success! The configuration would have been updated for category 'dnsmasq'
Success! The configuration would have been updated for category 'fail2ban'
dnsmasq: 
  applied: 
    /etc/dnsmasq.d/keevers.online: 
      status: force-removed
    /etc/dnsmasq.d/keevers.site: 
      status: force-removed
    /etc/dnsmasq.d/keevers.wiki: 
      status: removed
    /etc/dnsmasq.d/keevers.world: 
      status: force-removed
    /etc/resolv.dnsmasq.conf: 
      status: updated
  pending: 
dovecot: 
  applied: 
    /etc/dovecot/dovecot.conf: 
      status: updated
  pending: 
fail2ban: 
  applied: 
    /etc/fail2ban/jail.d/yunohost-jails.conf: 
      status: updated
  pending: 
postfix: 
  applied: 
    /etc/default/postsrsd: 
      status: updated
    /etc/postfix/relay_recipients.db: 
      status: updated
    /etc/postfix/sni: 
      status: updated
    /etc/postfix/virtual-mailbox-domains: 
      status: updated
  pending: 
ssh: 
  applied: 
  pending: 
    /etc/ssh/sshd_config: 
      status: modified
Warning: The ssh configuration has been manually modified, but you need to explicitly specify category 'ssh' with --force to actually apply the changes.
Success! Configuration updated for 'postfix'
Success! Configuration updated for 'dovecot'
Success! Configuration updated for 'dnsmasq'
Success! Configuration updated for 'fail2ban'
dnsmasq: 
  applied: 
    /etc/dnsmasq.d/keevers.online: 
      status: force-removed
    /etc/dnsmasq.d/keevers.site: 
      status: force-removed
    /etc/dnsmasq.d/keevers.wiki: 
      status: removed
    /etc/dnsmasq.d/keevers.world: 
      status: force-removed
    /etc/resolv.dnsmasq.conf: 
      status: updated
  pending: 
dovecot: 
  applied: 
    /etc/dovecot/dovecot.conf: 
      status: updated
  pending: 
fail2ban: 
  applied: 
    /etc/fail2ban/jail.d/yunohost-jails.conf: 
      status: updated
  pending: 
postfix: 
  applied: 
    /etc/default/postsrsd: 
      status: updated
    /etc/postfix/relay_recipients.db: 
      status: updated
    /etc/postfix/sni: 
      status: updated
    /etc/postfix/virtual-mailbox-domains: 
      status: updated
  pending: 
ssh: 
  applied: 
  pending: 
    /etc/ssh/sshd_config: 
      status: modified
Info: attribute 'virtualdomain' with value 'archivesmp.site' is not unique
Domain already exists
usage: yunohost {domain} ... [-h] [--output-as {json,plain,none}] [--debug] [--quiet] [--version] [--timeout ==SUPPRESS==]
yunohost: error: unrecognized arguments: --new-domain archivesmp.site
usage: yunohost domain {list,info,add,remove,main-domain,maindomain,url-available,action-run,dyndns,config,dns,cert} ... [-h]
yunohost domain: error: argument {list,info,add,remove,main-domain,maindomain,url-available,action-run,dyndns,config,dns,cert}: invalid choice: 'cert-install' (choose from 'list', 'info', 'add', 'remove', 'main-domain', 'maindomain', 'url-available', 'action-run', 'dyndns', 'config', 'dns', 'cert')
Warning: The ssh configuration has been manually modified, but you need to explicitly specify category 'ssh' with --force to actually apply the changes.
Success! Configuration updated for 'postfix'
Success! Configuration updated for 'dnsmasq'
dnsmasq: 
  applied: 
    /etc/resolv.dnsmasq.conf: 
      status: updated
  pending: 
postfix: 
  applied: 
    /etc/postfix/relay_recipients.db: 
      status: updated
  pending: 
ssh: 
  applied: 
  pending: 
    /etc/ssh/sshd_config: 
      status: modified
root@archivesmp /etc/nginx/conf.d # 
