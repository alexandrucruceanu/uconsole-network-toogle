# Installation and Usage Guide

## CLI Tools for uConsole Network Toggle

We've created two command-line tools to manage your network connectivity:

### CLI Version with Interactive Menu

1. Make the script executable:
   ```
   chmod +x network_toggle_cli.sh
   ```

2. Run the CLI application:
   ```
   ./network_toggle_cli.sh
   ```
   
   Or directly with Python:
   ```
   python3 network_toggle_cli.py
   ```

3. Follow the on-screen menu to enable/disable WiFi or mobile data.

### Quick Command-Line Script

1. Make the script executable:
   ```
   chmod +x toggle_network.sh
   ```

2. Use the script with simple commands:
   ```
   ./toggle_network.sh wifi on     # Turn on WiFi
   ./toggle_network.sh wifi off    # Turn off WiFi
   ./toggle_network.sh mobile on   # Turn on mobile data
   ./toggle_network.sh mobile off  # Turn off mobile data
   ./toggle_network.sh status      # Show current status
   ```


## Troubleshooting

### "4G modem not detected" Error

If you get a "4G modem not detected" error even though the modem light is on, use the troubleshooting script:

1. Make the script executable:
   ```
   chmod +x troubleshoot_4g.sh
   ```

2. Run the script as root:
   ```
   sudo ./troubleshoot_4g.sh
   ```

This script will:
- Check for required tools
- Enable the 4G module for your uConsole model
- Test AT commands on different ttyUSB ports
- Find the working port for your modem
- Restart ModemManager
- Check for modem detection
- Set up the network connection
- Provide a detailed summary and next steps

The script will automatically try to fix common issues and will tell you exactly what's working and what's not.

### Other Troubleshooting Steps

If the troubleshooting script doesn't resolve your issue:

1. Make sure all scripts are executable:
   ```
   chmod +x *.sh *.py
   ```

2. Check that your 4G module is properly connected and the SIM card is inserted correctly.

3. Verify that the APN settings match your provider (currently set to "internet.digimobil.es" for Digi Spain).

4. Try rebooting your uConsole and running the troubleshooting script again.

5. If the troubleshooting script identifies a working port that's different from ttyUSB2, edit the scripts to use that port instead.
