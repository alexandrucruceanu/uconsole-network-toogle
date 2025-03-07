#!/bin/bash

# Cleanup script to remove GUI-related files
echo "Removing GUI-related files..."

# Remove GUI Python script
if [ -f network_toggle.py ]; then
  rm network_toggle.py
  echo "Removed network_toggle.py"
fi

# Remove GUI shell scripts
if [ -f network_toggle.sh ]; then
  rm network_toggle.sh
  echo "Removed network_toggle.sh"
fi

if [ -f network_toggle_linux.sh ]; then
  rm network_toggle_linux.sh
  echo "Removed network_toggle_linux.sh"
fi

if [ -f network_toggle.bat ]; then
  rm network_toggle.bat
  echo "Removed network_toggle.bat"
fi

echo "Cleanup complete. Only CLI tools remain."
echo ""
echo "Available tools:"
echo "1. network_toggle_cli.py - Interactive CLI menu"
echo "2. network_toggle_cli.sh - Shell script to run the CLI menu"
echo "3. toggle_network.sh - Quick command-line toggle script"
echo "4. troubleshoot_4g.sh - Troubleshooting script for 4G issues"
echo ""
echo "For usage instructions, see README.md and INSTALL.md"
