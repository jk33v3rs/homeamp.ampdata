# Plan - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## Customized_Files

`Customized_files.Path` = "web"

## Data_Gathering

`Data_gathering.Accept_GeoLite2_EULA` = true

`Data_gathering.Commands.Log_aliases_as_main_command` = true

`Data_gathering.Commands.Log_unknown` = false

`Data_gathering.Disk_space` = true

`Data_gathering.Geolocation_Download_URL` = "https://geodb.playeranalytics.net/GeoLite2-Country.mmdb"

`Data_gathering.Geolocations` = true

`Data_gathering.Join_addresses.Enabled` = true

`Data_gathering.Join_addresses.Filter_out_from_data` = ['play.example.com']

`Data_gathering.Join_addresses.Preserve_case` = false

`Data_gathering.Join_addresses.Preserve_invalid` = false

`Data_gathering.Ping` = true

## Database

`Database.MySQL.Database` = "asmp_SQL"

`Database.MySQL.Host` = "135.181.212.169"

`Database.MySQL.Launch_options` = "?rewriteBatchedStatements=true&serverTimezone=UTC"

`Database.MySQL.Max_Lifetime.Time` = 25

`Database.MySQL.Max_Lifetime.Unit` = "MINUTES"

`Database.MySQL.Max_connections` = 8

`Database.MySQL.Password` = "SQLdb2024!"

`Database.MySQL.Port` = 3369

`Database.MySQL.User` = "sqlworkerSMP"

`Database.Type` = "MySQL"

## Display_Options

`Display_options.Command_colors.Highlight` = "&f"

`Display_options.Command_colors.Main` = "&2"

`Display_options.Command_colors.Secondary` = "&7"

`Display_options.Graphs.Disk_space.High_threshold` = 500

`Display_options.Graphs.Disk_space.Medium_threshold` = 100

`Display_options.Graphs.Show_gaps_in_data` = false

`Display_options.Graphs.TPS.High_threshold` = 18

`Display_options.Graphs.TPS.Medium_threshold` = 10

`Display_options.Open_player_links_in_new_tab` = false

`Display_options.Player_head_image_url` = "https://crafatar.com/avatars/${playerUUID}?size=120&default=MHF_Steve&overlay"

`Display_options.Players_table.Show_on_players_page` = 25000

`Display_options.Players_table.Show_on_server_page` = 2500

`Display_options.Sessions.Order_world_pies_by_percentage` = false

`Display_options.Sessions.Show_on_page` = 50

`Display_options.Theme` = "default"

## Export

`Export.Export_player_on_login_and_logout` = false

`Export.HTML_Export_path` = "Analysis Results"

`Export.JSON_Export_path` = "Raw JSON"

`Export.Parts.Player_JSON` = false

`Export.Parts.Player_pages` = false

`Export.Parts.Players_page` = false

`Export.Parts.Server_JSON` = false

`Export.Parts.Server_page` = false

`Export.Server_refresh_period.Time` = 20

`Export.Server_refresh_period.Unit` = "MINUTES"

## Formatting

`Formatting.Dates.Full` = "YYYY MM dd, HH:mm:ss"

`Formatting.Dates.JustClock` = "HH:mm:ss"

`Formatting.Dates.NoSeconds` = "YYYY MM dd, HH:mm"

`Formatting.Dates.Show_recent_day_names` = true

`Formatting.Dates.Show_recent_day_names_date_pattern` = "YYYY/MM/dd"

`Formatting.Dates.TimeZone` = "UTC"

`Formatting.Decimal_points` = "#.##"

`Formatting.Time_amount.Day` = "1d "

`Formatting.Time_amount.Days` = "%days%d "

`Formatting.Time_amount.Hours` = "%hours%h "

`Formatting.Time_amount.Minutes` = "%minutes%m "

`Formatting.Time_amount.Month` = "1 month, "

`Formatting.Time_amount.Months` = "%months% months, "

`Formatting.Time_amount.Seconds` = "%seconds%s"

`Formatting.Time_amount.Year` = "1 year, "

`Formatting.Time_amount.Years` = "%years% years, "

`Formatting.Time_amount.Zero` = "0s"

## Plugin

`Plugin.Configuration.Allow_proxy_to_manage_settings` = true

`Plugin.Logging.Create_new_locale_file_on_next_enable` = false

`Plugin.Logging.Delete_logs_after_days` = 7

`Plugin.Logging.Dev` = false

`Plugin.Logging.Locale` = "default"

`Plugin.Logging.Log_untranslated_locale_keys` = false

`Plugin.Update_notifications.Check_for_updates` = true

`Plugin.Update_notifications.Notify_about_DEV_releases` = false

## Plugins

`Plugins.Buycraft.Secret` = "-"

`Plugins.CMI.Enabled` = true

`Plugins.Economy (Vault).Enabled` = true

`Plugins.Factions.HideFactions` = ['ExampleFaction']

`Plugins.HuskSync.Enabled` = true

`Plugins.HuskTowns.Enabled` = true

`Plugins.Jobs.Enabled` = true

`Plugins.LuckPerms.Enabled` = true

`Plugins.Permission Groups (Vault).Enabled` = true

`Plugins.PlaceholderAPI.Enabled` = true

`Plugins.PlaceholderAPI.Load_these_placeholders_on_join` = ['%plan_server_uuid%']

`Plugins.PlaceholderAPI.Skip_storing_invalid_placeholder_values` = ['Missing player info']

`Plugins.PlaceholderAPI.Tracked_player_placeholders` = ['%example_placeholder%']

`Plugins.QuickShop-Hikari.Enabled` = false

`Plugins.Towny.HideTowns` = ['ExampleTown']

`Plugins.ViaVersion.Enabled` = true

`Plugins.mcMMO.Enabled` = true

## Time

`Time.Delays.Ping_player_join_delay.Time` = 30

`Time.Delays.Ping_player_join_delay.Unit` = "SECONDS"

`Time.Delays.Ping_server_enable_delay.Time` = 300

`Time.Delays.Ping_server_enable_delay.Unit` = "SECONDS"

`Time.Delays.Wait_for_DB_Transactions_on_disable.Time` = 20

`Time.Delays.Wait_for_DB_Transactions_on_disable.Unit` = "SECONDS"

`Time.Periodic_tasks.Check_DB_for_server_config_files_every.Time` = 1

`Time.Periodic_tasks.Check_DB_for_server_config_files_every.Unit` = "MINUTES"

`Time.Periodic_tasks.Clean_Database_every.Time` = 1

`Time.Periodic_tasks.Clean_Database_every.Unit` = "HOURS"

`Time.Periodic_tasks.Extension_data_refresh_every.Time` = 1

`Time.Periodic_tasks.Extension_data_refresh_every.Unit` = "HOURS"

`Time.Thresholds.AFK_threshold.Time` = 5

`Time.Thresholds.AFK_threshold.Unit` = "MINUTES"

`Time.Thresholds.Activity_index.Playtime_threshold.Time` = 30

`Time.Thresholds.Activity_index.Playtime_threshold.Unit` = "MINUTES"

`Time.Thresholds.Remove_disabled_extension_data_after.Time` = 2

`Time.Thresholds.Remove_disabled_extension_data_after.Unit` = "DAYS"

`Time.Thresholds.Remove_inactive_player_data_after.Time` = 3650

`Time.Thresholds.Remove_inactive_player_data_after.Unit` = "DAYS"

`Time.Thresholds.Remove_ping_data_after.Time` = 14

`Time.Thresholds.Remove_ping_data_after.Unit` = "DAYS"

`Time.Thresholds.Remove_time_series_data_after.Time` = 3650

`Time.Thresholds.Remove_time_series_data_after.Unit` = "DAYS"

## Webserver

`Webserver.Alternative_IP.Address` = "plan.archivesmp.com:%port%"

`Webserver.Alternative_IP.Enabled` = true

`Webserver.Cache.Invalidate_disk_cache_after.Time` = 2

`Webserver.Cache.Invalidate_disk_cache_after.Unit` = "DAYS"

`Webserver.Cache.Invalidate_memory_cache_after.Time` = 5

`Webserver.Cache.Invalidate_memory_cache_after.Unit` = "MINUTES"

`Webserver.Cache.Invalidate_query_results_on_disk_after.Time` = 7

`Webserver.Cache.Invalidate_query_results_on_disk_after.Unit` = "DAYS"

`Webserver.Cache.Reduced_refresh_barrier.Time` = 15

`Webserver.Cache.Reduced_refresh_barrier.Unit` = "SECONDS"

`Webserver.Disable_Webserver` = false

`Webserver.External_Webserver_address` = "https://plan.archvesmp.com"

`Webserver.Internal_IP` = "0.0.0.0"

`Webserver.Public_html_directory` = "public_html"

`Webserver.Security.Access_log.Print_to_console` = false

`Webserver.Security.Access_log.Remove_logs_after_days` = 30

`Webserver.Security.CORS.Allow_origin` = "*"

`Webserver.Security.Cookies_expire_after.Time` = 2

`Webserver.Security.Cookies_expire_after.Unit` = "HOURS"

`Webserver.Security.Disable_authentication` = false

`Webserver.Security.Disable_registration` = false

`Webserver.Security.IP_whitelist.Enabled` = false

`Webserver.Security.IP_whitelist.Whitelist` = ['127.0.0.1', '0:0:0:0:0:0:0:1']

`Webserver.Security.SSL_certificate.Alias` = "alias"

`Webserver.Security.SSL_certificate.KeyStore_path` = "Cert.jks"

`Webserver.Security.SSL_certificate.Key_pass` = "default"

`Webserver.Security.SSL_certificate.Store_pass` = "default"

`Webserver.Security.Use_X-Forwarded-For_Header` = false

## World_Aliases

`World_aliases.List.Radlantis` = "Radlantis"

`World_aliases.Regex` = ['Alias for world:^abc$']

