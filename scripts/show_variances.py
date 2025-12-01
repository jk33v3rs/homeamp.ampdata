import json

data = json.load(open('utildata/variable_configs_analysis_UPDATED.json'))

print('=' * 80)
print('VARIABLE CONFIGS - DETAILED BREAKDOWN (23 plugins)')
print('=' * 80)
print()

for plugin, configs in sorted(data.items()):
    servers_per_config = [list(cfg.keys()) for cfg in configs.values()]
    all_servers = set()
    for server_list in servers_per_config:
        all_servers.update(server_list)
    
    print(f'{plugin}:')
    print(f'  Config keys with variances: {len(configs)}')
    print(f'  Deployed on: {len(all_servers)} servers')
    print(f'  Variable config keys:')
    
    for config_key in sorted(configs.keys())[:10]:  # Show first 10
        unique_values = len(set(str(v) for v in configs[config_key].values()))
        server_count = len(configs[config_key])
        print(f'    - {config_key}: {unique_values} different values across {server_count} servers')
    
    if len(configs) > 10:
        print(f'    ... and {len(configs) - 10} more config keys')
    
    print()
