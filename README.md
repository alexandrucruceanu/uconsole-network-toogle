# uConsole Network Toggle

A simple GUI application to toggle between WiFi and 4G mobile connectivity on the uConsole device running Kali Linux.

## Features

- Toggle between WiFi and 4G mobile connectivity
- Display current connection status and IP address
- Support for both uConsole CM4 and A06/R01 models
- Automatic configuration of 4G connection with Digi Spain APN

## Requirements

- uConsole with 4G LTE module from Clockwork
- Kali Linux installed
- Python 3 with Tkinter
- NetworkManager and ModemManager installed
- SIM card inserted in the 4G module

## Installation

1. Copy all files to your uConsole device
2. Make the shell script executable:
   ```
   chmod +x network_toggle_linux.sh
   ```

## Usage

1. Run the application:
   ```
   ./network_toggle_linux.sh
   ```
   
   Or directly with Python:
   ```
   python3 network_toggle.py
   ```

2. The application will open with a simple GUI:
   - Select "WiFi" or "Mobile Data (4G)" using the radio buttons
   - Click "Enable Selected Network" to enable the selected network type
   - Click "Refresh Status" to update the connection status
   - The current connection status and IP address will be displayed

## Customization

If you need to use a different APN, username, or password, edit the `network_toggle.py` file and modify the following lines:

```python
# APN settings for Digi Spain
self.apn = "internet.digimobil.es"
self.username = ""  # Leave empty if not required
self.password = ""  # Leave empty if not required
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
