#!/bin/bash

# Troubleshooting script for 4G modem detection issues
echo "=== uConsole 4G Troubleshooting Tool ==="
echo "This script will help diagnose and fix 4G modem detection issues."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (sudo)."
  exit 1
fi

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Step 1: Check for required tools
echo "Step 1: Checking for required tools..."
MISSING_TOOLS=0

if ! command_exists mmcli; then
  echo "  [ERROR] ModemManager CLI (mmcli) not found."
  echo "  Please install with: sudo apt install modemmanager"
  MISSING_TOOLS=1
fi

if ! command_exists socat; then
  echo "  [ERROR] socat not found."
  echo "  Please install with: sudo apt install socat"
  MISSING_TOOLS=1
fi

if ! command_exists nmcli; then
  echo "  [ERROR] NetworkManager CLI (nmcli) not found."
  echo "  Please install with: sudo apt install network-manager"
  MISSING_TOOLS=1
fi

if [ $MISSING_TOOLS -eq 1 ]; then
  echo "Please install the missing tools and run this script again."
  exit 1
else
  echo "  [OK] All required tools are installed."
fi

# Step 2: Check uConsole model and enable 4G
echo ""
echo "Step 2: Checking uConsole model and enabling 4G module..."

if command_exists uconsole-4g-cm4; then
  echo "  Detected CM4 model."
  echo "  Enabling 4G module with uconsole-4g-cm4..."
  uconsole-4g-cm4 enable
  MODEL="CM4"
elif command_exists uconsole-4g; then
  echo "  Detected A06/R01 model."
  echo "  Enabling 4G module with uconsole-4g..."
  uconsole-4g enable
  MODEL="A06/R01"
else
  echo "  [WARNING] Could not detect uConsole model commands."
  echo "  Please manually enable the 4G module according to your model."
  read -p "  Press Enter to continue once you've enabled the 4G module..."
  MODEL="unknown"
fi

# Step 3: Wait for the module to initialize
echo ""
echo "Step 3: Waiting for 4G module to initialize (30 seconds)..."
echo "  This may take longer on some systems."
sleep 30

# Step 4: Check for USB devices
echo ""
echo "Step 4: Checking for USB devices..."
echo "  Looking for 4G modem USB devices..."
lsusb_output=$(lsusb)
echo "$lsusb_output"

if [[ "$lsusb_output" == *"SIMCom"* ]] || [[ "$lsusb_output" == *"Qualcomm"* ]]; then
  echo "  [OK] Found SIMCom/Qualcomm USB device."
else
  echo "  [WARNING] No SIMCom/Qualcomm USB device found."
  echo "  This might indicate a hardware connection issue."
fi

# Step 5: Check for ttyUSB devices
echo ""
echo "Step 5: Checking for ttyUSB devices..."
if [ -d /dev ]; then
  ttyusb_devices=$(ls -l /dev/ttyUSB* 2>/dev/null)
  if [ -z "$ttyusb_devices" ]; then
    echo "  [ERROR] No ttyUSB devices found."
    echo "  This indicates the 4G module is not properly connected or recognized."
  else
    echo "  Found ttyUSB devices:"
    echo "$ttyusb_devices"
    echo "  [OK] ttyUSB devices detected."
  fi
else
  echo "  [ERROR] /dev directory not found. This is unusual."
fi

# Step 6: Try different AT command ports
echo ""
echo "Step 6: Testing AT commands on different ports..."
for i in {0..5}; do
  if [ -e "/dev/ttyUSB$i" ]; then
    echo "  Testing AT command on /dev/ttyUSB$i..."
    at_output=$(echo -en "AT\r\n" | socat - /dev/ttyUSB$i,crnl 2>/dev/null)
    if [[ "$at_output" == *"OK"* ]]; then
      echo "  [OK] AT command successful on /dev/ttyUSB$i"
      WORKING_PORT=$i
      
      # Try the version check command
      echo "  Testing version check on /dev/ttyUSB$i..."
      version_output=$(echo -en "AT+CUSBPIDSWITCH?\r\n" | socat - /dev/ttyUSB$i,crnl 2>/dev/null)
      echo "  Version output: $version_output"
      
      if [[ "$version_output" == *"9001"* ]]; then
        echo "  [OK] Detected version 9001 on /dev/ttyUSB$i"
        VERSION="9001"
      elif [[ "$version_output" == *"9011"* ]]; then
        echo "  [OK] Detected version 9011 on /dev/ttyUSB$i"
        VERSION="9011"
      else
        echo "  [INFO] Could not determine version from output."
        VERSION="unknown"
      fi
    else
      echo "  [INFO] AT command failed on /dev/ttyUSB$i"
    fi
  fi
done

if [ -z "$WORKING_PORT" ]; then
  echo "  [WARNING] Could not find a working port for AT commands."
else
  echo "  [OK] Found working AT command port: /dev/ttyUSB$WORKING_PORT"
fi

# Step 7: Restart ModemManager
echo ""
echo "Step 7: Restarting ModemManager service..."
systemctl restart ModemManager
echo "  Waiting for ModemManager to initialize (10 seconds)..."
sleep 10

# Step 8: Check for modems with mmcli
echo ""
echo "Step 8: Checking for modems with mmcli..."
mmcli_output=$(mmcli -L)
echo "$mmcli_output"

if [[ "$mmcli_output" == *"No modems found"* ]]; then
  echo "  [ERROR] No modems found by ModemManager."
  echo "  Trying alternative detection methods..."
  
  # Check if usb0 interface exists
  if ip link show | grep -q usb0; then
    echo "  [OK] Found usb0 interface. This indicates the modem is working in direct mode."
    echo "  You can use this interface directly without ModemManager."
    HAS_USB0=1
  else
    echo "  [ERROR] No usb0 interface found."
    HAS_USB0=0
  fi
else
  echo "  [OK] ModemManager detected modem(s)."
  HAS_MODEM=1
  
  # Get the modem index
  MODEM_INDEX=$(echo "$mmcli_output" | grep -o "/org/freedesktop/ModemManager1/Modem/[0-9]*" | grep -o "[0-9]*")
  if [ -n "$MODEM_INDEX" ]; then
    echo "  Found modem with index: $MODEM_INDEX"
    
    # Get more details about the modem
    echo "  Getting modem details..."
    mmcli_modem_output=$(mmcli -m $MODEM_INDEX)
    echo "$mmcli_modem_output"
    
    # Find the primary port
    PRIMARY_PORT=$(echo "$mmcli_modem_output" | grep "primary port" | awk '{print $NF}')
    if [ -n "$PRIMARY_PORT" ]; then
      echo "  [OK] Found primary port: $PRIMARY_PORT"
    else
      echo "  [WARNING] Could not determine primary port."
      PRIMARY_PORT="ttyUSB2"  # Default
    fi
  fi
fi

# Step 9: Create or update the connection
echo ""
echo "Step 9: Setting up network connection..."

# Check if connection exists
conn_exists=$(nmcli connection show 4gnet 2>&1)
if [[ "$conn_exists" != *"not found"* ]]; then
  echo "  Connection '4gnet' already exists. Deleting it to recreate..."
  nmcli connection delete 4gnet
fi

# Determine the port to use
if [ -n "$PRIMARY_PORT" ]; then
  PORT=$PRIMARY_PORT
elif [ -n "$WORKING_PORT" ]; then
  PORT="ttyUSB$WORKING_PORT"
else
  PORT="ttyUSB2"  # Default fallback
fi

echo "  Creating new connection with APN: internet.digimobil.es on port: $PORT"
nmcli connection add type gsm ifname "$PORT" con-name 4gnet apn "internet.digimobil.es"

echo "  Bringing up the connection..."
nmcli connection up 4gnet

# Step 10: Check connection status
echo ""
echo "Step 10: Checking connection status..."
sleep 5

# Check if we have a ppp0 interface
if ip link show | grep -q ppp0; then
  echo "  [OK] Found ppp0 interface. 4G connection is established."
elif [ "$HAS_USB0" -eq 1 ]; then
  echo "  [OK] Using usb0 interface for 4G connection."
else
  echo "  [WARNING] No ppp0 or usb0 interface found. Connection might not be established."
fi

# Get IP address
ip_info=$(ip -4 addr show | grep -v "127.0.0.1" | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
if [ -n "$ip_info" ]; then
  echo "  [OK] IP address(es): $ip_info"
else
  echo "  [WARNING] No IP address found."
fi

# Summary
echo ""
echo "=== Troubleshooting Summary ==="
echo "uConsole Model: $MODEL"
if [ -n "$VERSION" ]; then
  echo "4G Module Version: $VERSION"
else
  echo "4G Module Version: Could not determine"
fi

if [ -n "$WORKING_PORT" ]; then
  echo "Working AT Command Port: /dev/ttyUSB$WORKING_PORT"
else
  echo "Working AT Command Port: None found"
fi

if [ "$HAS_MODEM" -eq 1 ]; then
  echo "ModemManager Detection: Yes"
  echo "Primary Port: $PRIMARY_PORT"
elif [ "$HAS_USB0" -eq 1 ]; then
  echo "ModemManager Detection: No, but usb0 interface found"
else
  echo "ModemManager Detection: No"
fi

echo "Connection Port Used: $PORT"
echo "IP Address: $ip_info"

echo ""
echo "=== Next Steps ==="
if [ "$HAS_MODEM" -eq 1 ] || [ "$HAS_USB0" -eq 1 ]; then
  echo "The 4G modem appears to be working. Try using the network_toggle_cli.py script again."
  echo "If you still have issues, edit the script to use port /dev/ttyUSB$WORKING_PORT instead of /dev/ttyUSB2."
else
  echo "1. Check that the 4G module is properly connected"
  echo "2. Make sure the SIM card is inserted correctly"
  echo "3. Try rebooting your uConsole"
  echo "4. Run this troubleshooting script again"
fi

echo ""
echo "Troubleshooting complete."
