#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

class NetworkToggleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Connection Manager")
        self.apn = "internet.digimobil.es"
        
        # Initialize modem
        self.modem_index = self.get_modem_index()
        if not self.modem_index:
            messagebox.showerror("Error", "4G modem not detected")
            self.root.destroy()
            return

        # GUI Elements
        self.status_label = ttk.Label(root, text="Current Status: Checking...")
        self.status_label.pack(pady=10)
        
        self.toggle_button = ttk.Button(root, text="Toggle Connection", command=self.toggle_connection)
        self.toggle_button.pack(pady=5)
        
        self.interface_var = tk.StringVar(value="wlan0")
        self.wifi_radio = ttk.Radiobutton(root, text="WiFi", variable=self.interface_var, value="wlan0")
        self.mobile_radio = ttk.Radiobutton(root, text="Mobile", variable=self.interface_var, value="wwan0")
        self.wifi_radio.pack()
        self.mobile_radio.pack()
        
        self.update_status()

    def get_modem_index(self):
        try:
            result = subprocess.check_output(["mmcli", "-L"], text=True)
            return result.split()[0].split('/')[-1]  # Extract modem index
        except subprocess.CalledProcessError:
            return None

    def update_status(self):
        current_interface = self.interface_var.get()
        try:
            wifi_status = subprocess.check_output(["nmcli", "radio", "wifi"], text=True).strip()
            mobile_status = subprocess.check_output(["mmcli", "-m", self.modem_index, "-e"], text=True)
            
            status_text = f"WiFi: {wifi_status}\nMobile: {self.get_mobile_status()}"
            self.status_label.config(text=status_text)
            
            # Update radio buttons based on current connection
            if "connected" in self.get_mobile_status():
                self.interface_var.set("wwan0")
            else:
                self.interface_var.set("wlan0")
                
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Status check failed: {str(e)}")
        
        self.root.after(5000, self.update_status)

    def get_mobile_status(self):
        try:
            status = subprocess.check_output(
                ["mmcli", "-m", self.modem_index, "--command=AT+UCGSTATUS"],
                text=True
            )
            return "connected" if "1" in status else "disconnected"
        except subprocess.CalledProcessError:
            return "status unknown"

    def toggle_connection(self):
        target_interface = self.interface_var.get()
        
        try:
            # Disable current interface
            if target_interface == "wwan0":
                subprocess.run(["nmcli", "radio", "wifi", "off"])
                self.setup_mobile_connection()
            else:
                subprocess.run(["mmcli", "-m", self.modem_index, "--disable"])
                subprocess.run(["nmcli", "radio", "wifi", "on"])
            
            messagebox.showinfo("Success", f"Switched to {target_interface}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Toggle failed: {str(e)}")

    def setup_mobile_connection(self):
        # Configure APN and enable modem
        subprocess.run([
            "mmcli", "-m", self.modem_index, 
            "--3gpp-set-initial-eps-bearer-settings="
            f"apn={self.apn},ip-type=ipv4"
        ])
        subprocess.run(["mmcli", "-m", self.modem_index, "--enable"])
        subprocess.run(["mmcli", "-m", self.modem_index, "--simple-connect"])

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkToggleApp(root)
    root.mainloop()
