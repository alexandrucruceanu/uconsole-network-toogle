#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import time
import threading
import re

class NetworkToggle:
    def __init__(self, root):
        self.root = root
        self.root.title("uConsole Network Toggle")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Set dark theme colors
        self.bg_color = "#2e2e2e"
        self.fg_color = "#ffffff"
        self.accent_color = "#007acc"
        
        self.root.configure(bg=self.bg_color)
        
        # Variables
        self.connection_type = tk.StringVar(value="wifi")
        self.status_text = tk.StringVar(value="Checking status...")
        self.is_4g_enabled = False
        self.is_wifi_enabled = False
        self.current_ip = tk.StringVar(value="Not connected")
        
        # APN settings for Digi Spain
        self.apn = "internet.digimobil.es"
        self.username = ""  # Leave empty if not required
        self.password = ""  # Leave empty if not required
        
        # Create UI
        self.create_widgets()
        
        # Start status check
        self.check_status()

    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="uConsole Network Manager", 
            font=("Arial", 16, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        title_label.pack(pady=(0, 20))
        
        # Connection type selector
        selector_frame = tk.Frame(main_frame, bg=self.bg_color)
        selector_frame.pack(fill=tk.X, pady=10)
        
        wifi_rb = ttk.Radiobutton(
            selector_frame, 
            text="WiFi", 
            variable=self.connection_type, 
            value="wifi",
            command=self.on_connection_change
        )
        wifi_rb.pack(side=tk.LEFT, padx=(0, 20))
        
        mobile_rb = ttk.Radiobutton(
            selector_frame, 
            text="Mobile Data (4G)", 
            variable=self.connection_type, 
            value="mobile",
            command=self.on_connection_change
        )
        mobile_rb.pack(side=tk.LEFT)
        
        # Status frame
        status_frame = tk.LabelFrame(
            main_frame, 
            text="Connection Status", 
            bg=self.bg_color,
            fg=self.fg_color,
            padx=10,
            pady=10
        )
        status_frame.pack(fill=tk.X, pady=10)
        
        status_label = tk.Label(
            status_frame, 
            textvariable=self.status_text,
            bg=self.bg_color,
            fg=self.fg_color
        )
        status_label.pack(anchor=tk.W)
        
        ip_label_text = tk.Label(
            status_frame, 
            text="IP Address:",
            bg=self.bg_color,
            fg=self.fg_color
        )
        ip_label_text.pack(anchor=tk.W, pady=(10, 0))
        
        ip_label = tk.Label(
            status_frame, 
            textvariable=self.current_ip,
            bg=self.bg_color,
            fg=self.accent_color
        )
        ip_label.pack(anchor=tk.W)
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=20)
        
        self.toggle_button = tk.Button(
            button_frame,
            text="Enable Selected Network",
            command=self.toggle_connection,
            bg=self.accent_color,
            fg=self.fg_color,
            padx=10,
            pady=5,
            relief=tk.FLAT
        )
        self.toggle_button.pack(side=tk.LEFT)
        
        refresh_button = tk.Button(
            button_frame,
            text="Refresh Status",
            command=self.check_status,
            bg=self.bg_color,
            fg=self.fg_color,
            padx=10,
            pady=5,
            relief=tk.FLAT
        )
        refresh_button.pack(side=tk.RIGHT)

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
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self._check_status_thread, daemon=True).start()

    def _check_status_thread(self):
        self.status_text.set("Checking network status...")
        self.toggle_button.config(state=tk.DISABLED)
        
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
        if ip_info:
            ip_addresses = ip_info.split('\n')
            # Filter out localhost
            ip_addresses = [ip for ip in ip_addresses if not ip.startswith("127.")]
            if ip_addresses:
                self.current_ip.set(ip_addresses[0])
            else:
                self.current_ip.set("Not connected")
        else:
            self.current_ip.set("Not connected")
        
        # Update status text
        if current_connection == "WiFi":
            self.status_text.set("Connected to WiFi")
            self.connection_type.set("wifi")
        elif current_connection == "Mobile Data":
            self.status_text.set("Connected to Mobile Data")
            self.connection_type.set("mobile")
        else:
            self.status_text.set("Not connected")
        
        self.toggle_button.config(state=tk.NORMAL)

    def on_connection_change(self):
        selected = self.connection_type.get()
        if selected == "wifi":
            self.toggle_button.config(text="Enable WiFi" if not self.is_wifi_enabled else "Disable WiFi")
        else:
            self.toggle_button.config(text="Enable Mobile Data" if not self.is_4g_enabled else "Disable Mobile Data")

    def toggle_connection(self):
        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=self._toggle_connection_thread, daemon=True).start()

    def _toggle_connection_thread(self):
        selected = self.connection_type.get()
        self.toggle_button.config(state=tk.DISABLED)
        
        if selected == "wifi":
            if self.is_wifi_enabled:
                # Disable WiFi
                self.status_text.set("Disabling WiFi...")
                self.run_command(["nmcli", "radio", "wifi", "off"])
                # Disable any active WiFi connection
                wifi_connections = self.run_command(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"])
                if wifi_connections:
                    for line in wifi_connections.split('\n'):
                        if ":wifi" in line:
                            conn_name = line.split(':')[0]
                            self.run_command(["nmcli", "connection", "down", conn_name])
            else:
                # Enable WiFi
                self.status_text.set("Enabling WiFi...")
                self.run_command(["nmcli", "radio", "wifi", "on"])
                # Try to connect to the last known WiFi
                self.run_command(["nmcli", "device", "wifi", "connect"])
        else:  # Mobile
            if self.is_4g_enabled:
                # Disable 4G
                self.status_text.set("Disabling Mobile Data...")
                # Bring down the 4G connection if it exists
                self.run_command(["nmcli", "connection", "down", "4gnet"], shell=False)
                # Power down the 4G module (depends on uConsole model)
                try:
                    self.run_command(["uconsole-4g-cm4", "disable"])
                except:
                    try:
                        self.run_command(["uconsole-4g", "disable"])
                    except:
                        pass
            else:
                # Enable 4G
                self.status_text.set("Enabling Mobile Data...")
                
                # First try to enable the 4G module (depends on uConsole model)
                try:
                    self.run_command(["uconsole-4g-cm4", "enable"])
                except:
                    try:
                        self.run_command(["uconsole-4g", "enable"])
                    except:
                        messagebox.showerror("Error", "Failed to enable 4G module. Please check your uConsole model.")
                        self.toggle_button.config(state=tk.NORMAL)
                        return
                
                # Wait for the module to initialize
                self.status_text.set("Waiting for 4G module to initialize...")
                time.sleep(20)
                
                # Check the version of the 4G extension
                version_output = self.run_command('echo -en "AT+CUSBPIDSWITCH?\\r\\n" | sudo socat - /dev/ttyUSB2,crnl', shell=True)
                
                if version_output and "9001" in version_output:
                    # For version 9001, we need to use ModemManager
                    self.status_text.set("Detected 4G module version 9001...")
                    
                    # Restart ModemManager to detect the modem
                    self.run_command(["sudo", "systemctl", "restart", "ModemManager"])
                    time.sleep(5)
                    
                    # Check if the modem is detected
                    modem_output = self.run_command(["mmcli", "-L"])
                    if not modem_output or "SIMCOM_SIM7600G-H" not in modem_output and "QUALCOMM" not in modem_output:
                        messagebox.showerror("Error", "4G modem not detected. Please check your hardware.")
                        self.toggle_button.config(state=tk.NORMAL)
                        return
                    
                    # Find the primary port
                    port_output = self.run_command('mmcli -m any | grep "primary port"', shell=True)
                    if "cdc-wdm0" in port_output:
                        # Blacklist some kernel modules as suggested in the documentation
                        blacklist_cmd = 'sudo bash -c \'cat << EOF > /etc/modprobe.d/blacklist-qmi.conf\nblacklist qmi_wwan\nblacklist cdc_wdm\nEOF\''
                        self.run_command(blacklist_cmd, shell=True)
                        port = "ttyUSB2"  # Use ttyUSB2 as suggested
                    elif "ttyUSB" in port_output:
                        port = re.search(r'ttyUSB\d+', port_output).group(0)
                    else:
                        port = "ttyUSB2"  # Default to ttyUSB2
                    
                    # Create 4G connection with the APN
                    self.status_text.set(f"Creating 4G connection with APN: {self.apn}...")
                    
                    # Check if the connection already exists
                    conn_check = self.run_command(["nmcli", "connection", "show", "4gnet"])
                    if conn_check and "not found" not in conn_check:
                        # Connection exists, just bring it up
                        self.run_command(["sudo", "nmcli", "connection", "up", "4gnet"])
                    else:
                        # Create new connection
                        if self.username and self.password:
                            cmd = ["sudo", "nmcli", "connection", "add", "type", "gsm", "ifname", port, "con-name", "4gnet", 
                                  "apn", self.apn, "gsm.username", self.username, "gsm.password", self.password]
                        else:
                            cmd = ["sudo", "nmcli", "connection", "add", "type", "gsm", "ifname", port, "con-name", "4gnet", 
                                  "apn", self.apn]
                        
                        self.run_command(cmd)
                        time.sleep(2)
                        
                        # Bring up the connection
                        self.run_command(["sudo", "nmcli", "connection", "up", "4gnet"])
                else:
                    # For other versions (e.g., 9011), just check if usb0 is available
                    self.status_text.set("Checking for usb0 interface...")
                    time.sleep(5)
                    ifconfig_output = self.run_command(["sudo", "ifconfig"])
                    if "usb0" in ifconfig_output:
                        self.status_text.set("Mobile data connection detected on usb0")
                    else:
                        messagebox.showerror("Error", "Failed to detect mobile data connection. Please check your SIM card and 4G module.")
        
        # Wait a bit for the connection to stabilize
        time.sleep(5)
        
        # Update status
        self.check_status()

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkToggle(root)
    root.mainloop()
