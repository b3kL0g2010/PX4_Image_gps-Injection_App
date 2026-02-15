# 🚀 GeoTagger Pro (PX4 EXIF Injector)

GeoTagger Pro is a desktop application that injects GPS and orientation metadata (Latitude, Longitude, Altitude, Yaw, Pitch, Roll) into images using PX4 ULog flight logs.

⚠ **Experimental Build**  
This software is currently under development. Validate outputs before production use.

---

## ✨ Features

- Inject GPS coordinates into images
- Inject altitude (MSL)
- Inject Yaw / Pitch / Roll metadata
- Modern PySide6 (Qt) user interface
- Drag-and-drop folder selection
- Photogrammetry preview panel
- Windows portable build support

---

# 📂 Project Structure

```
GeoTaggerPro/
│
├── main.py
├── pipeline.py
├── ulog_reader.py
├── telemetry.py
├── image_writer.py
├── requirements.txt
├── README.md
└── assets/
    ├── logo.jpg
    ├── preview.mp4
    ├── facebook.png
    ├── gmail.png
    ├── linkedin.png
    └── app_icon.ico
```

---

# 🖥 Running in Development Mode

---

## 🪟 Windows

### 1️⃣ Create Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

### 2️⃣ Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3️⃣ Run Application

```powershell
python main.py
```

---

## 🐧 Ubuntu

### 1️⃣ Install Python & venv

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

### 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run Application

```bash
python3 main.py
```

---

# 🏗 Building Executable (Windows)

PyInstaller is used to build a standalone executable.

Install it first:

```powershell
pip install pyinstaller
```

---

## 🔹 Option A — Portable Single EXE (onefile)

```powershell
pyinstaller --clean --onefile --windowed ^
--icon=assets/app_icon.ico ^
--add-data "assets;assets" ^
--name GeoTaggerPro ^
main.py
```

Output:

```
dist/GeoTaggerPro.exe
```

You can copy this file to another Windows PC (64-bit).

---

## 🔹 Option B — Folder Distribution (Recommended for Multimedia Stability)

```powershell
pyinstaller --clean --onedir --windowed ^
--icon=assets/app_icon.ico ^
--add-data "assets;assets" ^
--name GeoTaggerPro ^
main.py
```

Output:

```
dist/GeoTaggerPro/
```

Copy the entire folder to another Windows PC.

---

# 📦 Notes on Multimedia

This application uses Qt Multimedia (FFmpeg backend).

If video playback fails on Windows:

- Ensure Media Foundation is installed
- Avoid Windows "N" editions without media pack

---

# 🧪 Experimental Notice

This application is currently in beta stage.  
Please verify output metadata before using in production photogrammetry workflows.

---

# 🛠 Dependencies

- Python 3.9+
- PySide6
- Pandas
- NumPy
- PyULog
- Pillow
- Piexif
- PyInstaller (for building executable)

---

# 📜 License

This project is provided for research and educational use.

---

# 👨‍💻 Author

John Dasig  
GeoTagger Pro – PX4 EXIF Injector
