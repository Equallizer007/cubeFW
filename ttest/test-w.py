import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports


def connect_device():
    selected_device = device_dropdown.get()
    print(f"Connecting to {selected_device}")


# Setup main window
app = tk.Tk()
app.title("CUBEcontrol")
app.geometry("800x500")
app.resizable(False, False)

# Dark theme with blue accent color
app.tk.call("source", "azure.tcl")
app.tk.call("set_theme", "dark")

# Create and set frame
frame = ttk.Frame(app, padding=20, style="Transparent.TFrame")
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

# Logo text
logo_text = ttk.Label(frame, text="CUBEcontrol", font=("Arial", 24, 'bold'))
logo_text.grid(column=0, row=0, columnspan=3, pady=10)

# Label
ttk.Label(frame, text="Select a Device:", font=("Arial", 12)).grid(
    column=0, row=1, sticky=tk.W, columnspan=3, pady=10, padx=10
)

# Serial devices dropdown
serial_devices = [str(port.device) for port in serial.tools.list_ports.comports()]
device_dropdown = ttk.Combobox(
    frame, values=serial_devices, font=("Arial", 12), state="readonly"
)
device_dropdown.grid(column=0, row=2, sticky=(tk.W, tk.E), padx=10)

# Connect button
connect_button = ttk.Button(
    frame, text="Connect", style="Accent.TButton", command=connect_device
)
connect_button.grid(column=1, row=2, sticky=tk.W)

# Configure grid
frame.columnconfigure(1, weight=1)
frame.rowconfigure(0, weight=1)

app.mainloop()
