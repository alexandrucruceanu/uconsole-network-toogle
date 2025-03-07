# Installation and Usage Guide

## Error: No module named '_tkinter'

If you're seeing this error, it means the Tkinter Python library is not installed on your system. You have two options:

## Option 1: Use the CLI or Command-Line Versions (Recommended)

We've created two versions that don't require Tkinter:

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

## Option 2: Install Tkinter to Use the GUI Version

If you want to use the GUI version, you can install Tkinter on Kali Linux:

```
sudo apt update
sudo apt install python3-tk
```

After installation, you can run the GUI version:
```
./network_toggle_linux.sh
```

## Troubleshooting

If you encounter any issues:

1. Make sure all scripts are executable:
   ```
   chmod +x *.sh *.py
   ```

2. Check that your 4G module is properly connected and the SIM card is inserted correctly.

3. Verify that the APN settings match your provider (currently set to "internet.digimobil.es" for Digi Spain).

4. If you're having issues with the 4G connection, try running the commands manually to see more detailed error messages:
   ```
   sudo uconsole-4g enable  # or uconsole-4g-cm4 enable
   echo -en "AT+CUSBPIDSWITCH?\r\n" | sudo socat - /dev/ttyUSB2,crnl
   sudo nmcli connection add type gsm ifname ttyUSB2 con-name 4gnet apn internet.digimobil.es
   sudo nmcli connection up 4gnet
   ```
