# Quests - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## Global-Macros

`global-macros.bar` = "&6---&7---&6---"

## Global-Quest-Display

`global-quest-display.lore.append-not-started` = ['', '&eLeft Click &7to start this quest.']

`global-quest-display.lore.append-started` = ['', '&aYou have started this quest.', '&ePress Q &7to track this quest.', '&eRight Click &7to cancel this quest.']

`global-quest-display.lore.append-tracked` = ['', '&aYou are &etracking &athis quest.', '&ePress Q &7to stop tracking this quest.', '&eRight Click &7to cancel this quest.']

## Gui

`gui.back-button.enabled` = true

`gui.back-button.lore` = ['&7Return to the categories menu.']

`gui.back-button.name` = "&cReturn"

`gui.back-button.slot` = 45

`gui.back-button.type` = "ARROW"

`gui.no-started-quests.lore` = ['&7Go start some!']

`gui.no-started-quests.name` = "&c&lNo Started Quests"

`gui.no-started-quests.type` = "FEATHER"

`gui.page-desc.enabled` = true

`gui.page-desc.lore` = ['&7You are currently viewing page &c{page}.']

`gui.page-desc.name` = "&7Page &c{page}"

`gui.page-desc.slot` = 49

`gui.page-desc.type` = "PAPER"

`gui.page-next.enabled` = true

`gui.page-next.lore` = ['&7Switch the page to page &c{nextpage}.']

`gui.page-next.name` = "&7Next Page"

`gui.page-next.slot` = 50

`gui.page-next.type` = "FEATHER"

`gui.page-prev.enabled` = true

`gui.page-prev.lore` = ['&7Switch the page to page &c{prevpage}.']

`gui.page-prev.name` = "&7Previous Page"

`gui.page-prev.slot` = 48

`gui.page-prev.type` = "FEATHER"

`gui.quest-cancel-background.type` = "GRAY_STAINED_GLASS_PANE"

`gui.quest-cancel-no.lore` = ['&7Return to the quest menu.']

`gui.quest-cancel-no.name` = "&c&lAbort Cancel"

`gui.quest-cancel-no.type` = "RED_STAINED_GLASS_PANE"

`gui.quest-cancel-yes.lore` = ['&7Confirm you wish to cancel', '&7this quest and lose all', '&7progress.']

`gui.quest-cancel-yes.name` = "&a&lConfirm Cancel"

`gui.quest-cancel-yes.type` = "GREEN_STAINED_GLASS_PANE"

`gui.quest-completed-display.lore` = ['&7You have completed this quest', '&7(&a{quest}&7) and cannot.', '&7repeat it.']

`gui.quest-completed-display.name` = "&a&lQuest Complete"

`gui.quest-completed-display.type` = "GREEN_STAINED_GLASS_PANE"

`gui.quest-cooldown-display.lore` = ['&7You have recently completed this quest', '&7(&e{quest}&7) and you must', '&7wait another &e{time} &7to unlock again.']

`gui.quest-cooldown-display.name` = "&e&lQuest On Cooldown"

`gui.quest-cooldown-display.type` = "ORANGE_STAINED_GLASS_PANE"

`gui.quest-locked-display.lore` = ['&7You have not completed the requirements', '&7for this quest (&c{quest}&7).', '', '&7Requires: &c{requirements}', '&7to be completed to unlock.']

`gui.quest-locked-display.name` = "&c&lQuest Locked"

`gui.quest-locked-display.type` = "RED_STAINED_GLASS_PANE"

`gui.quest-permission-display.lore` = ['&7You do not have permission for this', '&7quest (&6{quest}&7).']

`gui.quest-permission-display.name` = "&6&lNo Permission"

`gui.quest-permission-display.type` = "BROWN_STAINED_GLASS_PANE"

## Messages

`messages.beta-reminder` = "&cQuests > &7Reminder: you are currently using a &cbeta &7version of Quests. Please send bug reports to https://github.com/LMBishop/Quests/issues and check for updates regularly using &c/quests admin update&7!"

`messages.command-category-open-disabled` = "&7Categories are disabled."

`messages.command-category-open-doesntexist` = "&7The specified category '&c{category}&7' does not exist."

`messages.command-data-not-loaded` = "&4Your quests progress file has not been loaded; you cannot use quests. If this issue persists, contact an admin."

`messages.command-no-permission` = "&7You do not have permission to use this command."

`messages.command-quest-admin-category-permission` = "&7Category &c{category} &7 could not be opened for player &c{player}&7. They do not have permission to view it."

`messages.command-quest-admin-complete-success` = "&7Quest &c{quest} &7completed for player &c{player}&7."

`messages.command-quest-admin-fullreset` = "&7Data for player &c{player}&7 has been fully reset."

`messages.command-quest-admin-loaddata` = "&7Quest data for '&c{player}&7' is being loaded."

`messages.command-quest-admin-nodata` = "&7No data could be found for player &c{player}&7."

`messages.command-quest-admin-playernotfound` = "&7Player '&c{player}&7' could not be found."

`messages.command-quest-admin-random-category-none` = "&7Player &c{player}&7 has no quests in category '&c{category}&7' which they can start."

`messages.command-quest-admin-random-category-success` = "&7Successfully started random quest '&c{quest}&7' from category '&c{category}&7' for player &c{player}&7."

`messages.command-quest-admin-random-none` = "&7Player &c{player}&7 has no quests which they can start."

`messages.command-quest-admin-random-success` = "&7Successfully started random quest '&c{quest}&7' for player &c{player}&7."

`messages.command-quest-admin-reset-success` = "&7Successfully reset quest '&c{quest}&7' for player &c{player}&7."

`messages.command-quest-admin-start-failcategorypermission` = "&7Quest '&c{quest}&7' could not be started for player &c{player}&7. They do not have permission for the category which the quest is in."

`messages.command-quest-admin-start-failcomplete` = "&7Quest '&c{quest}&7' could not be started for player &c{player}&7. They have already completed it."

`messages.command-quest-admin-start-failcooldown` = "&7Quest '&c{quest}&7' could not be started for player &c{player}&7. It is still on cooldown for them."

`messages.command-quest-admin-start-faillimit` = "&7Quest '&c{quest}&7' could not be started for player &c{player}&7. They have reached their quest start limit."

`messages.command-quest-admin-start-faillocked` = "&7Quest '&c{quest}&7' could not be started for player &c{player}&7. They have not yet unlocked it."

`messages.command-quest-admin-start-failother` = "&7Quest '&c{quest}&7' could not be started for player &c{player}&7."

`messages.command-quest-admin-start-failpermission` = "&7Quest '&c{quest}&7' could not be started for player &c{player}&7. They do not have permission."

`messages.command-quest-admin-start-failstarted` = "&7Quest '&c{quest}&7' could not be started for player &c{player}&7. It is already started."

`messages.command-quest-admin-start-success` = "&7Quest &c{quest} &7started for player &c{player}&7."

`messages.command-quest-cancel-specify` = "&7You must specify a quest to cancel."

`messages.command-quest-general-doesntexist` = "&7The specified quest '&c{quest}&7' does not exist."

`messages.command-quest-opencategory-admin-success` = "&7Opened category &c{category} &7for player &c{player}&7."

`messages.command-quest-openquests-admin-success` = "&7Opened Quest GUI for player &c{player}&7."

`messages.command-quest-openstarted-admin-success` = "&7Opened started Quest GUI for player &c{player}&7."

`messages.command-quest-start-doesntexist` = "&7The specified quest '&c{quest}&7' does not exist."

`messages.command-sub-doesntexist` = "&7The specified subcommand '&c{sub}' &7does not exist."

`messages.command-taskview-admin-fail` = "&7Task type '&c{task}&7' does not exist."

`messages.placeholderapi-data-not-loaded` = "Data not loaded"

`messages.placeholderapi-false` = "false"

`messages.placeholderapi-no-time-limit` = "No time limit"

`messages.placeholderapi-no-tracked-quest` = "No tracked quest"

`messages.placeholderapi-quest-not-started` = "Quest not started"

`messages.placeholderapi-true` = "true"

`messages.quest-cancel` = "&7Quest &c{quest} &7cancelled!"

`messages.quest-cancel-notcancellable` = "&7You cannot cancel this quest."

`messages.quest-cancel-notstarted` = "&7You have not started this quest."

`messages.quest-category-permission` = "&7You do not have permission to view this category."

`messages.quest-category-quest-permission` = "&7You do not have permission to start this quest since it is in a category you do not have permission to view."

`messages.quest-complete` = "&7Quest &c{quest} &7completed!"

`messages.quest-expire` = "&7Quest &c{quest} &7has expired."

`messages.quest-random-none` = "&cYou have no quests which you can start."

`messages.quest-start` = "&7Quest &c{quest} &7started!"

`messages.quest-start-cooldown` = "&7You have recently completed this quest. You have to wait &c{time} &7until you are able to restart it."

`messages.quest-start-disabled` = "&7You cannot repeat this quest."

`messages.quest-start-limit` = "&7Players are limited to &c{limit} &7started quests at a time."

`messages.quest-start-locked` = "&7You have not unlocked this quest yet."

`messages.quest-start-permission` = "&7You do not have permission to start this quest."

`messages.quest-start-started` = "&7You have already started this quest."

`messages.quest-track` = "&7Tracking quest &c{quest}&7."

`messages.quest-track-stop` = "&7No longer tracking quest &c{quest}&7."

`messages.quest-updater` = "&cQuests > &7A new version &c{newver} &7was found on Spigot (your version: &c{oldver}&7). Please update me! <3 - Link: {link}"

`messages.time-format` = "{hours}h {minutes}m"

`messages.ui-placeholder-completed-false` = "false"

`messages.ui-placeholder-completed-true` = "true"

`messages.ui-placeholder-no-time-limit` = "No time limit"

`messages.ui-placeholder-truncated` = " +{amount} more"

## Number-Formats

`number-formats.floating.format` = "#,##0.00"

`number-formats.floating.locale` = "en-US"

`number-formats.integral.format` = "#,##0"

`number-formats.integral.locale` = "en-US"

## Options

`options.actionbar.complete` = false

`options.actionbar.progress` = false

`options.allow-quest-cancel` = true

`options.allow-quest-track` = true

`options.bossbar.color.0.0` = "BLUE"

`options.bossbar.complete` = false

`options.bossbar.limit` = -1

`options.bossbar.progress` = false

`options.bossbar.replace-on-limit` = true

`options.bossbar.style.0.0` = "SOLID"

`options.bossbar.time` = 5

`options.categories-enabled` = true

`options.coreprotect-block-lookup-delay` = -1

`options.error-checking.override-errors` = false

`options.global-quest-display-configuration-override` = false

`options.global-task-configuration-override` = false

`options.gui-actions.cancel-quest` = "RIGHT"

`options.gui-actions.start-quest` = "LEFT"

`options.gui-actions.track-quest` = "DROP"

`options.gui-close-after-accept` = true

`options.gui-confirm-cancel` = true

`options.gui-hide-categories-nopermission` = false

`options.gui-hide-locked` = false

`options.gui-hide-quests-nopermission` = false

`options.gui-truncate-requirements` = true

`options.gui-use-placeholderapi` = false

`options.guinames.daily-quests` = "Daily Quests"

`options.guinames.quest-cancel` = "Cancel Quest"

`options.guinames.quests-category` = "Quests Categories"

`options.guinames.quests-menu` = "Quests"

`options.guinames.quests-started-menu` = "Started Quests"

`options.mobkilling-use-wildstacker-hook` = true

`options.performance-tweaking.quest-autosave-interval` = 12000

`options.performance-tweaking.quest-queue-executor-interval` = 1

`options.placeholder-cache-time` = 10

`options.placeholderapi-global-refresh-ticks` = 30

`options.playerblocktracker-class-name` = "com.gestankbratwurst.playerblocktracker.PlayerBlockTracker"

`options.progress-use-placeholderapi` = false

`options.quest-autostart` = false

`options.quest-autotrack` = true

`options.quest-limit.default` = 2

`options.quests-use-placeholderapi` = false

`options.record-log-history` = true

`options.sounds.gui.interact` = ""

`options.sounds.gui.open` = "ITEM_BOOK_PAGE_TURN:1:3"

`options.sounds.quest-cancel` = "UI_TOAST_OUT:2:3"

`options.sounds.quest-complete` = "UI_TOAST_CHALLENGE_COMPLETE:1.25:3"

`options.sounds.quest-start` = "ENTITY_PLAYER_LEVELUP:2:3"

`options.storage.database-settings.connection-pool-settings.connection-timeout` = 5000

`options.storage.database-settings.connection-pool-settings.idle-timeout` = 600000

`options.storage.database-settings.connection-pool-settings.keepalive-time` = 0

`options.storage.database-settings.connection-pool-settings.maximum-lifetime` = 1800000

`options.storage.database-settings.connection-pool-settings.maximum-pool-size` = 8

`options.storage.database-settings.connection-pool-settings.minimum-idle` = 8

`options.storage.database-settings.network.address` = "135.181.212.169:3369"

`options.storage.database-settings.network.database` = "asmp_SQL"

`options.storage.database-settings.network.password` = "SQLdb2024!"

`options.storage.database-settings.network.username` = "sqlworkerSMP"

`options.storage.provider` = "mysql"

`options.storage.synchronisation.delay-loading` = 0

`options.tab-completion.enabled` = true

`options.task-type-exclusions` = []

`options.titles-enabled` = true

`options.trim-gui-size.quests-category-menu` = true

`options.trim-gui-size.quests-menu` = true

`options.trim-gui-size.quests-started-menu` = true

`options.use-progress-as-fallback` = true

`options.verbose-logging-level` = 2

`options.verify-quest-exists-on-load` = true

## Quest-Mode

`quest-mode.mode` = "NORMAL"

## Titles

`titles.quest-complete.subtitle` = "&7{quest}"

`titles.quest-complete.title` = "&cQuest Complete"

`titles.quest-start.subtitle` = "&7{quest}"

`titles.quest-start.title` = "&cQuest Started"

