import customtkinter as ctk
import tkinter as tk
from screeninfo import get_monitors
from threading import Thread
import keyboard
import pystray
from PIL import Image, ImageDraw
import subprocess
import sys
import time
import wmi
import os

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

def is_external_display_connected():
    try:
        w = wmi.WMI(namespace='wmi')
        for item in w.WmiMonitorConnectionParams():
            video_output = item.VideoOutputTechnology
            if video_output in [2, 3, 4, 5, 6, 2147483648]:
                return True
    except Exception as e:
        print("[WMI] Detection failed:", e)
    return False

class BlackoutWindow(tk.Toplevel):
    def __init__(self, screen):
        super().__init__()
        self.attributes("-topmost", True)
        self.configure(bg="black")
        self.geometry(f"{screen.width}x{screen.height}+{screen.x}+{screen.y}")
        self.overrideredirect(True)
        self.label = tk.Label(self, text="Your display is blocked", font=("Arial", 36, "bold"),
                              fg="white", bg="black")
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        self.bind("<Escape>", lambda e: self.destroy())

class MonItApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MonIt - Display Manager")
        self.geometry("900x550")
        self.resizable(False, False)
        try:
            icon_path = os.path.join(
                getattr(sys, '_MEIPASS', os.path.abspath(".")),
                "icon.ico"
            )
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"[Icon Load Error] {e}")

        self.second_screen = self.detect_secondary_screen()
        self.blackout_window = None
        self.sidebar_buttons = {}
        self.blackout_active = False
        self.was_duplicate = False

        self.block_hotkey = 'ctrl+shift+b'
        self.unblock_hotkey = 'ctrl+shift+u'

        self.block_hotkey_handle = None
        self.unblock_hotkey_handle = None


        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.init_ui()
        self.register_hotkey()
        Thread(target=self.create_tray_icon, daemon=True).start()

    def get_display_mode(self):
        return "extend" if len(get_monitors()) > 1 else "duplicate"

    def detect_secondary_screen(self):
        screens = get_monitors()
        return screens[1] if len(screens) > 1 else None

    def spam_blackout_attempts(self):
        for attempt in range(7):
            self.second_screen = self.detect_secondary_screen()
            if self.second_screen:
                try:
                    if self.blackout_window and self.blackout_window.winfo_exists():
                        self.blackout_window.destroy()
                    self.blackout_window = BlackoutWindow(self.second_screen)
                    self.blackout_active = True
                    print(f"[MonIt] ✅ Blackout successful on attempt {attempt + 1}")
                    break
                except Exception as e:
                    print(f"[MonIt] ❌ Error on blackout attempt {attempt + 1}: {e}")
            else:
                print(f"[MonIt] ℹ️ Attempt {attempt + 1}: second screen not detected yet.")
            time.sleep(0.15)

    def block_secondary_display(self):
        mode = self.get_display_mode()
        if mode == "duplicate":
            print("[MonIt] Switching to Extend Mode...")
            subprocess.run("DisplaySwitch.exe /extend", shell=True)
            self.was_duplicate = True
            time.sleep(1)
        else:
            self.was_duplicate = False
        self.spam_blackout_attempts()

    def unblock_secondary_display(self):
        if self.blackout_window and self.blackout_window.winfo_exists():
            self.blackout_window.destroy()
        self.blackout_window = None
        self.blackout_active = False
        if self.was_duplicate:
            print("[MonIt] Reverting back to Duplicate Mode...")
            subprocess.run("DisplaySwitch.exe /clone", shell=True)
            self.was_duplicate = False

    def register_hotkey(self):
        try:
            if self.block_hotkey_handle:
                keyboard.remove_hotkey(self.block_hotkey_handle)
            if self.unblock_hotkey_handle:
                keyboard.remove_hotkey(self.unblock_hotkey_handle)
        except Exception as e:
            print(f"[Hotkeys] Failed to remove old hotkeys: {e}")

        try:
            self.block_hotkey_handle = keyboard.add_hotkey(
                self.block_hotkey,
                lambda: Thread(target=self.block_secondary_display).start()
            )
            self.unblock_hotkey_handle = keyboard.add_hotkey(
                self.unblock_hotkey,
                lambda: Thread(target=self.unblock_secondary_display).start()
            )
            print(f"[Hotkeys] Registered:\n  Block: {self.block_hotkey} | Unblock: {self.unblock_hotkey}")
        except Exception as e:
            print(f"[Hotkeys] Failed to register new hotkeys: {e}")

    def open_hotkey_popup(self, key_type, label_to_update):
        popup = ctk.CTkToplevel(self)
        popup.geometry("300x180")
        popup.title("Press New Hotkey")
        popup.grab_set()

        info_label = ctk.CTkLabel(popup, text="Press the new hotkey combination...", font=("Segoe UI", 14))
        info_label.pack(pady=10)

        detected_combo = ctk.CTkLabel(popup, text="", font=("Segoe UI", 12))
        detected_combo.pack(pady=5)

        keys_pressed = set()
        combo_final = []

        def on_key_event(event):
            if event.event_type == "down":
                keys_pressed.add(event.name)
                combo = '+'.join(sorted(keys_pressed))
                detected_combo.configure(text=f"Detected: {combo.upper()}")

        hook = keyboard.hook(on_key_event)

        def save_hotkey():
            keyboard.unhook(hook)
            combo = '+'.join(sorted(keys_pressed))
            if combo:
                if key_type == "block":
                    self.block_hotkey = combo
                    label_to_update.configure(text=f"Block Hotkey:\n{combo.upper()}")
                else:
                    self.unblock_hotkey = combo
                    label_to_update.configure(text=f"Unblock Hotkey:\n{combo.upper()}")
                self.register_hotkey()
            popup.destroy()

        save_button = ctk.CTkButton(popup, text="Save Hotkey", command=save_hotkey)
        save_button.pack(pady=10)

        def on_popup_close():
            keyboard.unhook(hook)
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_popup_close)


    def init_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.logo = ctk.CTkLabel(self.sidebar, text="MonIt", font=("Segoe Script", 26, "bold"))
        self.logo.pack(pady=20)

        self.sidebar_buttons['home'] = ctk.CTkButton(self.sidebar, text="Home", command=self.show_home)
        self.sidebar_buttons['keys'] = ctk.CTkButton(self.sidebar, text="Keys", command=self.show_keys)
        self.sidebar_buttons['manage'] = ctk.CTkButton(self.sidebar, text="Manage", command=self.show_manage)
        self.sidebar_buttons['about'] = ctk.CTkButton(self.sidebar, text="About", command=self.show_about)

        for btn in self.sidebar_buttons.values():
            btn.pack(pady=10, padx=10, fill="x")

        self.abort_button = ctk.CTkButton(self.sidebar, text="Abort", fg_color="#ff4d4d",
                                          hover_color="#e63946", text_color="white",
                                          command=self.exit_app)
        self.abort_button.pack(side="bottom", pady=15, padx=10, fill="x")

        self.content = ctk.CTkFrame(self, corner_radius=10, fg_color="#f8f9fa")
        self.content.pack(expand=True, fill="both", padx=10, pady=10)

        self.show_home()

    def show_home(self):
        self.clear_content()
        monitors = get_monitors()
        external_connected = is_external_display_connected()

        if len(monitors) == 1:
            if self.get_display_mode() == "extend":
                text = "Extended Mode:\nNo second screen detected.\nOnly primary screen is active."
            else:
                if external_connected:
                    text = (
                        "Duplicate Mode:\n"
                        "Windows reports 1 screen, but HDMI/VGA output is connected.\n"
                        "Both screens are likely duplicating the primary output."
                    )
                else:
                    text = (
                        "Duplicate Mode:\n"
                        "No external display detected.\n"
                        "Only primary screen is active."
                    )
        else:
            if self.get_display_mode() == "extend":
                mon = monitors[1]
                text = (
                    f"Extended Mode:\nSecond Screen Detected\n"
                    f"Resolution: {mon.width}x{mon.height}\n"
                    f"Position: ({mon.x}, {mon.y})"
                )
            else:
                main = monitors[0]
                text = (
                    f"Duplicate Mode:\n"
                    f"Second screen may not be listed separately\n"
                    f"Resolution: {main.width}x{main.height}\n"
                    f"Both screens are mirroring the same output."
                )

        # ✅ Create a container frame
        container = ctk.CTkFrame(self.content, corner_radius=10, fg_color="#ffffff")
        container.pack(padx=20, pady=(20, 0), fill="x", anchor="n")

        label = ctk.CTkLabel(container, text=text, font=("Segoe UI", 16, "bold"), justify="center", text_color="black")
        label.pack(padx=20, pady=20)

    def show_keys(self):
        self.clear_content()

        title = ctk.CTkLabel(self.content, text="Hotkey Settings", font=("Segoe UI", 18, "bold"))
        title.pack(pady=20)

        hotkey_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        hotkey_frame.pack(padx=20, pady=10, fill="both", expand=True)
        hotkey_frame.grid_columnconfigure(0, weight=1)
        hotkey_frame.grid_columnconfigure(1, weight=0)
        hotkey_frame.grid_columnconfigure(2, weight=1)

        unblock_frame = ctk.CTkFrame(hotkey_frame)
        unblock_frame.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        unblock_label = ctk.CTkLabel(unblock_frame, text=f"Unblock Hotkey:\n{self.unblock_hotkey.upper()}",
                                     font=("Segoe UI", 14), justify="center")
        unblock_label.pack(pady=10)
        ctk.CTkButton(unblock_frame, text="Change Unblock Hotkey",
                      command=lambda: self.open_hotkey_popup("unblock", unblock_label)).pack(pady=5)

        divider = ctk.CTkLabel(hotkey_frame, text="", width=1, fg_color="#ccc", height=180)
        divider.grid(row=0, column=1, sticky="ns")

        block_frame = ctk.CTkFrame(hotkey_frame)
        block_frame.grid(row=0, column=2, padx=(10, 0), pady=10, sticky="nsew")

        block_label = ctk.CTkLabel(block_frame, text=f"Block Hotkey:\n{self.block_hotkey.upper()}",
                                   font=("Segoe UI", 14), justify="center")
        block_label.pack(pady=10)
        ctk.CTkButton(block_frame, text="Change Block Hotkey",
                      command=lambda: self.open_hotkey_popup("block", block_label)).pack(pady=5)

    def show_manage(self):
        self.clear_content()
        title = ctk.CTkLabel(self.content, text="Manage Displays", font=("Segoe UI", 18, "bold"))
        title.pack(pady=20)

        monitors = get_monitors()
        for i, mon in enumerate(monitors):
            label = ctk.CTkLabel(self.content,
                                 text=f"Monitor {i + 1}: {mon.width}x{mon.height} at ({mon.x},{mon.y})",
                                 font=("Segoe UI", 14))
            label.pack(pady=5)

    def show_about(self):
        self.clear_content()
        title = ctk.CTkLabel(self.content, text="About MonIt", font=("Segoe UI", 18, "bold"))
        title.pack(pady=20)

        description = ctk.CTkLabel(self.content,
                                   text="MonIt - Smart Display Blocker\n\nCreated by Lok Nagendra\nVersion 1.0",
                                   font=("Segoe UI", 14), wraplength=600, justify="center")
        description.pack(pady=10)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def hide_to_tray(self):
        self.withdraw()
        print("App hidden to tray.")

    def show_from_tray(self):
        self.deiconify()
        self.lift()

    def exit_app(self):
        try:
            keyboard.remove_hotkey(self.block_hotkey)
        except:
            pass
        try:
            keyboard.remove_hotkey(self.unblock_hotkey)
        except:
            pass
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()
        sys.exit()

    def create_tray_icon(self):
        try:
            # Load icon from bundled path if running as .exe
            icon_path = os.path.join(
                getattr(sys, '_MEIPASS', os.path.abspath(".")),
                "icon.png"
            )
            icon_image = Image.open(icon_path).resize((64, 64))

            self.tray_icon = pystray.Icon("monit", icon_image, "MonIt", menu=pystray.Menu(
                pystray.MenuItem("Show", lambda: self.show_from_tray()),
                pystray.MenuItem("Exit", lambda: self.exit_app())
            ))
            self.tray_icon.run()
        except Exception as e:
            print(f"[Tray Icon Error] {e}")

if __name__ == "__main__":
    app = MonItApp()
    app.mainloop()
