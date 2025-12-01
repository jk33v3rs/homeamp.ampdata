#!/usr/bin/env python3
"""
Package expectations data for deployment to production servers.

This script prepares the configuration expectations (baselines) that will be
deployed alongside the agent software on both Hetzner and OVH servers.

Expectations = what configs SHOULD look like
Reality = what configs ACTUALLY look like on servers

The agent compares expectations vs reality to detect drift.
"""

import json
import shutil
from pathlib import Path

# Paths
HOMEAMP_ROOT = Path(__file__).parent.parent
UTILDATA = HOMEAMP_ROOT / "utildata"
SOFTWARE = HOMEAMP_ROOT / "software" / "homeamp-config-manager"
EXPECTATIONS_DIR = SOFTWARE / "data" / "expectations"

# Source files
UNIVERSAL_CONFIGS = UTILDATA / "universal_configs_analysis.json"
VARIABLE_CONFIGS = UTILDATA / "variable_configs_analysis_UPDATED.json"

def main():
    print("=" * 70)
    print("ArchiveSMP Config Manager - Package Expectations Data")
    print("=" * 70)
    print()
    
    # Check source files exist
    if not UNIVERSAL_CONFIGS.exists():
        print(f"❌ ERROR: Universal configs file not found:")
        print(f"   {UNIVERSAL_CONFIGS}")
        return False
    
    if not VARIABLE_CONFIGS.exists():
        print(f"❌ ERROR: Variable configs file not found:")
        print(f"   {VARIABLE_CONFIGS}")
        return False
    
    print("✓ Found source expectations files")
    print(f"  - {UNIVERSAL_CONFIGS.name}")
    print(f"  - {VARIABLE_CONFIGS.name}")
    print()
    
    # Load and validate
    try:
        with open(UNIVERSAL_CONFIGS, 'r') as f:
            universal_data = json.load(f)
        print(f"✓ Loaded {len(universal_data)} universal plugin configs")
        
        with open(VARIABLE_CONFIGS, 'r') as f:
            variable_data = json.load(f)
        print(f"✓ Loaded {len(variable_data)} variable plugin configs")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: Failed to load expectations files: {e}")
        return False
    
    # Create expectations directory
    EXPECTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created expectations directory:")
    print(f"  {EXPECTATIONS_DIR}")
    print()
    
    # Copy files
    try:
        dest_universal = EXPECTATIONS_DIR / "universal_configs.json"
        dest_variable = EXPECTATIONS_DIR / "variable_configs.json"
        
        shutil.copy2(UNIVERSAL_CONFIGS, dest_universal)
        print(f"✓ Copied universal configs to:")
        print(f"  {dest_universal}")
        
        shutil.copy2(VARIABLE_CONFIGS, dest_variable)
        print(f"✓ Copied variable configs to:")
        print(f"  {dest_variable}")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: Failed to copy files: {e}")
        return False
    
    # Create metadata file
    metadata = {
        "version": "1.0.0",
        "created": str(Path(UNIVERSAL_CONFIGS).stat().st_mtime),
        "universal_plugins": len(universal_data),
        "variable_plugins": len(variable_data),
        "total_plugins_tracked": 88,  # 82 universal + 6 paid
        "notes": [
            "Universal configs should be identical across all instances",
            "Variable configs have documented per-server differences",
            "23 plugins have both universal baselines AND documented variances"
        ]
    }
    
    metadata_file = EXPECTATIONS_DIR / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Created metadata file:")
    print(f"  {metadata_file}")
    print()
    
    # Summary
    print("=" * 70)
    print("SUCCESS - Expectations data packaged!")
    print("=" * 70)
    print()
    print("Next steps for deployment:")
    print()
    print("1. Copy entire project to production servers:")
    print("   scp -r software/homeamp-config-manager/ webadmin@135.181.212.169:/home/webadmin/")
    print("   scp -r software/homeamp-config-manager/ webadmin@37.187.143.41:/home/webadmin/")
    print()
    print("2. On production servers, the expectations data will be at:")
    print("   /home/webadmin/archivesmp-config-manager/data/expectations/")
    print()
    print("3. Start services (see DEPLOYMENT_GUIDE.md)")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
