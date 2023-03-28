import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk  # pip install sv-ttk
import serial.tools.list_ports
import serial
import threading


class CubeControlApp:
    def __init__(self) -> None:
        self.device = None
        self.serial_devices = []
        self.update_serial_handle = None

        self.app = tk.Tk()
        self.app.title("CUBEcontrol")
        self.app.geometry("800x500")
        self.app.resizable(False, False)

        self.setup_ui()

    def setup_ui(self) -> None:
        sv_ttk.set_theme("light")

        # Create right frame for the image
        self.right_frame = ttk.Frame(
            self.app,
            height=500,
            width=400,
            padding=0,
            borderwidth=0,
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.right_frame.pack_propagate(False)
        self.right_frame.grid_propagate(False)

        # Create left frame for the labels and dropdown
        self.left_frame = ttk.Frame(
            self.app,
            height=500,
            width=400,
            padding=20,
            borderwidth=0,
        )
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        self.left_frame.pack_propagate(False)
        self.left_frame.grid_propagate(False)

        # Configure grid in the left frame
        self.left_frame.columnconfigure(1, weight=1)
        self.left_frame.rowconfigure(0, weight=1)

        # Load and display the image in the right frame
        image_file = "image.png"
        self.image = tk.PhotoImage(file=image_file)
        self.image_label = ttk.Label(
            self.right_frame,
            # background="green",
            image=self.image,
            borderwidth=0,
            padding=0,
        )
        self.image_label.grid()
        self.image_label.update()
        print(self.image_label.winfo_height())
        print(self.image_label.winfo_width())

        # Logo text
        self.logo_text_label = ttk.Label(
            self.left_frame,
            text="CUBEcontrol",
            anchor="center",
            font=("Arial", 24, "bold"),
            width=400,
        )
        self.logo_text_label.grid(column=0, row=0, columnspan=3)

        # Label
        self.select_device_label = ttk.Label(
            self.left_frame, text="Select a Device:", font=("Arial", 12)
        )
        self.select_device_label.grid(
            column=0, row=1, sticky=tk.W, columnspan=3, pady=10, padx=10
        )

        # Serial devices dropdown
        self.serial_devices = [
            str(port.device) for port in serial.tools.list_ports.comports()
        ]
        self.device_dropdown = ttk.Combobox(
            self.left_frame,
            values=self.serial_devices,
            font=("Arial", 12),
            state="disabled",
        )
        self.device_dropdown.grid(column=0, row=2, sticky=(tk.W, tk.E), padx=10)

        # Connect button
        self.connect_button = ttk.Button(
            self.left_frame,
            text="Connect",
            style="Accent.TButton",
            state="disabled",
            command=self.connect_device,
        )
        self.connect_button.grid(column=1, row=2, sticky=tk.W)

        # Schedule the automatic update of the serial devices list
        self.update_serial_handle = self.app.after(0, self.update_serial_devices)

    def connect_device(self) -> None:
        selected_device = self.device_dropdown.get()
        print(f"Connecting to {selected_device}...")
        try:
            self.device = serial.Serial(selected_device, 9600, timeout=1)
        except Exception as e:
            messagebox.showerror(
                "Error connecting to device!",
                message=f"Error connecting to device: {e}",
            )
            return
        if self.device.is_open:
            self.stop_serial = False
            self.connect_button.configure(
                text="Disconnect", command=self.disconnect_device
            )
            self.device_dropdown.configure(state="disabled")
            self.create_console()
            self.logo_text_label.grid(column=0, row=0, sticky="n")
            self.select_device_label.grid_remove()
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.serial_thread.start()

    def disconnect_device(self) -> None:
        print("Disconnected from device")
        self.stop_serial = True
        self.serial_thread.join()
        self.connect_button.configure(
            text="Connect", command=self.connect_device, state="enabled"
        )
        self.device_dropdown.configure(state="readonly")
        self.select_device_label.grid()
        self.remove_console()
        self.logo_text_label.grid(column=0, row=0, sticky="")

    def update_serial_devices(self) -> None:
        # Get the list of serial devices and update the dropdown
        self.serial_devices = [
            str(port.device) for port in serial.tools.list_ports.comports()
        ]
        if self.device == None:
            if len(self.serial_devices) > 0:
                self.device_dropdown["values"] = self.serial_devices
                self.device_dropdown.configure(state="readonly")
                self.connect_button.configure(state="enabled")
                if self.device_dropdown.current() < 0:
                    self.device_dropdown.current(0)

            else:
                self.device_dropdown.set("No Device Connected")
                self.device_dropdown.configure(state="disabled")
                self.connect_button.configure(state="disabled")
        else:
            if self.device.port not in self.serial_devices:
                self.disconnect_device()
                messagebox.showerror(
                    "Connection Lost!", message="Connection to device lost!"
                )

        # Schedule the next update
        self.update_serial_handle = self.app.after(1000, self.update_serial_devices)

    def create_console(self) -> None:
        # Create a console frame within the right frame
        print("create console")
        self.console_frame = ttk.Frame(
            self.right_frame, style="Card.TFrame", padding=20, width=400, height=500
        )
        self.console_frame.pack()
        self.console_frame.grid_propagate(False)

        console_label = ttk.Label(
            self.console_frame, text="Console:", font=("Arial", 12), anchor="center"
        )
        console_label.grid(column=0, row=0, columnspan=3, sticky="w")

        self.console_text = tk.Text(self.console_frame, wrap=tk.WORD, state="disabled")
        self.console_text.grid(
            column=0, row=1, columnspan=3, sticky="nsew"
        )  # Fill available space

        # Create a scrollbar and associate it with console_text
        scrollbar = ttk.Scrollbar(
            self.console_frame, orient="vertical", command=self.console_text.yview
        )
        scrollbar.grid(column=3, row=1, sticky="ns")

        # Set the yscrollcommand option of console_text to the set method of the scrollbar
        self.console_text.configure(yscrollcommand=scrollbar.set)
        self.console_frame.grid_rowconfigure(2, weight=1)  # Add empty row with weight 1

        self.console_input = ttk.Entry(self.console_frame, font=("Arial", 12))
        self.console_input.bind("<Return>", lambda event: self.send_serial())
        self.console_input.grid(column=0, row=3, columnspan=2, sticky="ew")

        send_button = ttk.Button(
            self.console_frame,
            text="Send",
            style="Accent.TButton",
            command=self.send_serial,
        )
        send_button.grid(column=2, row=3, sticky="e", padx=(5, 0))

        # Create the clear button and bind it to the clear_console_text function
        clear_button = ttk.Button(
            self.console_frame,
            text="Clear",
            style="Accent.TButton",
            command=self.clear_console_text,
        )
        clear_button.grid(column=0, row=4, sticky="w", padx=(0, 5))

        # Create a toggle button and bind it to the toggle_auto_scroll function
        self.auto_scroll_enabled = tk.BooleanVar(value=True)
        toggle_button = ttk.Checkbutton(
            self.console_frame, text="Auto Scroll", variable=self.auto_scroll_enabled
        )
        toggle_button.grid(column=1, row=4, sticky="w", pady=(10, 0))

        # Create a toggle button and bind it to the show_all function
        self.show_all_enabled = tk.BooleanVar(value=True)
        toggle_button = ttk.Checkbutton(
            self.console_frame, text="Show All", variable=self.show_all_enabled
        )
        toggle_button.grid(column=2, row=4, sticky="w", pady=(10, 0))

        # Configure column and row weights to ensure proper resizing behavior
        self.console_frame.columnconfigure(0, weight=1)
        self.console_frame.columnconfigure(1, weight=1)
        self.console_frame.columnconfigure(2, weight=1)
        self.console_frame.rowconfigure(1, weight=1)

    def update_console_text(self, new_text: str) -> None:
        self.console_text.configure(state="normal")
        self.console_text.insert("end", new_text)
        self.console_text.configure(state="disabled")
        # Add auto-scrolling functionality
        if self.auto_scroll_enabled.get():
            self.console_text.see("end")

    def clear_console_text(self) -> None:
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")

    def remove_console(self) -> None:
        self.console_frame.destroy()

    def send_serial(self):
        if self.device is not None:
            input_data = self.console_input.get() + "\n"
            if len(input_data) <= 1:
                return
            self.device.write(input_data.encode())
            self.console_text.config(state="normal")
            self.update_console_text(f">>> {input_data}")
            self.console_text.config(state="disabled")
            self.console_input.delete(0, tk.END)
        else:
            self.console_text.config(state="normal")
            self.update_console_text("Serial port not connected.\n")
            self.console_text.config(state="disabled")

    def read_serial(self):
        while not self.stop_serial and self.device is not None:
            if self.device.inWaiting() > 0:
                data = self.device.readline().decode()
                self.console_text.config(state="normal")
                self.console_text.insert(tk.END, f"{data}")
                self.console_text.config(state="disabled")
        # print("closed")
        if self.device is not None:
            self.device.close()
        self.device = None

    def start(self):
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.app.mainloop()

    def on_closing(self):
        print("closing all threads...")
        self.stop_serial = True
        self.serial_thread.join()
        self.app.destroy()


if __name__ == "__main__":
    app = CubeControlApp()
    app.start()
