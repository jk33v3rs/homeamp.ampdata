# QSFindItemAddOn - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## General

`blacklisted-materials` = ['BARRIER', 'STRUCTURE_BLOCK', 'COMMAND_BLOCK', 'CHAIN_COMMAND_BLOCK', 'REPEATING_COMMAND_BLOCK', 'COMMAND_BLOCK_MINECART', 'JIGSAW', 'DEBUG_STICK', 'LIGHT', 'STRUCTURE_VOID']

`blacklisted-worlds` = ['world_number_1', 'world_number_2']

`config-version` = 21

`debug-mode` = false

`ignore-empty-chests` = true

`nearest-warp-mode` = 1

`plugin-prefix` = "&8[&a&lShop Search&8] &r"

`search-loaded-shops-only` = false

`shop-gui-item-lore` = ['', '&fPrice: &a${ITEM_PRICE} per {ITEM_STACK_SIZE} item(s)', '&fStock/Space: &7{SHOP_STOCK}', '&fOwner: &7{SHOP_OWNER}', '&fLocation: &7{SHOP_LOC}', '&fWorld: &7{SHOP_WORLD}', '&fWarp: &7{NEAREST_WARP}', '&fShop Visits: &7{SHOP_VISITS}', '']

`shop-player-visit-cooldown-in-minutes` = 5

`shop-search-gui-title` = "&l» &rShops"

`shop-sorting-method` = 2

`suppress-update-notifications` = false

## Bentobox

`bentobox.ignore-locked-island-shops` = true

## Find-Item-Command

`find-item-command.command-alias` = ['searchshop', 'shopsearch', 'searchitem']

`find-item-command.disable-search-all-shops` = false

`find-item-command.find-item-command-no-permission-message` = "&cNo permission!"

`find-item-command.hideshop-autocomplete` = "hideshop"

`find-item-command.hiding-shop-owner-invalid-message` = "&cThat shop is not yours!"

`find-item-command.incorrect-usage-message` = "&cIncorrect usage! Try &e/finditem &a{TO-BUY | TO-SELL} &6{item type | item name}"

`find-item-command.invalid-material-message` = "&cEither no shops were found or you provided an invalid item! &fTry selecting from autofill."

`find-item-command.invalid-shop-block-message` = "&cThe block you are looking at is not a shop!"

`find-item-command.no-shop-found-message` = "&7No shops found!"

`find-item-command.remove-hideshop-revealshop-subcommands` = false

`find-item-command.revealshop-autocomplete` = "revealshop"

`find-item-command.shop-already-hidden-message` = "&cThis shop is already hidden!"

`find-item-command.shop-already-public-message` = "&cThis shop is already public!"

`find-item-command.shop-hide-success-message` = "&aShop is now hidden from search list!"

`find-item-command.shop-reveal-success-message` = "&aShop is no longer hidden from search list!"

`find-item-command.shop-search-loading-message` = "&7Searching..."

`find-item-command.to-buy-autocomplete` = "TO_BUY"

`find-item-command.to-sell-autocomplete` = "TO_SELL"

## Player-Shop-Teleportation

`player-shop-teleportation.custom-commands.commands-list` = ['tp {PLAYER} {SHOP_LOC_X} {SHOP_LOC_Y} {SHOP_LOC_Z}', 'eco give {PLAYER_NAME} 1000000']

`player-shop-teleportation.custom-commands.run-custom-commands` = false

`player-shop-teleportation.direct-shop-tp-mode.click-to-teleport-message` = "&6&lClick to teleport to the shop!"

`player-shop-teleportation.direct-shop-tp-mode.shop-tp-no-permission-message` = "&cYou don't have permission to teleport to shop!"

`player-shop-teleportation.direct-shop-tp-mode.tp-delay-in-seconds` = 0

`player-shop-teleportation.direct-shop-tp-mode.tp-delay-message` = "&6You will be teleported in &c{DELAY} &6seconds..."

`player-shop-teleportation.direct-shop-tp-mode.tp-player-directly-to-shop` = true

`player-shop-teleportation.direct-shop-tp-mode.tp-to-own-shop-no-permission-message` = "&cYou cannot teleport to your own shop!"

`player-shop-teleportation.direct-shop-tp-mode.unsafe-shop-area-message` = "&cThe area around the shop is unsafe!"

`player-shop-teleportation.nearest-warp-tp-mode.do-not-tp-if-warp-locked` = true

`player-shop-teleportation.nearest-warp-tp-mode.no-residence-near-shop-error-message` = "&cNo residence near this shop"

`player-shop-teleportation.nearest-warp-tp-mode.no-warp-near-shop-error-message` = "&cNo warp near this shop"

`player-shop-teleportation.nearest-warp-tp-mode.no-wg-region-near-shop-error-message` = "&cNo WG Region near this shop"

`player-shop-teleportation.nearest-warp-tp-mode.only-show-player-owned-warps` = true

`player-shop-teleportation.nearest-warp-tp-mode.tp-player-to-nearest-warp` = false

`player-shop-teleportation.nearest-warp-tp-mode.use-residence-subzones` = false

## Shop-Gui

`shop-gui.back-button-material` = "RED_CONCRETE"

`shop-gui.back-button-text` = "&7&l« &cBack"

`shop-gui.close-button-material` = "BARRIER"

`shop-gui.close-button-text` = "&fClose Search"

`shop-gui.custom-model-data.back-button-custom-model-data` = ""

`shop-gui.custom-model-data.close-button-custom-model-data` = ""

`shop-gui.custom-model-data.filler-item-custom-model-data` = ""

`shop-gui.custom-model-data.goto-first-page-button-custom-model-data` = ""

`shop-gui.custom-model-data.goto-last-page-button-custom-model-data` = ""

`shop-gui.custom-model-data.next-button-custom-model-data` = ""

`shop-gui.filler-item` = "GRAY_STAINED_GLASS_PANE"

`shop-gui.goto-first-page-button-material` = ""

`shop-gui.goto-first-page-button-text` = "&7&l« &cGo to First Page"

`shop-gui.goto-last-page-button-material` = ""

`shop-gui.goto-last-page-button-text` = "&aGo to Last Page &7&l»"

`shop-gui.next-button-material` = "GREEN_CONCRETE"

`shop-gui.next-button-text` = "&aNext &7&l»"

`shop-gui.shop-navigation.first-page-alert-message` = "&cYou are already on first page!"

`shop-gui.shop-navigation.last-page-alert-message` = "&cYou are already on last page!"

`shop-gui.use-shorter-currency-format` = true

