# ImageFrame - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## General

`Updater` = true

## Hooks

`Hooks.ViaVersion.DisableSmoothAnimationForLegacyPlayers` = false

## Invisibleframe

`InvisibleFrame.GlowEmptyFrames` = true

`InvisibleFrame.MaxConversionsPerSplash` = 8

## Messages

`Messages.AccessPermission.Types.ALL` = "ALL"

`Messages.AccessPermission.Types.EDIT` = "EDIT"

`Messages.AccessPermission.Types.EDIT_CLONE` = "EDIT WITH CLONE"

`Messages.AccessPermission.Types.GET` = "GET"

`Messages.AccessPermission.Types.MARKER` = "MARKER"

`Messages.AccessPermission.Types.NONE` = "NONE"

`Messages.AccessPermission.Updated` = "&aUpdated access for {PlayerName} ({PlayerUUID}), they now have {Permission} permission."

`Messages.DateFormat` = "dd/MM/yyyy HH:mm:ss zzz"

`Messages.DuplicateMapName` = "&cYou've already created an image map with that name!"

`Messages.GivenInvisibleFrame` = "&aGiven {Amount} invisible item frames to {Player}."

`Messages.ImageMapAlreadyQueued` = "&cYou already have another ImageMap queued and processing, please wait!"

`Messages.ImageMapCreated` = "&aImageMap has been created!"

`Messages.ImageMapDeleted` = "&eImageMap had been deleted!"

`Messages.ImageMapPlaybackJumpTo` = "&aJumped to position at {Seconds} seconds!"

`Messages.ImageMapPlayerPurge` = "&ePurged {Amount} ImageMaps owned by {CreatorName} ({CreatorUUID}) - [{ImageMapNames}]"

`Messages.ImageMapProcessing` = "&eImageMap is being processed, please wait!"

`Messages.ImageMapProcessingActionBar` = "&eImageMap &a{Name} &eis being processed{Dots}"

`Messages.ImageMapQueuedActionBar` = "&7ImageMap &a{Name} &eis currently queued ({Position} Remaining)"

`Messages.ImageMapRefreshed` = "&aImageMap has been refreshed!"

`Messages.ImageMapRenamed` = "&aImageMap had been renamed!"

`Messages.ImageMapTogglePaused` = "&aToggled ImageMap playback pause!"

`Messages.ImageOverMaxFileSize` = "&cImageMap cannot be loaded as it is over the max file size allowed. ({Size} bytes)"

`Messages.InvalidImageMap` = "&cThis image map had likely already been deleted."

`Messages.InvalidOverlayMap` = "&cOverlay only works on Vanilla Minecraft maps and without duplicates in selection!"

`Messages.InvalidUsage` = "&cInvalid Usage!"

`Messages.ItemFrameOccupied` = "&cFailed to place or remove some maps on selected ItemFrame, they are either destroyed, replaced, occupied or protected."

`Messages.MapLookup` = "&bList of image maps by {CreatorName} ({CreatorUUID}):"

`Messages.Markers.AddBegin` = "&aRight click on an Item Frame containing the map "{Name}" to place marker! &bRun "/imageframe marker cancel" to cancel placement"

`Messages.Markers.AddConfirm` = "&aMarker placed!"

`Messages.Markers.Cancel` = "&eMarker placement cancelled!"

`Messages.Markers.Clear` = "&eMarkers cleared!"

`Messages.Markers.DuplicateName` = "&cThere is already a marker with that name!"

`Messages.Markers.LimitReached` = "&cYou can only create {Limit} markers on one map!"

`Messages.Markers.NotAMarker` = "&cThat is not a valid marker"

`Messages.Markers.NotRenderOnFrameWarning` = "&eWarning: This marker type does not render on Item Frames!"

`Messages.Markers.Remove` = "&eMarker removed!"

`Messages.NoConsole` = "&cThis command can only be ran by players!"

`Messages.NoPermission` = "&cYou do not have permission to do that!"

`Messages.NotAnImageMap` = "&cThat is not an ImageMap"

`Messages.NotEnoughMaps` = "&cYou do not have {Amount} maps!"

`Messages.NotEnoughSpace` = "&cUnable to place Combined ImageMap as there is not enough room."

`Messages.Oversize` = "&cThat is too big! Max size for a map is {MaxSize}"

`Messages.PlayerCreationLimitReached` = "&cYou can only create {Limit} maps at once! Delete some to create new ones"

`Messages.PlayerNotFound` = "&cThis player cannot be found!"

`Messages.Preferences.Keys.VIEW_ANIMATED_MAPS` = "View Animated Maps"

`Messages.Preferences.UpdateMessage` = "&ePlayer Preference {Preference}&e has been updated to {Value}&e!"

`Messages.Preferences.Values.FALSE` = "&cDisabled"

`Messages.Preferences.Values.TRUE` = "&aEnabled"

`Messages.Preferences.Values.UNSET` = "&7Unset"

`Messages.Reloaded` = "&eImageFrame has been reloaded!"

`Messages.Selection.Begin` = "&bRight click an Item Frame to select corner 1 and 2"

`Messages.Selection.Clear` = "&eLeaving selection mode"

`Messages.Selection.Corner1` = "&aSelected Item Frame corner 1"

`Messages.Selection.Corner2` = "&aSelected Item Frame corner 2"

`Messages.Selection.IncorrectSize` = "&cYour selection's size does not match, {Width} x {Height} required."

`Messages.Selection.Invalid` = "&cInvalid selection!"

`Messages.Selection.NoSelection` = "&cYou don't have a valid selection yet."

`Messages.Selection.Oversize` = "&cOversize selection! Max size for a map is {MaxSize}"

`Messages.Selection.Success` = "&aSelected {Width} x {Height} Item Frames! &eIf any of them are removed/replaced, you will need to select them again."

`Messages.SetCreator` = "&aImageMap creator of id {ImageID} set to {CreatorName} ({CreatorUUID})"

`Messages.URLImageMapInfo` = ['&bImageID: {ImageID}', '&aName: {Name}', '&eMap Size: {Width} x {Height}', '&6Dithering: {DitheringType}', '&dCreator: {CreatorName} ({CreatorUUID})', '&fAccess: {Access}', '&aTime Created: {TimeCreated}', '&bMarkers: {Markers}', '&eURL: {URL}']

`Messages.URLRestricted` = "&cThat URL is restricted and cannot be used to create image maps."

`Messages.UnableToChangeImageType` = "&cChanging the image type is currently not supported. Please create a new image map instead."

`Messages.UnableToLoadMap` = "&cImageMap cannot be loaded, there is a problem while reading the image. Contact server administrators to check the server console for more info."

`Messages.UnknownError` = "&cAn unknown error had occurred."

`Messages.UploadExpired` = "&cImage upload link had expired, please create a new one."

`Messages.UploadLink` = "&aOpen {URL} on your browser to upload an image, it is valid for 5 minutes."

## Settings

`Settings.CacheControlMode` = "MANUAL_PERSISTENT"

`Settings.CombinedMapItem.Lore` = ['&aRight Click on Item Frames of size {Width} x {Height} to place ImageMap', '', '&7ImageID: {ImageID}', '&7Creator: {CreatorName} ({CreatorUUID})', '&7Time Created: {TimeCreated}']

`Settings.CombinedMapItem.Name` = "&bImageMap &f- &f{Name} &7({Width} x {Height})"

`Settings.ExemptMapIdsFromDeletion` = ['-1']

`Settings.HandleAnimatedMapsOnMainThread` = false

`Settings.MapItemFormat` = "&f{Name} &7({X}, {Y})"

`Settings.MapMarkerLimit` = 20

`Settings.MapPacketSendingRateLimit` = -1

`Settings.MapRenderersContextual` = false

`Settings.MaxImageFileSize` = 52428800

`Settings.MaxProcessingTime` = 60

`Settings.MaxSize` = 100

`Settings.ParallelProcessingLimit` = 1

`Settings.RequireEmptyMaps` = true

`Settings.RestrictImageUrl.Enabled` = false

`Settings.RestrictImageUrl.Whitelist` = ['https://i.imgur.com', 'http://i.imgur.com', 'https://storage.googleapis.com', 'http://storage.googleapis.com', 'https://cdn.discordapp.com', 'http://cdn.discordapp.com', 'https://media.discordapp.net', 'http://media.discordapp.net', 'https://textures.minecraft.net', 'http://textures.minecraft.net']

`Settings.SendAnimatedMapsOnMainThread` = false

`Settings.TryDeleteBlankMapFiles` = false

## Uploadservice

`UploadService.Enabled` = true

`UploadService.WebServer.Host` = "0.0.0.0"

