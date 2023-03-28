import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import serial
import threading

device = None
serial_devices = []


def connect_device():
    global device, update_serial_handle
    selected_device = device_dropdown.get()
    print(f"Connecting to {selected_device}...")
    try:
        device = serial.Serial(selected_device, 9600, timeout=1)
        if device.is_open:
            connect_button.configure(text="Disconnect", command=disconnect_device)
            device_dropdown.configure(state="disabled")
            # create_console()
    except Exception as e:
        print(f"Error connecting to device: {e}")


def disconnect_device():
    global device
    if device.is_open:
        device.close()
        device = None
        print("Disconnected from device")
        connect_button.configure(text="Connect", command=connect_device, state="enabled")
        device_dropdown.configure(state="readonly")
        # remove_console()


def update_serial_devices():
    # Get the list of serial devices and update the dropdown
    global serial_devices
    serial_devices = [str(port.device) for port in serial.tools.list_ports.comports()]
    if (device == None):
        if len(serial_devices) > 0:
            device_dropdown["values"] = serial_devices
            device_dropdown.configure(state="readonly")
            connect_button.configure(state="enabled")
            if device_dropdown.current() < 0:
                device_dropdown.current(0)

        else:
            device_dropdown.set("No Device Connected")
            device_dropdown.configure(state="disabled")
            connect_button.configure(state="disabled")
    else:
        if device.port not in serial_devices:
            print("ERROR: connection lost")

    # Schedule the next update
    app.after(1000, update_serial_devices)


# Setup main window
app = tk.Tk()
app.title("CUBEcontrol")
app.geometry("800x500")
app.resizable(False, False)

# Dark theme with blue accent color
app.tk.call("source", "azure.tcl")
app.tk.call("set_theme", "dark")

# Create right frame for the image
right_frame = ttk.Frame(app, padding=0, borderwidth=0)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Create left frame for the labels and dropdown
left_frame = ttk.Frame(app, padding=20)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Configure grid in the left frame
left_frame.columnconfigure(1, weight=1)
left_frame.rowconfigure(0, weight=1)

# Load and display the image in the right frame
image_file = "image.png"
image = tk.PhotoImage(file=image_file)
image_label = ttk.Label(right_frame, image=image)
image_label.pack(anchor="e", expand=True)

# Logo text
logo_text = ttk.Label(left_frame, text="CUBEcontrol", font=("Arial", 24, "bold"))
logo_text.grid(column=0, row=0, columnspan=3, pady=10)

# Label
ttk.Label(left_frame, text="Select a Device:", font=("Arial", 12)).grid(
    column=0, row=1, sticky=tk.W, columnspan=3, pady=10, padx=10
)

# Serial devices dropdown
serial_devices = [str(port.device) for port in serial.tools.list_ports.comports()]
device_dropdown = ttk.Combobox(
    left_frame, values=serial_devices, font=("Arial", 12), state="disabled"
)
device_dropdown.grid(column=0, row=2, sticky=(tk.W, tk.E), padx=10)

# Connect button
connect_button = ttk.Button(
    left_frame,
    text="Connect",
    style="Accent.TButton",
    state="disabled",
    command=connect_device,
)
connect_button.grid(column=1, row=2, sticky=tk.W)
# Schedule the automatic udate of the serial devices list
update_serial_handle = app.after(0, update_serial_devices)
app.mainloop()
