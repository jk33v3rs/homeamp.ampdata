# ExcellentJobs - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## Abuse_Protection

`Abuse_Protection.Ignore_Block_Generation` = ['STONE', 'OBSIDIAN', 'COBBLESTONE']

`Abuse_Protection.Ignore_Fertilized` = ['*']

`Abuse_Protection.Ignore_GameModes` = ['CREATIVE']

`Abuse_Protection.Ignore_SpawnReasons` = ['SPAWNER', 'BUILD_SNOWMAN', 'BUILD_IRONGOLEM', 'EGG', 'SPAWNER_EGG', 'DISPENSE_EGG', 'SLIME_SPLIT']

`Abuse_Protection.Ignore_Vehicles` = false

`Abuse_Protection.Track_Player_Blocks` = true

## Features

`Features.Boosters` = true

## General

`General.Default_Menu_Command` = true

`General.Disabled_Worlds` = ['another_world', 'my_world']

`General.Payment.Instant` = false

`General.Payment.Interval` = 900

`General.ProgressBar.ActionBar.Enabled` = false

`General.ProgressBar.ActionBar.Text` = "<gray><lyellow><b>%job_name% Job</b></lyellow> (Lv. <white>%job_level%</white>) | <lred>+%exp% XP</lred> | <lgreen>+%income%</lgreen></gray>"

`General.ProgressBar.BossBar.Enabled` = true

`General.ProgressBar.Enabled` = true

`General.ProgressBar.StayTime` = 8

`General.ProgressBar.Style` = "SOLID"

`General.ProgressBar.Title` = "<gray><lyellow><b>%job_name% Job</b></lyellow> (Lv. <white>%job_level%</white>) | <lred>+%exp% XP</lred> | <lgreen>+%income%</lgreen></gray>"

## Jobs

`Jobs.Cooldown.OnJoin` = true

`Jobs.Cooldown.OnLeave` = true

`Jobs.Cooldown.Values.Default_Value` = 86400

`Jobs.Cooldown.Values.Mode` = "RANK"

`Jobs.Cooldown.Values.Permission_Prefix` = ""

`Jobs.Cooldown.Values.Values.admin` = 0

`Jobs.Cooldown.Values.Values.vip` = 42200

`Jobs.DailyLimits.Reset_At_Midnight` = true

`Jobs.Details.Enchant.Multiplier_By_Level_Cost` = 1.0

`Jobs.Leave_Reset_Progress` = true

`Jobs.Leave_When_Lost_Permission` = true

`Jobs.Primary_Amount.Default_Value` = -1

`Jobs.Primary_Amount.Mode` = "RANK"

`Jobs.Primary_Amount.Permission_Prefix` = "excellentjobs.jobs.primary."

`Jobs.Primary_Amount.Values.default` = -1

`Jobs.Secondary_Amount.Default_Value` = -1

`Jobs.Secondary_Amount.Mode` = "RANK"

`Jobs.Secondary_Amount.Permission_Prefix` = "excellentjobs.jobs.secondary."

`Jobs.Secondary_Amount.Values.default` = -1

## Leveling

`Leveling.Fireworks` = true

## Levelledmobs

`LevelledMobs.Integration.KillEntity.Enabled` = true

`LevelledMobs.Integration.KillEntity.Multiplier` = 1.0

## Specialorders

`SpecialOrders.Cooldown` = 86400

`SpecialOrders.Enabled` = true

`SpecialOrders.Max_Amount` = 3

`SpecialOrders.Rewards.item_ingots.Commands` = ['give %player_name% iron_ingot 64', 'give %player_name% gold_ingot 64']

`SpecialOrders.Rewards.item_ingots.Name` = "Irong Ingot (x64), Gold Ingot (x64)"

`SpecialOrders.Rewards.money_10000.Commands` = ['eco give %player_name% 10000']

`SpecialOrders.Rewards.money_10000.Name` = "$10000"

`SpecialOrders.Rewards.money_15000.Commands` = ['eco give %player_name% 15000']

`SpecialOrders.Rewards.money_15000.Name` = "$15000"

`SpecialOrders.Rewards.money_5000.Commands` = ['eco give %player_name% 5000']

`SpecialOrders.Rewards.money_5000.Name` = "$5000"

## Statistic

`Statistic.Enabled` = true

`Statistic.Entries_Per_Page` = 10

`Statistic.Update_Interval` = 600

## Zones

`Zones.Control_Entrance` = true

`Zones.Enabled` = true

`Zones.Highlighting.CornerBlock` = "WHITE_STAINED_GLASS"

`Zones.Highlighting.WireBlock` = "CHAIN"

`Zones.RegenerationTask.Interval` = 5

`Zones.Strict_Mode` = false

`Zones.WandItem.Display_Name` = "<lyellow><b>Zone Wand</b></lyellow>"

`Zones.WandItem.Lore` = ['<dgray>(Drop to exit selection mode)</dgray>', '', '<lyellow>[▶] </lyellow><lgray>Left-Click to <lyellow>set 1st</lyellow> point.</lgray>', '<lyellow>[▶] </lyellow><lgray>Right-Click to <lyellow>set 2nd</lyellow> point.</lgray>']

`Zones.WandItem.Material` = "minecraft:blaze_rod"

