#!/usr/bin/env python3
import subprocess
import os
import time
import re
import sys

class NetworkToggleCLI:
    def __init__(self):
        # APN settings for Digi Spain
        self.apn = "internet.digimobil.es"
        self.username = ""  # Leave empty if not required
        self.password = ""  # Leave empty if not required
        
        self.is_4g_enabled = False
        self.is_wifi_enabled = False

    def run_command(self, command, shell=False):
        try:
            if shell:
                result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            else:
                result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
            print(f"Error output: {e.stderr}")
            return None

    def check_status(self):
        print("Checking network status...")
        
        # Check WiFi status
        wifi_output = self.run_command(["nmcli", "radio", "wifi"])
        self.is_wifi_enabled = wifi_output == "enabled"
        
        # Check 4G status
        modem_output = self.run_command(["mmcli", "-L"])
        self.is_4g_enabled = "SIMCOM_SIM7600G-H" in modem_output or "QUALCOMM" in modem_output
        
        # Check current connection and IP
        connection_info = self.run_command(["nmcli", "-t", "-f", "TYPE,STATE,DEVICE", "connection", "show", "--active"])
        
        current_connection = "None"
        if connection_info:
            for line in connection_info.split('\n'):
                if "gsm:activated" in line:
                    current_connection = "Mobile Data"
                    break
                elif "wifi:activated" in line:
                    current_connection = "WiFi"
                    break
        
        # Get IP address
        ip_info = self.run_command("ip -4 addr show | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'", shell=True)
        current_ip = "Not connected"
        if ip_info:
            ip_addresses = ip_info.split('\n')
            # Filter out localhost
            ip_addresses = [ip for ip in ip_addresses if not ip.startswith("127.")]
            if ip_addresses:
                current_ip = ip_addresses[0]
        
        # Print status
        print("\n=== Network Status ===")
        print(f"WiFi: {'Enabled' if self.is_wifi_enabled else 'Disabled'}")
        print(f"Mobile Data: {'Enabled' if self.is_4g_enabled else 'Disabled'}")
        print(f"Current Connection: {current_connection}")
        print(f"IP Address: {current_ip}")
        print("=====================\n")
        
        return current_connection

    def enable_wifi(self):
        print("Enabling WiFi...")
        self.run_command(["nmcli", "radio", "wifi", "on"])
        # Try to connect to the last known WiFi
        print("Attempting to connect to known WiFi networks...")
        self.run_command(["nmcli", "device", "wifi", "connect"])
        print("WiFi enabled. Use 'nmcli device wifi list' to see available networks")
        print("To connect to a specific network: nmcli device wifi connect SSID-Name password WIFI-PASSWORD")

    def disable_wifi(self):
        print("Disabling WiFi...")
        # Disable any active WiFi connection
        wifi_connections = self.run_command(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"])
        if wifi_connections:
            for line in wifi_connections.split('\n'):
                if ":wifi" in line:
                    conn_name = line.split(':')[0]
                    self.run_command(["nmcli", "connection", "down", conn_name])
        self.run_command(["nmcli", "radio", "wifi", "off"])
        print("WiFi disabled")

    def enable_mobile_data(self):
        print("Enabling Mobile Data...")
        
        # First try to enable the 4G module (prioritizing CM4 model since user has CM4-based uConsole)
        try:
            print("Using CM4 model command...")
            self.run_command(["uconsole-4g-cm4", "enable"])
        except:
            try:
                print("CM4 command failed, trying A06/R01 model command...")
                self.run_command(["uconsole-4g", "enable"])
            except:
                print("Failed to enable 4G module. Please check your uConsole model.")
                return False
        
        # Wait for the module to initialize
        print("Waiting for 4G module to initialize (20 seconds)...")
        time.sleep(20)
        
        # Check the version of the 4G extension
        print("Checking 4G module version...")
        version_output = self.run_command('echo -en "AT+CUSBPIDSWITCH?\\r\\n" | sudo socat - /dev/ttyUSB2,crnl', shell=True)
        
        if version_output and "9001" in version_output:
            # For version 9001, we need to use ModemManager
            print("Detected 4G module version 9001")
            
            # Restart ModemManager to detect the modem
            print("Restarting ModemManager...")
            self.run_command(["sudo", "systemctl", "restart", "ModemManager"])
            time.sleep(5)
            
            # Check if the modem is detected
            modem_output = self.run_command(["mmcli", "-L"])
            if not modem_output or "SIMCOM_SIM7600G-H" not in modem_output and "QUALCOMM" not in modem_output:
                print("4G modem not detected. Please check your hardware.")
                return False
            
            # Find the primary port
            print("Finding primary port...")
            port_output = self.run_command('mmcli -m any | grep "primary port"', shell=True)
            if "cdc-wdm0" in port_output:
                # Blacklist some kernel modules as suggested in the documentation
                print("Detected cdc-wdm0 port, blacklisting kernel modules...")
                blacklist_cmd = 'sudo bash -c \'cat << EOF > /etc/modprobe.d/blacklist-qmi.conf\nblacklist qmi_wwan\nblacklist cdc_wdm\nEOF\''
                self.run_command(blacklist_cmd, shell=True)
                port = "ttyUSB2"  # Use ttyUSB2 as suggested
            elif "ttyUSB" in port_output:
                port = re.search(r'ttyUSB\d+', port_output).group(0)
                print(f"Using port: {port}")
            else:
                port = "ttyUSB2"  # Default to ttyUSB2
                print(f"No port detected, defaulting to: {port}")
            
            # Create 4G connection with the APN
            print(f"Creating 4G connection with APN: {self.apn}...")
            
            # Check if the connection already exists
            conn_check = self.run_command(["nmcli", "connection", "show", "4gnet"])
            if conn_check and "not found" not in conn_check:
                # Connection exists, just bring it up
                print("Connection already exists, bringing it up...")
                self.run_command(["sudo", "nmcli", "connection", "up", "4gnet"])
            else:
                # Create new connection
                print("Creating new connection...")
                if self.username and self.password:
                    cmd = ["sudo", "nmcli", "connection", "add", "type", "gsm", "ifname", port, "con-name", "4gnet", 
                          "apn", self.apn, "gsm.username", self.username, "gsm.password", self.password]
                else:
                    cmd = ["sudo", "nmcli", "connection", "add", "type", "gsm", "ifname", port, "con-name", "4gnet", 
                          "apn", self.apn]
                
                self.run_command(cmd)
                time.sleep(2)
                
                # Bring up the connection
                print("Bringing up the connection...")
                self.run_command(["sudo", "nmcli", "connection", "up", "4gnet"])
        else:
            # For other versions (e.g., 9011), just check if usb0 is available
            print("Checking for usb0 interface...")
            time.sleep(5)
            ifconfig_output = self.run_command(["sudo", "ifconfig"])
            if "usb0" in ifconfig_output:
                print("Mobile data connection detected on usb0")
            else:
                print("Failed to detect mobile data connection. Please check your SIM card and 4G module.")
                return False
        
        # Wait a bit for the connection to stabilize
        print("Waiting for connection to stabilize...")
        time.sleep(5)
        return True

    def disable_mobile_data(self):
        print("Disabling Mobile Data...")
        # Bring down the 4G connection if it exists
        self.run_command(["nmcli", "connection", "down", "4gnet"], shell=False)
        # Power down the 4G module (prioritizing CM4 model)
        try:
            print("Using CM4 model command...")
            self.run_command(["uconsole-4g-cm4", "disable"])
        except:
            try:
                print("CM4 command failed, trying A06/R01 model command...")
                self.run_command(["uconsole-4g", "disable"])
            except:
                print("Failed to disable 4G module.")
        print("Mobile data disabled")

    def show_menu(self):
        print("\nuConsole Network Toggle CLI")
        print("==========================")
        print("1. Enable WiFi")
        print("2. Disable WiFi")
        print("3. Enable Mobile Data (4G)")
        print("4. Disable Mobile Data (4G)")
        print("5. Check Status")
        print("6. Exit")
        choice = input("\nEnter your choice (1-6): ")
        return choice

    def run(self):
        while True:
            self.check_status()
            choice = self.show_menu()
            
            if choice == '1':
                self.enable_wifi()
            elif choice == '2':
                self.disable_wifi()
            elif choice == '3':
                self.enable_mobile_data()
            elif choice == '4':
                self.disable_mobile_data()
            elif choice == '5':
                # Status is already shown at the beginning of the loop
                pass
            elif choice == '6':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
            
            # Pause to let the user read the output
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    app = NetworkToggleCLI()
    app.run()
