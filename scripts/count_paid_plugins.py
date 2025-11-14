import csv

f = open('utildata/Asset Registry ArSMP - Jun25 - Plugins IN USE.csv')
lines = f.readlines()
f.close()

# Skip first 2 header rows
reader = csv.reader(lines[2:])

paid = []
free = []

for row in reader:
    if len(row) > 9 and row[1].strip():
        plugin = row[1].strip()
        source = row[9].strip() if len(row) > 9 else ''
        
        # Check if it's a paid source
        if ('spigot' in source.lower() or 
            'polymart' in source.lower() or 
            'builtbybit' in source.lower() or 
            source.startswith('$') or
            'paid' in source.lower() or
            'premium' in source.lower()):
            paid.append((plugin, source))
        else:
            free.append((plugin, source))

print(f'Paid plugins: {len(paid)}')
for p in paid:
    print(f'  {p[0]}: {p[1]}')

print(f'\nFree plugins: {len(free)}')
print(f'\nTotal: {len(paid) + len(free)}')
