

root@archivesmp /etc/nginx/conf.d # 


# Try SSOwat regeneration now that other configs are updated
sudo yunohost tools regen-conf ssowat --force




# If that still fails with StopIteration, try nginx regeneration
sudo yunohost tools regen-conf nginx --force




# Check current main domain setting
sudo yunohost domain main-domain




# Try to access the SSO portal
curl -I https://archivesmp.site/yunohost/sso/




# Check SSOwat config was created
cat /etc/ssowat/conf.json | python3 -m json.tool | head -100




Info: The operation 'Regenerate system configurations 'ssowat'' could not be completed. Please share the full log of this operation using the command 'yunohost log share 20251121-150830-regen_conf-ssowat' to get help
Error: Could not regenerate the configuration for category(s): 
current_main_domain: archivesmp.site
HTTP/2 200 
server: nginx
date: Fri, 21 Nov 2025 15:08:42 GMT
content-type: text/html
content-length: 11028
last-modified: Tue, 19 Aug 2025 23:40:33 GMT
x-sso-wat: You've just been SSOed
content-security-policy: upgrade-insecure-requests; default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; object-src 'none'; img-src 'self' data:;
x-content-type-options: nosniff
x-xss-protection: 1; mode=block
x-download-options: noopen
x-permitted-cross-domain-policies: none
x-frame-options: SAMEORIGIN
permissions-policy: interest-cohort=()
strict-transport-security: max-age=63072000; includeSubDomains; preload
cache-control: no-store, no-cache, must-revalidate
accept-ranges: bytes


{
    "cookie_name": "yunohost.portal",
    "cookie_secret_file": "/etc/yunohost/.ssowat_cookie_secret",
    "domain_portal_urls": {
        "admin.archivesmp.com": "admin.archivesmp.com/yunohost/sso",
        "amp.archivesmp.site": "archivesmp.site/yunohost/sso",
        "archivesmp.site": "archivesmp.site/yunohost/sso",
        "atlas.archivesmp.site": "archivesmp.site/yunohost/sso",
        "cloud.archivesmp.site": "archivesmp.site/yunohost/sso",
        "cloud.keevers.website": "cloud.keevers.website/yunohost/sso",
        "dash.archivesmp.site": "archivesmp.site/yunohost/sso",
        "default": "/yunohost/admin",
        "files.archivesmp.site": "archivesmp.site/yunohost/sso",
        "grimmdotter.online": "grimmdotter.online/yunohost/sso",
        "jk33v3rs.archivesmp.site": "archivesmp.site/yunohost/sso",
        "jupyter.archivesmp.site": "archivesmp.site/yunohost/sso",
        "maps.archivesmp.com": "maps.archivesmp.com/yunohost/sso",
        "mattermost.archivesmp.site": "archivesmp.site/yunohost/sso",
        "n8n.archivesmp.site": "archivesmp.site/yunohost/sso",
        "openwebui.archivesmp.site": "archivesmp.site/yunohost/sso",
        "plan.archivesmp.com": "plan.archivesmp.com/yunohost/sso",
        "plex.archivesmp.site": "archivesmp.site/yunohost/sso",
        "portainer.archivesmp.site": "archivesmp.site/yunohost/sso",
        "remote.archivesmp.site": "archivesmp.site/yunohost/sso",
        "st.archivesmp.site": "archivesmp.site/yunohost/sso",
        "todo.grimmdotter.online": "grimmdotter.online/yunohost/sso",
        "zt.archivesmp.site": "archivesmp.site/yunohost/sso"
    },
    "permissions": {
        "cockpit.main": {
            "auth_header": "basic-with-password",
            "public": false,
            "uris": [
                "archivesmp.site/monitor"
            ],
            "users": [
                "jk33v3rs",
                "jk3ating",
                "otter",
                "webadmin"
            ]
        },
        "core_skipped": {
            "auth_header": false,
            "public": true,
            "uris": [
                "admin.archivesmp.com/yunohost/admin",
                "maps.archivesmp.com/yunohost/admin",
                "plan.archivesmp.com/yunohost/admin",
                "archivesmp.site/yunohost/admin",
                "amp.archivesmp.site/yunohost/admin",
                "atlas.archivesmp.site/yunohost/admin",
                "cloud.archivesmp.site/yunohost/admin",
                "dash.archivesmp.site/yunohost/admin",
                "files.archivesmp.site/yunohost/admin",
                "jk33v3rs.archivesmp.site/yunohost/admin",
                "jupyter.archivesmp.site/yunohost/admin",
                "mattermost.archivesmp.site/yunohost/admin",
                "n8n.archivesmp.site/yunohost/admin",
                "openwebui.archivesmp.site/yunohost/admin",
                "plex.archivesmp.site/yunohost/admin",
                "portainer.archivesmp.site/yunohost/admin",
                "remote.archivesmp.site/yunohost/admin",
                "st.archivesmp.site/yunohost/admin",
                "zt.archivesmp.site/yunohost/admin",
                "grimmdotter.online/yunohost/admin",
                "todo.grimmdotter.online/yunohost/admin",
                "cloud.keevers.website/yunohost/admin",
                "admin.archivesmp.com/yunohost/api",
                "maps.archivesmp.com/yunohost/api",
                "plan.archivesmp.com/yunohost/api",
                "archivesmp.site/yunohost/api",
                "amp.archivesmp.site/yunohost/api",
                "atlas.archivesmp.site/yunohost/api",
                "cloud.archivesmp.site/yunohost/api",
                "dash.archivesmp.site/yunohost/api",
                "files.archivesmp.site/yunohost/api",
                "jk33v3rs.archivesmp.site/yunohost/api",
                "jupyter.archivesmp.site/yunohost/api",
                "mattermost.archivesmp.site/yunohost/api",
                "n8n.archivesmp.site/yunohost/api",
                "openwebui.archivesmp.site/yunohost/api",
                "plex.archivesmp.site/yunohost/api",
                "portainer.archivesmp.site/yunohost/api",
                "remote.archivesmp.site/yunohost/api",
                "st.archivesmp.site/yunohost/api",
                "zt.archivesmp.site/yunohost/api",
                "grimmdotter.online/yunohost/api",
                "todo.grimmdotter.online/yunohost/api",
                "cloud.keevers.website/yunohost/api",
                "admin.archivesmp.com/yunohost/portalapi",
                "maps.archivesmp.com/yunohost/portalapi",
                "plan.archivesmp.com/yunohost/portalapi",
                "archivesmp.site/yunohost/portalapi",
                "amp.archivesmp.site/yunohost/portalapi",
                "atlas.archivesmp.site/yunohost/portalapi",
                "cloud.archivesmp.site/yunohost/portalapi",
                "dash.archivesmp.site/yunohost/portalapi",
                "files.archivesmp.site/yunohost/portalapi",
                "jk33v3rs.archivesmp.site/yunohost/portalapi",
