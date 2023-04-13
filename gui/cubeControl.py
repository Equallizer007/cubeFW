"""CUBEcontrol v1.0
This is the CubeControl gui apllication designed to control the edm-mashine CUBE

@author Marcus Voss mail@marcusvoss.de/marcus.voss@campus.tu-berlin.de
@date 02.04.2023
    
"""
import tkinter as tk  # Importing the Tkinter library for creating graphical user interfaces
from tkinter import (
    ttk,
    messagebox,
    StringVar,
)  # Importing additional Tkinter classes for themed widgets, message boxes, and string variables
import sv_ttk  # Importing a custom module for additional themed Tkinter widgets (assuming it's a custom module)
import serial  # Importing the PySerial library for communicating with serial devices
import serial.tools.list_ports  # Importing a utility to list available serial ports
import threading  # Importing the threading module for creating and managing threads
import re  # Importing the regular expressions module for advanced string manipulation
import os  # Importing the OS module for interacting with the operating system


# current file path to allow the app to be called from outside its own workspace
current_path = os.path.dirname(os.path.realpath(__file__))


class Console:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent

    def create_console(self) -> None:
        self.console_frame = ttk.Frame(self.parent, padding=20, width=400, height=500)
        self.console_frame.pack()
        self.console_frame.grid_propagate(False)

        console_label = ttk.Label(self.console_frame, text="Console:", font=("Arial", 12), anchor="center")
        console_label.grid(column=0, row=0, columnspan=3, sticky="w")

        self.console_text = tk.Text(self.console_frame, wrap=tk.WORD, state="disabled", font=("Arial", 10))
        self.console_text.tag_config("send", foreground="green")
        self.console_text.tag_config("error", background="yellow", foreground="red")
        self.console_text.grid(column=0, row=1, columnspan=3, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.console_frame, orient="vertical", command=self.console_text.yview)
        scrollbar.grid(column=3, row=1, sticky="ns")
        self.console_text.configure(yscrollcommand=scrollbar.set)
        self.console_frame.grid_rowconfigure(2, weight=1)
        self.placeholder_text = "Type your command here..."

        self.console_input = ttk.Entry(self.console_frame, font=("Arial", 12))
        self.console_input.bind("<Return>", lambda event: self.send_serial())
        self._set_placeholder_text()
        self._bind_entry_events(self.console_input)
        self.console_input.grid(column=0, row=3, columnspan=2, sticky="ew")

        send_button = ttk.Button(
            self.console_frame,
            text="Send",
            style="Accent.TButton",
            command=self.send_serial,  # Assuming you have a 'send_serial' function in your main class
        )
        send_button.grid(column=2, row=3, sticky="e", padx=(5, 0))

        clear_button = ttk.Button(
            self.console_frame,
            text="Clear",
            style="Accent.TButton",
            command=self.clear_console_text,
        )
        clear_button.grid(column=0, row=4, sticky="w", padx=(0, 5))

        self.auto_scroll_enabled = tk.BooleanVar(value=True)
        toggle_button = ttk.Checkbutton(self.console_frame, text="Auto Scroll", variable=self.auto_scroll_enabled)
        toggle_button.grid(column=1, row=4, sticky="w", pady=(10, 0))

        self.show_all_enabled = tk.BooleanVar(value=False)
        toggle_button = ttk.Checkbutton(self.console_frame, text="Show All", variable=self.show_all_enabled)
        toggle_button.grid(column=2, row=4, sticky="w", pady=(10, 0))

        self.console_frame.columnconfigure(0, weight=1)
        self.console_frame.columnconfigure(1, weight=1)
        self.console_frame.columnconfigure(2, weight=1)
        self.console_frame.rowconfigure(1, weight=1)

    def update_console_text(self, new_text: str, send=False) -> None:
        if new_text[-1] != "\n":
            new_text += "\n"

        # filter esp-inernal messages
        if not self.show_all_enabled.get() and "\r\n" in new_text and "parse" not in new_text:
            return

        new_text = new_text.replace("\r", "")
        # print(">> ", new_text.encode())
        self.console_text.configure(state="normal")
        if send:
            self.console_text.insert("end", new_text, "send")
        elif "error" in new_text.lower():
            self.console_text.insert("end", new_text, "error")
        else:
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
        if self.app.device is not None:
            input_data = self.console_input.get()
            if len(input_data) <= 0:
                return
            if input_data == self.placeholder_text:
                return
            self.app.send_msg(input_data)

        else:
            self.console_text.config(state="normal")
            self.update_console_text("Serial port not connected.\n")
            self.console_text.config(state="disabled")

    def _remove_placeholder_text(self):
        if self.console_input.get() == self.placeholder_text:
            self.console_input.delete(0, "end")
            self.console_input.configure(foreground="black")

    def _set_placeholder_text(self):
        if len(self.console_input.get()) == 0:
            self.console_input.delete(0, "end")
            self.console_input.insert(0, self.placeholder_text)
            self.console_input.configure(foreground="#a9a9a9")

    def _bind_entry_events(self, entry_widget):
        entry_widget.bind("<FocusIn>", lambda event: self._remove_placeholder_text())
        entry_widget.bind("<FocusOut>", lambda event: self._set_placeholder_text())


class ConfigWindow:
    def __init__(self, parent):
        # refernce to the window and parent
        self.window = None
        self.parent = parent

        # Define default configurations with their names, display texts, and data types
        default_config = {
            "ontime": [4000, "OnTime (ns):", "int"],
            "offtime": [12000, "OffTime (ns):", "int"],
            "lower_thr": [3.5, "Lower Threshold (V):", "float"],
            "upper_thr": [30.0, "Upper Threshold (V):", "float"],
            "auto_sens": [10, "Sensitivity:", "int"],
        }

        # Create the config dictionary with StringVars for each configuration value
        self.config = {k: [v[0], StringVar(value=str(v[0])), v[1], v[2]] for k, v in default_config.items()}

    def get(self, var):
        return self.config[var][0]

    def open(self):
        # Check if the window already exists, and if so, destroy it
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            return

        # Create the configuration window and set its properties
        self.window = tk.Toplevel(self.parent)
        self.window.title("Config")
        self.window.resizable(False, False)
        self.window.transient(self.parent)

        # Add inner padding using a ttk.Frame
        inner_frame = ttk.Frame(self.window, padding=(20, 20, 20, 20))
        inner_frame.pack(fill="both", expand=True)
        self.window.geometry("+%d+%d" % (self.parent.winfo_x() + 400, self.parent.winfo_y() + 200))

        # Define the label frames' information
        label_frames = [
            ("Generator Settings", 0, 0, ("ontime", "offtime")),
            ("ADC Settings", 0, 1, ("lower_thr", "upper_thr")),
            ("Automode Settings", 0, 2, ("auto_sens",)),
        ]

        # Create the label frames and their corresponding entries
        for lf_text, lf_col, lf_row, lf_vars in label_frames:
            label_frame = ttk.LabelFrame(inner_frame, text=lf_text, padding=10)
            label_frame.grid(column=lf_col, row=lf_row, columnspan=3, sticky="nesw", padx=0, pady=5)
            for i, var in enumerate(lf_vars):
                ttk.Label(label_frame, text=self.config[var][2]).grid(column=0, row=i)
                ttk.Entry(
                    label_frame,
                    width=9,
                    validate="focusout",
                    validatecommand=(
                        self.window.register(lambda s, v=var: self.validate_entry(s, v)),
                        "%P",
                    ),
                    textvariable=self.config[var][1],
                ).grid(column=1, row=i, sticky="nesw", padx=15)

    def validate_entry(self, input_str, strvar):
        # Initialize input_value and get the data type from the config dictionary
        input_value = 0
        ttype = self.config[strvar][3]

        # Try to parse the input string based on the data type
        try:
            if ttype == "int":
                input_value = int(input_str)
            elif ttype == "float":
                input_value = float(input_str)
            else:
                input_value = -1

            # Check if the input value is within the allowed range
            if 0 < input_value <= 100000:
                # If the input value is valid, update the configuration value
                self.config[strvar][0] = input_value
                return True
        except ValueError:
            pass
        # If the input value is not valid, reset the entry to the last valid value
        self.config[strvar][1].set(str(self.config[strvar][0]))
        return False


class CubeControlApp:
    def __init__(self) -> None:
        self.device = None
        self.serial_devices = []
        self.update_serial_handle = None

        self.app = tk.Tk()
        #self.app.iconbitmap(current_path + "/img/icon.ico")
        self.app.title("CUBEcontrol --- version 1.0")
        self.app.geometry("800x500")
        self.app.resizable(False, False)

        self.adc_pattern = re.compile(r"<ADC>.*calc:(\d+\.\d+)V")
        self.pos_pattern = re.compile(r"POS> homed:(\d) steps:(\d+) pos:(\d+\.\d{4})")
        self.config_window = ConfigWindow(self.app)

        self.setup_ui()

    def setup_ui(self) -> None:
        # set theme
        sv_ttk.set_theme("light")

        # Create frames and configure grid
        self.right_frame, self.left_frame = self.create_frames(self.app)
        self.console = Console(self, self.right_frame)

        # Load and display the image, text, and logo in the right frame
        self.display_image_text_logo()

        # Add the select device label and dropdown in the left frame
        self.add_device_selection()

        # Schedule the automatic update of the serial devices list
        self.update_serial_handle = self.app.after(0, self.update_serial_devices)

    def create_frames(self, app):
        frame_settings = [
            ("right_frame", tk.RIGHT, 400, 500, 0),
            ("left_frame", tk.LEFT, 400, 500, 20),
        ]

        for name, side, width, height, padding in frame_settings:
            frame = ttk.Frame(app, height=height, width=width, padding=padding, borderwidth=0)
            frame.pack(side=side, fill=tk.BOTH, expand=False)
            frame.pack_propagate(False)
            frame.grid_propagate(False)
            setattr(self, name, frame)

        self.left_frame.columnconfigure(1, weight=1)
        self.left_frame.rowconfigure(0, weight=1)

        return self.right_frame, self.left_frame

    def display_image_text_logo(self):
        self.image = tk.PhotoImage(file=current_path + "/img/background.png")
        self.image_canvas = tk.Canvas(self.right_frame, width=400, height=500, bd=0, highlightthickness=0)
        self.image_canvas.grid()
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.image)

        version_text = "Marcus Voß 2023"
        self.image_canvas.create_text(330, 480, text=version_text)

        self.logo_image = tk.PhotoImage(file=current_path + "/img/logo.png")
        logo_labels = [
            ("logo_image_label", self.logo_image, None, 0, 0, 3),
            ("logo_text_label", None, "CUBEcontrol", 0, 0, 3),
        ]

        for name, image, text, col, row, colspan in logo_labels:
            label = ttk.Label(
                self.left_frame,
                image=image,
                text=text,
                anchor="center",
                font=("Arial", 24, "bold"),
                width=400,
            )
            label.grid(column=col, row=row, columnspan=colspan)
            setattr(self, name, label)

    def add_device_selection(self):
        self.select_device_label = ttk.Label(self.left_frame, text="Select a Device:", font=("Arial", 12))
        self.select_device_label.grid(column=0, row=1, sticky=tk.W, columnspan=3, pady=10, padx=10)

        self.serial_devices = [str(port.device) for port in serial.tools.list_ports.comports()]
        self.device_dropdown = ttk.Combobox(
            self.left_frame,
            values=self.serial_devices,
            font=("Arial", 12),
            state="disabled",
        )
        self.device_dropdown.grid(column=0, row=2, padx=10)

        self.connect_button = ttk.Button(
            self.left_frame,
            text="Connect",
            style="Accent.TButton",
            state="disabled",
            command=self.connect_device,
        )
        self.connect_button.grid(column=1, row=2, sticky=tk.W)

    def connect_device(self) -> None:
        selected_device = self.device_dropdown.get()
        print(f"Connecting to {selected_device}...")
        try:
            self.device = serial.Serial(selected_device, 115200, timeout=1)
        except Exception as e:
            messagebox.showerror(
                "Error connecting to device!",
                message=f"Error connecting to device: {e}",
            )
            return
        if self.device.is_open:
            self.stop_serial = False
            self.connect_button.configure(text="Disconnect", command=self.disconnect_device)
            self.device_dropdown.configure(state="disabled")
            self.create_control_widgets()
            self.console.create_console()
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.console.update_console_text(f"Connected to {self.device.port} @  baudrate {self.device.baudrate}")
            # send intial messages
            self.send_msg("M0 ;restart device")
            self.send_msg("G91 ; relative positioning")
            self.send_msg("M1 500 ;set report interval to 500ms")
            self.serial_thread.start()

    def disconnect_device(self) -> None:
        print("Disconnected from device")
        self.stop_serial = True
        self.serial_thread.join()
        self.connect_button.configure(text="Connect", command=self.connect_device, state="enabled")
        self.device_dropdown.configure(state="readonly")
        self.select_device_label.grid()
        self.console.remove_console()
        self.remove_control_widgets()
        self.device = None

    def fill_movement_frame(self, parent):
        # Labels and buttons settings
        widget_settings = [
            ("current_position_label", ttk.Label, "?", 0, 0, {}),
            ("current_steps_label", ttk.Label, "Steps: ?", 1, 0, {}),
            ("homed_label", ttk.Label, "Not Homed", 2, 0, {}),
            (
                "up_arrow_button",
                ttk.Button,
                "↑ Up",
                0,
                1,
                {"sticky": "nesw", "pady": 10},
            ),
            (
                "down_arrow_button",
                ttk.Button,
                "↓ Down",
                1,
                1,
                {"sticky": "nesw", "pady": 10, "padx": (15, 15)},
            ),
            ("home_button", ttk.Button, "Home", 0, 3, {"sticky": "nesw"}),
            (
                "restart_button",
                ttk.Button,
                "Restart",
                1,
                3,
                {"sticky": "nesw", "padx": (15, 15)},
            ),
            ("touch_button", ttk.Button, "Touch", 2, 3, {"sticky": "nesw"}),
        ]

        commands = [
            None,
            None,
            None,
            lambda: self.send_msg(
                f"G1 Z-{self.movement_steps[self.movement_steps_dropdown.current()]} ;move up {self.movement_steps_dropdown.get()}"
            ),
            lambda: self.send_msg(
                f"G1 Z{self.movement_steps[self.movement_steps_dropdown.current()]} ;move down {self.movement_steps_dropdown.get()}"
            ),
            lambda: self.send_msg("G28 ;home"),
            lambda: self.send_msg("M0 ;restart"),
            lambda: self.send_msg(
                f"M102 {self.config_window.get('lower_thr')} {self.config_window.get('upper_thr')} ;touchmode"
            ),
        ]

        # Create and grid labels and buttons
        for idx, (name, widget_class, text, col, row, options) in enumerate(widget_settings):
            widget = widget_class(parent, text=text, width=9)
            widget.grid(column=col, row=row, **options)
            if commands[idx] is not None:
                widget.configure(command=commands[idx])
            setattr(self, name, widget)

        # Movement Step dropdown
        self.movement_steps = [0.5, 1, 2.5, 5, 10, 100, 1000, 5000]
        movement_steps_labels = [
            "0.5µm",
            "1µm",
            "2.5µm",
            "5µm",
            "10µm",
            "100µm",
            "1mm",
            "5mm",
        ]
        self.movement_steps_dropdown = ttk.Combobox(
            parent,
            values=movement_steps_labels,
            font=("Arial", 11),
            state="readonly",
            width=6,
        )
        self.movement_steps_dropdown.current(0)
        self.movement_steps_dropdown.grid(column=2, row=1, pady=10, sticky="w")

    def fill_generator_frame(self, parent):
        # Buttons settings
        widget_settings = [
            (
                "config_button",
                ttk.Button,
                "Config",
                0,
                0,
                {"sticky": "nesw", "pady": (0, 10)},
            ),
            ("generator_enable_button", ttk.Button, "Enable", 0, 1, {"sticky": "nesw"}),
            (
                "generator_disable_button",
                ttk.Button,
                "Disable",
                1,
                1,
                {"sticky": "nesw", "padx": (15, 15)},
            ),
            (
                "generator_auto_button",
                ttk.Button,
                "Auto ON",
                1,
                0,
                {"sticky": "nesw", "padx": (15, 15), "pady": (0, 10)},
            ),
            ("generator_auto_disable_button", ttk.Button, "Auto OFF", 2, 0, {"sticky": "nesw", "pady": (0, 10)}),
        ]

        commands = [
            self.config_window.open,
            lambda: self.send_msg(
                f"M100 {self.config_window.get('ontime')} {self.config_window.get('offtime')} ;enable generator"
            ),
            lambda: self.send_msg("M101 ;disable generator"),
            lambda: self.send_msg(
                f"M103 {self.config_window.get('lower_thr')} {self.config_window.get('upper_thr')} {self.config_window.get('auto_sens')} ;auto mode"
            ),
            lambda: self.send_msg("M104 ;auto off"),
        ]

        for i, (name, widget_class, text, col, row, options) in enumerate(widget_settings):
            widget = widget_class(parent, text=text, width=9, command=commands[i])
            widget.grid(column=col, row=row, **options)

    def update_serial_devices(self) -> None:
        # Get the list of serial devices and update the dropdown
        self.serial_devices = [str(port.device) for port in serial.tools.list_ports.comports()]
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
                messagebox.showerror("Connection Lost!", message="Connection to device lost!")

        # Schedule the next update
        self.update_serial_handle = self.app.after(1000, self.update_serial_devices)

    def create_control_widgets(self) -> None:
        self.logo_text_label.grid(column=0, row=0, sticky="n")
        self.select_device_label.grid_remove()

        self.control_frame = ttk.Frame(self.left_frame, padding=10)
        self.control_frame.grid(column=0, row=1, columnspan=2, sticky="w")

        frames = [
            ("generator_label_frame", "Generator"),
            ("adc_label_frame", "ADC"),
            ("movement_label_frame", "Movement"),
        ]

        for idx, (name, text) in enumerate(frames):
            frame = ttk.LabelFrame(self.control_frame, text=text, padding=10)
            frame.grid(column=0, row=idx, columnspan=3, sticky="nesw", padx=0, pady=5)
            setattr(self, name, frame)

        self.adc_voltage_label = ttk.Label(self.adc_label_frame, text="ADC voltage: ?")
        self.adc_voltage_label.grid(column=0, row=0, pady=5, padx=(10, 0))

        self.fill_generator_frame(self.generator_label_frame)
        self.fill_movement_frame(self.movement_label_frame)

    def remove_control_widgets(self) -> None:
        self.logo_text_label.grid(column=0, row=0, sticky="")
        self.control_frame.destroy()

    def send_msg(self, input_data):
        if len(input_data) <= 0 or self.device is None:
            return
        if input_data[-1] != "\n":
            input_data += "\n"
        self.device.write(input_data.encode())
        self.console.update_console_text(f">>> {input_data}", True)

    def parse_msg(self, msg):
        match_adc_voltage = self.adc_pattern.search(msg)
        if match_adc_voltage:
            voltage = float(match_adc_voltage.group(1))
            self.adc_voltage_label.configure(text=f"ADC voltage: {voltage}V")
            return 1
        pos_match = self.pos_pattern.search(msg)

        if pos_match:
            homed = bool(int(pos_match.group(1)))
            steps = int(pos_match.group(2))
            pos = float(pos_match.group(3))
            self.current_steps_label.configure(text=f"Steps: {steps}")
            self.current_position_label.configure(text=f"{pos:.4f}mm")
            self.homed_label.configure(text="Homed" if homed else "Not Homed")
            return 1
        return 0

    def read_serial(self):
        while not self.stop_serial and self.device is not None:
            if self.device.inWaiting() > 0:
                data = None
                try:
                    data = self.device.readline().decode()
                except UnicodeDecodeError as e:
                    #print(e)
                    pass
                if self.parse_msg(data) == 0:
                    self.console.update_console_text(data)
        if self.device is not None:
            self.device.close()
        self.device = None

    def start(self):
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.app.mainloop()

    def on_closing(self):
        print("closing all threads...")
        self.stop_serial = True
        if hasattr(self, "serial_thread"):
            self.serial_thread.join()
        self.app.destroy()


if __name__ == "__main__":
    app = CubeControlApp()
    app.start()
