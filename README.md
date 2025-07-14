# MonIt - Monitor Interceptor

MonIt is a lightweight Python desktop application that **detects secondary displays or projectors** and gives you control over what is shown on them. It is ideal for classrooms, meetings, or any environment where sensitive information should not be shared on extended screens.

## 🧠 Features

- 🔌 **Live Detection**: Instantly detects when a new display/projector is connected.
- 🖥️ **Screen Blocking**: Press a hotkey to show a fullscreen black screen on the secondary display with the message **"Your display is blocked"**.
- 🎛️ **GUI Panel**: View current display status, set the blocking hotkey, and manage settings easily.
- 🔧 **Auto-Start on Boot**: Registers itself with Windows Task Scheduler to start monitoring on system boot.
- 🛑 **Manual Override**: If launched manually, the full GUI is shown without affecting startup behavior.
- 🖱️ **System Tray**: Minimize to tray for lightweight background running.

---

## 📸 Screenshot

> (Add a screenshot of the GUI here if available)

---

## 🛠️ Tech Stack

- **Python 3.8+**
- `tkinter` / `customtkinter`
- `screeninfo` – Monitor detection
- `keyboard` – Hotkey management
- `pystray` – System tray icon
- `Pillow` – Drawing tray icon
- `wmi` – Windows hardware interface
- `subprocess`, `os`, `threading`

---

## ⚙️ Setup Instructions

download the .exe file in the dist folder

-- can connect if facing any problems.

--thankyou
