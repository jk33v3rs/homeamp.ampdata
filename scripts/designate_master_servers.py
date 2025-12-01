import json

# Load variable configs
with open('utildata/variable_configs_analysis.json') as f:
    variable_data = json.load(f)

print("=== VARIABLE CONFIG PLUGINS - MASTER SERVER RECOMMENDATIONS ===\n")

for plugin in sorted(variable_data.keys()):
    configs = variable_data[plugin]
    
    # Get all servers that have this plugin
    all_servers = set()
    for config_key, server_values in configs.items():
        all_servers.update(server_values.keys())
    
    servers_list = sorted(all_servers)
    
    print(f"\n{plugin}")
    print(f"  Deployed on: {len(servers_list)} servers")
    print(f"  Servers: {', '.join(servers_list)}")
    print(f"  Variable settings: {len(configs)}")
    
    # Recommend master server based on:
    # 1. Production servers (SMP101, SMP201, EMAD01) preferred
    # 2. Or the first alphabetically as fallback
    
    if 'SMP101' in servers_list:
        master = 'SMP101'
        reason = "Primary production SMP server"
    elif 'SMP201' in servers_list:
        master = 'SMP201'
        reason = "Secondary production SMP server"
    elif 'EMAD01' in servers_list:
        master = 'EMAD01'
        reason = "EliteMobs Adventure server"
    elif 'HUB01' in servers_list:
        master = 'HUB01'
        reason = "Network hub server"
    else:
        master = servers_list[0]
        reason = "First alphabetically"
    
    print(f"  🎯 RECOMMENDED MASTER: {master} ({reason})")
    
    # Show sample config differences
    if len(configs) <= 3:
        print(f"  Config variations:")
        for config_key, server_values in configs.items():
            unique_values = len(set(str(v) for v in server_values.values()))
            print(f"    - {config_key}: {unique_values} different value(s)")

print("\n" + "="*70)
print("SUMMARY: Master server recommendations for variable-config plugins")
print("="*70 + "\n")

master_assignments = {}
for plugin in sorted(variable_data.keys()):
    configs = variable_data[plugin]
    servers = set()
    for config_values in configs.values():
        servers.update(config_values.keys())
    servers_list = sorted(servers)
    
    if 'SMP101' in servers_list:
        master = 'SMP101'
    elif 'SMP201' in servers_list:
        master = 'SMP201'
    elif 'EMAD01' in servers_list:
        master = 'EMAD01'
    elif 'HUB01' in servers_list:
        master = 'HUB01'
    else:
        master = servers_list[0]
    
    master_assignments[plugin] = master
    print(f"{plugin:25s} -> {master}")

# Group by master server
print("\n" + "="*70)
print("GROUPED BY MASTER SERVER")
print("="*70 + "\n")

by_master = {}
for plugin, master in master_assignments.items():
    if master not in by_master:
        by_master[master] = []
    by_master[master].append(plugin)

for master in sorted(by_master.keys()):
    plugins = by_master[master]
    print(f"{master}: {len(plugins)} plugins")
    for plugin in plugins:
        print(f"  - {plugin}")
