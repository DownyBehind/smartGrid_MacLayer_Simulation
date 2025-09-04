#!/usr/bin/env python3
"""
Script to format all JSON files in the config directory
"""
import json
import os
import glob

def format_json_file(filepath):
    """Format a single JSON file with proper indentation"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Formatted: {os.path.basename(filepath)}")
        return True
    except Exception as e:
        print(f"✗ Error formatting {filepath}: {e}")
        return False

def main():
    config_dir = "simulator_simpleAndQuick/config"
    
    if not os.path.exists(config_dir):
        print(f"Config directory not found: {config_dir}")
        return
    
    # Find all JSON files
    json_files = glob.glob(os.path.join(config_dir, "*.json"))
    
    if not json_files:
        print("No JSON files found in config directory")
        return
    
    print(f"Found {len(json_files)} JSON files to format...")
    print()
    
    success_count = 0
    for json_file in sorted(json_files):
        if format_json_file(json_file):
            success_count += 1
    
    print()
    print(f"Successfully formatted {success_count}/{len(json_files)} files")

if __name__ == "__main__":
    main()
