# LuckPerms - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## General

`allow-invalid-usernames` = false

`apply-bukkit-attachment-permissions` = true

`apply-bukkit-child-permissions` = true

`apply-bukkit-default-permissions` = true

`apply-default-negated-permissions-before-wildcards` = false

`apply-global-groups` = true

`apply-global-world-groups` = true

`apply-regex` = true

`apply-shorthand` = true

`apply-sponge-implicit-wildcards` = false

`apply-wildcards` = true

`argument-based-command-permissions` = false

`auto-install-translations` = true

`auto-op` = false

`auto-push-updates` = true

`broadcast-received-log-entries` = true

`commands-allow-op` = true

`context-satisfy-mode` = "at-least-one-value-per-key"

`debug-logins` = false

`disable-bulkupdate` = false

`disabled-context-calculators` = []

`disabled-contexts` = null

`enable-ops` = true

`group-weight` = null

`include-global` = true

`include-global-world` = true

`inheritance-traversal-algorithm` = "depth-first-pre-order"

`log-notify` = true

`log-notify-filtered-descriptions` = null

`messaging-service` = "pluginmsg"

`meta-value-selection` = null

`meta-value-selection-default` = "inheritance"

`post-traversal-inheritance-sort` = false

`prevent-primary-group-removal` = false

`primary-group-calculation` = "parents-by-weight"

`push-log-entries` = true

`register-command-list-data` = true

`require-sender-group-membership-to-modify` = false

`resolve-command-selectors` = false

`server` = "global"

`skip-bulkupdate-confirmation` = false

`storage-method` = "MariaDB"

`sync-minutes` = -1

`temporary-add-behaviour` = "deny"

`update-client-command-list` = true

`use-server-uuid-cache` = true

`use-vault-server` = true

`vault-group-use-displaynames` = true

`vault-ignore-world` = false

`vault-include-global` = true

`vault-npc-group` = "npc"

`vault-npc-op-status` = false

`vault-unsafe-lookups` = true

`watch-files` = true

`world-rewrite` = null

## Commands-Read-Only-Mode

`commands-read-only-mode.console` = false

`commands-read-only-mode.players` = false

## Data

`data.address` = "135.181.212.169:3369"

`data.database` = "asmp_SQL"

`data.mongodb-collection-prefix` = ""

`data.mongodb-connection-uri` = ""

`data.password` = "SQLdb2024!"

`data.pool-settings.connection-timeout` = 5000

`data.pool-settings.keepalive-time` = 0

`data.pool-settings.maximum-lifetime` = 1800000

`data.pool-settings.maximum-pool-size` = 10

`data.pool-settings.minimum-idle` = 10

`data.pool-settings.properties.characterEncoding` = "utf8"

`data.pool-settings.properties.useUnicode` = true

`data.username` = "sqlworkerSMP"

## Disable-Luckperms-Commands

`disable-luckperms-commands.console` = false

`disable-luckperms-commands.players` = false

## Meta-Formatting

`meta-formatting.prefix.duplicates` = "first-only"

`meta-formatting.prefix.end-spacer` = ""

`meta-formatting.prefix.format` = ['highest']

`meta-formatting.prefix.middle-spacer` = " "

`meta-formatting.prefix.start-spacer` = ""

`meta-formatting.suffix.duplicates` = "first-only"

`meta-formatting.suffix.end-spacer` = ""

`meta-formatting.suffix.format` = ['highest']

`meta-formatting.suffix.middle-spacer` = " "

`meta-formatting.suffix.start-spacer` = ""

## Nats

`nats.address` = "localhost"

`nats.enabled` = false

`nats.password` = ""

`nats.username` = ""

## Rabbitmq

`rabbitmq.address` = "localhost"

`rabbitmq.enabled` = false

`rabbitmq.password` = "guest"

`rabbitmq.username` = "guest"

`rabbitmq.vhost` = "/"

## Redis

`redis.address` = "135.181.212.169:6379"

`redis.enabled` = false

`redis.password` = "Fartp0wer69!"

`redis.username` = "default"

## Split-Storage

`split-storage.enabled` = false

`split-storage.methods.group` = "h2"

`split-storage.methods.log` = "h2"

`split-storage.methods.track` = "h2"

`split-storage.methods.user` = "h2"

`split-storage.methods.uuid` = "h2"

