# uConsole Network Toggle

A command-line application to toggle between WiFi and 4G mobile connectivity on the uConsole device running Kali Linux.

## Features

- Toggle between WiFi and 4G mobile connectivity
- Display current connection status and IP address
- Support for both uConsole CM4 and A06/R01 models
- Automatic configuration of 4G connection with Digi Spain APN
- Command-line interface for maximum compatibility

## Requirements

- uConsole with 4G LTE module from Clockwork
- Kali Linux installed
- Python 3
- NetworkManager and ModemManager installed
- SIM card inserted in the 4G module

## Installation

1. Copy all files to your uConsole device
2. Make the shell scripts executable:
   ```
   chmod +x network_toggle_cli.sh toggle_network.sh troubleshoot_4g.sh
   ```

## Usage

### CLI Version with Interactive Menu

1. Run the CLI application:
   ```
   ./network_toggle_cli.sh
   ```
   
   Or directly with Python:
   ```
   python3 network_toggle_cli.py
   ```

2. The application will display a text-based menu:
   - Choose options by entering the corresponding number
   - The current network status is displayed at the top
   - Follow the on-screen instructions to enable/disable networks

### Quick Toggle Script (for command line or scripts)

For quick toggling between networks without an interactive interface:

1. Make the script executable:
   ```
   chmod +x toggle_network.sh
   ```

2. Use the script with the following commands:
   ```
   ./toggle_network.sh wifi on     # Turn on WiFi
   ./toggle_network.sh wifi off    # Turn off WiFi
   ./toggle_network.sh mobile on   # Turn on mobile data
   ./toggle_network.sh mobile off  # Turn off mobile data
   ./toggle_network.sh status      # Show current status
   ```

This script is useful for quickly switching between networks or for use in other scripts.

## Customization

If you need to use a different APN, username, or password, you can edit the following files:

1. For the CLI version, edit `network_toggle_cli.py`:
   ```python
   # APN settings for Digi Spain
   self.apn = "internet.digimobil.es"
   self.username = ""  # Leave empty if not required
   self.password = ""  # Leave empty if not required
   ```

2. For the quick toggle script, edit `toggle_network.sh`:
   ```bash
   # APN settings for Digi Spain
   APN="internet.digimobil.es"
   USERNAME=""
   PASSWORD=""
   ```

## Troubleshooting

- If the 4G module is not detected, make sure it's properly installed and the SIM card is inserted correctly
- If the connection fails, check the APN settings and make sure they match your mobile provider's requirements
- For version 9001 of the 4G module, the script will automatically handle the necessary configuration
- For other versions (e.g., 9011), the script will check for the usb0 interface

## How It Works

The script follows the official guidelines from the uConsole GitHub repository for setting up the 4G extension:

1. Powers on the 4G extension using the appropriate command for your uConsole model
2. Checks the version of the 4G extension
3. For version 9001, it:
   - Restarts ModemManager to detect the modem
   - Finds the primary port
   - Creates a GSM connection with the specified APN
   - Brings up the connection
4. For other versions, it checks if the usb0 interface is available

The WiFi functionality uses NetworkManager to enable/disable the WiFi radio and manage connections.
