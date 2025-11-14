# CommunityQuests - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## General

`barColor` = "GREEN"

`disableBossBar` = true

`disableDuplicateBreaks` = true

`disableDuplicatePlaces` = true

`donateMenuItem` = "EMERALD"

`leaderBoardSize` = 5

`questLimit` = 5

## Quests

`Quests.BreakStuff.description` = "&fbreak anythingggggg"

`Quests.BreakStuff.displayName` = "Just break stuff"

`Quests.BreakStuff.objectives` = [{'type': 'blockbreak', 'goal': 100, 'description': 'Broken blox'}]

`Quests.BreakStuff.rewards.commands` = ['give %player% diamond_sword 1 0 {display:{Name:"{\\"text\\":\\"Powerful Diamond Sword\\",\\"color\\":\\"aqua\\"}"},ench:[{id:16,lvl:5}]}']

`Quests.BreakStuff.rewards.experience` = 10000

`Quests.Cane.displayItem` = "SUGAR_CANE"

`Quests.Cane.displayName` = "&6Sugar it up"

`Quests.Cane.objectives` = [{'type': 'blockbreak', 'goal': 10, 'materials': ['SUGAR_CANE'], 'description': 'I need some Sugar!'}]

`Quests.Cane.questDuration` = "7d"

`Quests.Cane.rewards.items` = [{'material': 'GRASS_BLOCK', 'amount': 16}]

`Quests.CarrotQuest.description` = "&fPlant some carrots"

`Quests.CarrotQuest.displayItem` = "CARROT"

`Quests.CarrotQuest.displayName` = "&6&lCarrot King"

`Quests.CarrotQuest.objectives` = [{'type': 'blockbreak', 'goal': 25, 'materials': ['carrots'], 'description': '&6&lCarrots'}, {'type': 'blockbreak', 'goal': 10, 'materials': ['wheat'], 'description': '&6&lWheat'}]

`Quests.CarrotQuest.rewards.rankedRewards.*.experience` = 25

`Quests.CarrotQuest.rewards.rankedRewards.*.items` = [{'material': 'stone_sword', 'amount': 1, 'displayName': '&8Stone Sword'}]

`Quests.CarrotQuest.rewards.rankedRewards.1.experience` = 100

`Quests.CarrotQuest.rewards.rankedRewards.1.items` = [{'material': 'diamond_sword', 'amount': 1, 'displayName': '&bPowerful Diamond Sword'}]

`Quests.CarrotQuest.rewards.rankedRewards.2.experience` = 50

`Quests.CarrotQuest.rewards.rankedRewards.2.items` = [{'material': 'iron_sword', 'amount': 1, 'displayName': '&7Iron Sword'}]

`Quests.CarvePumpkin.commands` = ['give %player% diamond_sword 1 0 {display:{Name:"{\\"text\\":\\"Powerful Diamond Sword\\",\\"color\\":\\"aqua\\"}"},Enchantments:[{id:sharpness,lvl:5}]}']

`Quests.CarvePumpkin.description` = "Lets carve some pumpkins for Halloween!"

`Quests.CarvePumpkin.displayName` = "Carve a pumpkin"

`Quests.CarvePumpkin.objectives` = [{'type': 'carvepumpkin', 'goal': 10, 'description': 'pumpkinz'}]

`Quests.CarvePumpkin.rewards.experience` = 10000

`Quests.CraftSwords.description` = "&fCraft 10 swords and 10 sticks!"

`Quests.CraftSwords.displayName` = "&l&aSwords and Sticks!"

`Quests.CraftSwords.objectives` = [{'type': 'craftitem', 'materials': ['DIAMOND_SWORD', 'IRON_SWORD'], 'description': '&bDiamond swords', 'goal': 10}, {'type': 'craftItem', 'materials': ['STICK'], 'goal': 10, 'description': '&bStick'}]

`Quests.CraftSwords.rewards.experience` = 100

`Quests.EatFood.description` = "&fEat 25 apples, potatoes, or mushroom stew!"

`Quests.EatFood.displayName` = "&l&aEat Food"

`Quests.EatFood.objectives` = [{'type': 'consumeitem', 'goal': 25, 'description': '&fFood consumed', 'materials': ['APPLE', 'POTATO', 'Mushroom_Stew']}]

`Quests.EatFood.rewards.experience` = 100

`Quests.EatFood.rewards.items` = [{'material': 'EMERALD', 'amount': 64, 'displayName': '&cEmerald'}]

`Quests.Egg.barColor` = "WHITE"

`Quests.Egg.barStyle` = "SEGMENTED_20"

`Quests.Egg.description` = "H1 needs some cake, you can get some eggs!"

`Quests.Egg.displayItem` = "EGG"

`Quests.Egg.displayName` = "&6Eggcellent"

`Quests.Egg.objectives` = [{'type': 'donate', 'materials': ['EGG']}]

`Quests.Egg.questDuration` = "7d"

`Quests.Egg.rewards.items` = [{'material': 'CHICKEN_SPAWN_EGG', 'amount': 1}]

`Quests.ExpQuest.description` = "&fGet lots of experience"

`Quests.ExpQuest.displayName` = "&c&lGet that EXP"

`Quests.ExpQuest.objectives` = [{'type': 'experience', 'goal': 10000, 'description': 'EXP'}]

`Quests.ExpQuest.rewards.experience` = 10000

`Quests.ExpQuest.rewards.items` = [{'material': 'DIAMOND_SWORD', 'amount': 1, 'displayName': '&bPowerful Diamond Sword'}]

`Quests.FishFrenzy.barColor` = "BLUE"

`Quests.FishFrenzy.barStyle` = "SOLID"

`Quests.FishFrenzy.description` = "&fCatch 8 cod and 4 salmon as fast as you can!"

`Quests.FishFrenzy.displayItem` = "fishing_rod"

`Quests.FishFrenzy.displayName` = "&9&lFishing Frenzy"

`Quests.FishFrenzy.objectives` = [{'type': 'catchfish', 'goal': 8, 'entities': ['Cod'], 'description': '&9&lCod'}, {'type': 'catchfish', 'goal': 4, 'entities': ['Salmon'], 'description': '&9&lSalmon'}]

`Quests.FishFrenzy.questDuration` = "30m"

`Quests.FishFrenzy.rewards.rankedRewards.*.experience` = 25

`Quests.FishFrenzy.rewards.rankedRewards.*.items` = [{'material': 'stone_sword', 'amount': 1, 'displayName': '&8Stone Sword'}]

`Quests.FishFrenzy.rewards.rankedRewards.1.experience` = 100

`Quests.FishFrenzy.rewards.rankedRewards.1.items` = [{'material': 'diamond_sword', 'amount': 1, 'displayName': '&bPowerful Diamond Sword'}]

`Quests.FishFrenzy.rewards.rankedRewards.2.experience` = 50

`Quests.FishFrenzy.rewards.rankedRewards.2.items` = [{'material': 'iron_sword', 'amount': 1, 'displayName': '&7Iron Sword'}]

`Quests.GuiQuest.description` = "&fDonate 60 potatoes and 20 diamonds with /cq donate!"

`Quests.GuiQuest.displayName` = "&a&lPotato Diamond Quest"

`Quests.GuiQuest.objectives` = [{'type': 'donate', 'goal': 60, 'materials': ['POTATO'], 'description': '&l&aPotatoes'}, {'type': 'donate', 'goal': 20, 'materials': ['DIAMOND'], 'description': '&l&aDiamonds'}]

`Quests.GuiQuest.rewards.rankedRewards.*.experience` = 25

`Quests.GuiQuest.rewards.rankedRewards.*.items` = [{'material': 'stone_sword', 'amount': 1, 'displayName': '&8Stone Sword'}]

`Quests.GuiQuest.rewards.rankedRewards.1.commands` = ['give %player% diamond_sword 1']

`Quests.GuiQuest.rewards.rankedRewards.1.experience` = 100

`Quests.GuiQuest.rewards.rankedRewards.1.items` = [{'material': 'DIAMOND_SWORD', 'amount': 1, 'displayName': '&bPowerful Diamond Sword'}]

`Quests.GuiQuest.rewards.rankedRewards.2.experience` = 50

`Quests.GuiQuest.rewards.rankedRewards.2.items` = [{'material': 'iron_sword', 'amount': 1, 'displayName': '&7Iron Sword'}]

`Quests.MoveIt.barColor` = "WHITE"

`Quests.MoveIt.barStyle` = "SEGMENTED_20"

`Quests.MoveIt.description` = "Just keep on running until your shoes fall off!"

`Quests.MoveIt.displayItem` = "DIAMOND_BOOTS"

`Quests.MoveIt.displayName` = "&6Movement Quest"

`Quests.MoveIt.objectives` = [{'type': 'movement'}]

`Quests.MoveIt.questDuration` = "7d"

`Quests.MoveIt.rewards.items` = [{'material': 'CHICKEN_SPAWN_EGG', 'amount': 1}]

`Quests.MythicQuest.description` = "&c&lKill 4 Cave Spiders!"

`Quests.MythicQuest.displayName` = "&c&lKill mythic mobs"

`Quests.MythicQuest.objective` = [{'type': 'mythicmob', 'goal': 4, 'description': 'Spiderz', 'entities': ['CAVE_SPIDER']}]

`Quests.MythicQuest.rewards.experience` = 10000

`Quests.MythicQuest.rewards.items` = [{'material': 'DIAMOND_SWORD', 'amount': 1, 'displayName': '&bPowerful Diamond Sword'}]

`Quests.PlantTree.description` = "&fPlant 10 oak or acacia trees and break 10 logs!"

`Quests.PlantTree.displayName` = "&a&lSave the Planet"

`Quests.PlantTree.objectives` = [{'type': 'blockplace', 'materials': ['OAK_SAPLING', 'ACACIA_SAPLING'], 'description': '&fPlant trees', 'goal': 10}, {'type': 'blockbreak', 'materials': ['OAK_LOG', 'ACACIA_LOG', 'FIRE'], 'goal': 10, 'description': '&fChop trees'}]

`Quests.PlantTree.rewards.experience` = 100

`Quests.PlantTree.rewards.items` = [{'material': 'EMERALD', 'amount': 64, 'displayName': '&cEmerald'}]

`Quests.TestQuest.barColor` = "GREEN"

`Quests.TestQuest.barStyle` = "SEGMENTED_20"

`Quests.TestQuest.description` = "Kill 100 zombies and pigs! 
Kill 50 skeletons!"

`Quests.TestQuest.displayItem` = "ZOMBIE_HEAD"

`Quests.TestQuest.displayName` = "&cZombie and Pig Slayer"

`Quests.TestQuest.objectives` = [{'type': 'mobkill', 'dynamicGoal': '%server_online%', 'entities': ['Zombie', 'Pig', 'ZOMBIFIED_PIGLIN'], 'description': 'Zombies & Pigs'}, {'type': 'mobkill', 'goal': 5, 'customMobNames': ['Skeleton'], 'description': 'Skeletons'}]

`Quests.TestQuest.questDuration` = "1d"

`Quests.TestQuest.rewards.rankedRewards.*.experience` = 25

`Quests.TestQuest.rewards.rankedRewards.*.items` = [{'material': 'stone_sword', 'amount': 1, 'displayName': '&8Stone Sword'}]

`Quests.TestQuest.rewards.rankedRewards.1.experience` = 100

`Quests.TestQuest.rewards.rankedRewards.1.items` = [{'material': 'diamond_sword', 'amount': 1, 'displayName': '&bPowerful Diamond Sword'}]

`Quests.TestQuest.rewards.rankedRewards.2.experience` = 50

`Quests.TestQuest.rewards.rankedRewards.2.items` = [{'material': 'iron_sword', 'amount': 1, 'displayName': '&7Iron Sword'}]

## Hologram

`hologram.enabled` = true

`hologram.refresh-interval` = 60

`hologram.text` = ['<#B22AFE>&l&nCommunity Quests</#ff8157>', '&f&lRight click to view quests', '%communityquests_name%', '%communityquests_description%', '%communityquests_top_all%']

