#!/bin/bash

# Script to quickly toggle between WiFi and mobile connectivity
# Usage: ./toggle_network.sh [wifi|mobile] [on|off]
# Examples:
#   ./toggle_network.sh wifi on    - Turn on WiFi
#   ./toggle_network.sh wifi off   - Turn off WiFi
#   ./toggle_network.sh mobile on  - Turn on mobile data
#   ./toggle_network.sh mobile off - Turn off mobile data
#   ./toggle_network.sh status     - Show current status

# APN settings for Digi Spain
APN="internet.digimobil.es"
USERNAME=""
PASSWORD=""

# Function to check status
check_status() {
    echo "Checking network status..."
    
    # Check WiFi status
    WIFI_STATUS=$(nmcli radio wifi)
    
    # Check 4G status
    MODEM_OUTPUT=$(mmcli -L)
    if [[ "$MODEM_OUTPUT" == *"SIMCOM_SIM7600G-H"* ]] || [[ "$MODEM_OUTPUT" == *"QUALCOMM"* ]]; then
        MOBILE_STATUS="enabled"
    else
        MOBILE_STATUS="disabled"
    fi
    
    # Check current connection
    CONNECTION_INFO=$(nmcli -t -f TYPE,STATE,DEVICE connection show --active)
    
    CURRENT_CONNECTION="None"
    if [[ "$CONNECTION_INFO" == *"gsm:activated"* ]]; then
        CURRENT_CONNECTION="Mobile Data"
    elif [[ "$CONNECTION_INFO" == *"wifi:activated"* ]]; then
        CURRENT_CONNECTION="WiFi"
    fi
    
    # Get IP address
    IP_INFO=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v "127.0.0.1")
    if [ -z "$IP_INFO" ]; then
        IP_INFO="Not connected"
    fi
    
    # Print status
    echo "=== Network Status ==="
    echo "WiFi: $WIFI_STATUS"
    echo "Mobile Data: $MOBILE_STATUS"
    echo "Current Connection: $CURRENT_CONNECTION"
    echo "IP Address: $IP_INFO"
    echo "====================="
}

# Function to enable WiFi
enable_wifi() {
    echo "Enabling WiFi..."
    nmcli radio wifi on
    echo "Attempting to connect to known WiFi networks..."
    nmcli device wifi connect
    echo "WiFi enabled."
}

# Function to disable WiFi
disable_wifi() {
    echo "Disabling WiFi..."
    # Disable any active WiFi connection
    WIFI_CONNECTIONS=$(nmcli -t -f NAME,TYPE connection show --active | grep ":wifi")
    if [ -n "$WIFI_CONNECTIONS" ]; then
        CONN_NAME=$(echo "$WIFI_CONNECTIONS" | cut -d':' -f1)
        nmcli connection down "$CONN_NAME"
    fi
    nmcli radio wifi off
    echo "WiFi disabled"
}

# Function to enable mobile data
enable_mobile() {
    echo "Enabling Mobile Data..."
    
    # First try to enable the 4G module (prioritizing CM4 model since user has CM4-based uConsole)
    if command -v uconsole-4g-cm4 &> /dev/null; then
        echo "Using CM4 model command..."
        uconsole-4g-cm4 enable
        MODEL="CM4"
    elif command -v uconsole-4g &> /dev/null; then
        echo "CM4 command not found, trying A06/R01 model command..."
        uconsole-4g enable
        MODEL="A06/R01"
    else
        echo "Failed to enable 4G module. Please check your uConsole model."
        exit 1
    fi
    
    echo "Using uConsole $MODEL model commands"
    
    # Wait for the module to initialize
    echo "Waiting for 4G module to initialize (20 seconds)..."
    sleep 20
    
    # Check the version of the 4G extension
    echo "Checking 4G module version..."
    VERSION_OUTPUT=$(echo -en "AT+CUSBPIDSWITCH?\r\n" | sudo socat - /dev/ttyUSB2,crnl)
    
    if [[ "$VERSION_OUTPUT" == *"9001"* ]]; then
        # For version 9001, we need to use ModemManager
        echo "Detected 4G module version 9001"
        
        # Restart ModemManager to detect the modem
        echo "Restarting ModemManager..."
        sudo systemctl restart ModemManager
        sleep 5
        
        # Check if the modem is detected
        MODEM_OUTPUT=$(mmcli -L)
        if [[ "$MODEM_OUTPUT" != *"SIMCOM_SIM7600G-H"* ]] && [[ "$MODEM_OUTPUT" != *"QUALCOMM"* ]]; then
            echo "4G modem not detected. Please check your hardware."
            exit 1
        fi
        
        # Find the primary port
        echo "Finding primary port..."
        PORT_OUTPUT=$(mmcli -m any | grep "primary port")
        if [[ "$PORT_OUTPUT" == *"cdc-wdm0"* ]]; then
            # Blacklist some kernel modules as suggested in the documentation
            echo "Detected cdc-wdm0 port, blacklisting kernel modules..."
            sudo bash -c 'cat << EOF > /etc/modprobe.d/blacklist-qmi.conf
blacklist qmi_wwan
blacklist cdc_wdm
EOF'
            PORT="ttyUSB2"  # Use ttyUSB2 as suggested
        elif [[ "$PORT_OUTPUT" == *"ttyUSB"* ]]; then
            PORT=$(echo "$PORT_OUTPUT" | grep -oP 'ttyUSB\d+')
            echo "Using port: $PORT"
        else
            PORT="ttyUSB2"  # Default to ttyUSB2
            echo "No port detected, defaulting to: $PORT"
        fi
        
        # Create 4G connection with the APN
        echo "Creating 4G connection with APN: $APN..."
        
        # Check if the connection already exists
        CONN_CHECK=$(nmcli connection show 4gnet 2>&1)
        if [[ "$CONN_CHECK" != *"not found"* ]]; then
            # Connection exists, just bring it up
            echo "Connection already exists, bringing it up..."
            sudo nmcli connection up 4gnet
        else
            # Create new connection
            echo "Creating new connection..."
            if [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
                sudo nmcli connection add type gsm ifname "$PORT" con-name 4gnet apn "$APN" gsm.username "$USERNAME" gsm.password "$PASSWORD"
            else
                sudo nmcli connection add type gsm ifname "$PORT" con-name 4gnet apn "$APN"
            fi
            
            sleep 2
            
            # Bring up the connection
            echo "Bringing up the connection..."
            sudo nmcli connection up 4gnet
        fi
    else
        # For other versions (e.g., 9011), just check if usb0 is available
        echo "Checking for usb0 interface..."
        sleep 5
        IFCONFIG_OUTPUT=$(sudo ifconfig)
        if [[ "$IFCONFIG_OUTPUT" == *"usb0"* ]]; then
            echo "Mobile data connection detected on usb0"
        else
            echo "Failed to detect mobile data connection. Please check your SIM card and 4G module."
            exit 1
        fi
    fi
    
    # Wait a bit for the connection to stabilize
    echo "Waiting for connection to stabilize..."
    sleep 5
    echo "Mobile data enabled"
}

# Function to disable mobile data
disable_mobile() {
    echo "Disabling Mobile Data..."
    # Bring down the 4G connection if it exists
    nmcli connection down 4gnet 2>/dev/null
    
    # Power down the 4G module (prioritizing CM4 model)
    if command -v uconsole-4g-cm4 &> /dev/null; then
        echo "Using CM4 model command..."
        uconsole-4g-cm4 disable
    elif command -v uconsole-4g &> /dev/null; then
        echo "CM4 command not found, trying A06/R01 model command..."
        uconsole-4g disable
    else
        echo "Failed to disable 4G module. Please check your uConsole model."
    fi
    
    echo "Mobile data disabled"
}

# Main script logic
case "$1" in
    wifi)
        case "$2" in
            on)
                enable_wifi
                ;;
            off)
                disable_wifi
                ;;
            *)
                echo "Usage: $0 wifi [on|off]"
                exit 1
                ;;
        esac
        ;;
    mobile)
        case "$2" in
            on)
                enable_mobile
                ;;
            off)
                disable_mobile
                ;;
            *)
                echo "Usage: $0 mobile [on|off]"
                exit 1
                ;;
        esac
        ;;
    status)
        check_status
        ;;
    *)
        echo "Usage: $0 [wifi|mobile] [on|off] or $0 status"
        echo "Examples:"
        echo "  $0 wifi on    - Turn on WiFi"
        echo "  $0 wifi off   - Turn off WiFi"
        echo "  $0 mobile on  - Turn on mobile data"
        echo "  $0 mobile off - Turn off mobile data"
        echo "  $0 status     - Show current status"
        exit 1
        ;;
esac

# Show status after making changes
if [ "$1" != "status" ]; then
    echo ""
    check_status
fi

exit 0
