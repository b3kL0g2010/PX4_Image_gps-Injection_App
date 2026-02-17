#pyinstaller --clean --onedir --windowed --icon=assets/app_icon.ico --add-data "assets;assets" --name GeoTaggerPro --version-file version.txt main.py
#pyinstaller --clean --onefile --windowed --icon=assets/app_icon.ico --add-data "assets;assets" --name GeoTaggerPro_Portable --version-file version.txt main.py


#py main.py

#git pull origin main
# git reset --hard
# pip install -r requirements.txt




import sys
import os
import webbrowser

from datetime import datetime
from PySide6.QtGui import QIcon

from PySide6.QtWidgets import QMessageBox, QToolButton, QGraphicsDropShadowEffect
from PySide6.QtWidgets import QCheckBox, QPlainTextEdit
    # QPlainTextEdit Planning to add logs/console for real-time processing feedback
    
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QProgressBar, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QPixmap, QIcon

from pipeline import run_pipeline
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl



# ---- Resolve Base Directory into resource_path(for assets) ----
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

LOGO_PATH = resource_path("assets/logo.jpg")
ICON_PATH = resource_path("assets/app_icon.ico")
VIDEO_PATH = resource_path("assets/preview.mp4")
FB_ICON = resource_path("assets/facebook.png")
GMAIL_ICON = resource_path("assets/gmail.png")
LINKEDIN_ICON = resource_path("assets/linkedin.png")



# ---- Drag & Drop Line Edit ----
class DropLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event):
        self.setText(event.mimeData().urls()[0].toLocalFile())


# ---- Worker Thread ----
class Worker(QThread):
    progress = Signal(int)
    finished = Signal(list)
    error = Signal(str)
    log = Signal(str)

    def __init__(self, img, ulg, out, interval, apply_offset):
        super().__init__()
        self.img = img
        self.ulg = ulg
        self.out = out
        self.interval = interval
        self.apply_offset = apply_offset

    def run(self):
        try:
            violations = run_pipeline(
                self.img,
                self.ulg,
                self.out,
                self.apply_offset,
                self.progress.emit,
                self.log.emit
            )
            self.finished.emit(violations)
        except Exception as e:
            self.error.emit(str(e))

# ---- Animated Icon Button for Socmed ----
class AnimatedIconButton(QToolButton):

    def __init__(self, icon_path):
        super().__init__()

        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(28, 28))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: none;")

        # Glow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(0)
        self.shadow.setColor(Qt.white)
        self.shadow.setOffset(0)
        self.setGraphicsEffect(self.shadow)

        # Scale animation
        self.anim = QPropertyAnimation(self, b"iconSize")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    def enterEvent(self, event):
        # Glow on
        self.shadow.setBlurRadius(20)

        # Scale up
        self.anim.stop()
        self.anim.setStartValue(self.iconSize())
        self.anim.setEndValue(QSize(34, 34))
        self.anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        # Remove glow
        self.shadow.setBlurRadius(0)

        # Scale down
        self.anim.stop()
        self.anim.setStartValue(self.iconSize())
        self.anim.setEndValue(QSize(28, 28))
        self.anim.start()

        super().leaveEvent(event)


# ---- Main Window ----
class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setWindowTitle("PX4 EXIF INJECTOR")
        self.setFixedSize(1000, 650)
        self.build_ui()
        self.apply_style()
        # Animate BETA badge
        self.animate_beta(self.beta_label)

    def animate_beta(self, widget):
        self.beta_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(self.beta_effect)

        self.beta_anim = QPropertyAnimation(self.beta_effect, b"opacity")
        self.beta_anim.setDuration(1000)
        self.beta_anim.setStartValue(0.3)
        self.beta_anim.setEndValue(1.0)
        self.beta_anim.setLoopCount(-1)
        self.beta_anim.start()

    # CONTACT ME Side
    def open_facebook(self):
        webbrowser.open("https://www.facebook.com/dasigjp1996")

    def open_gmail(self):
        webbrowser.open("mailto:cpe.dasigjp2025@gmail.com")

    def open_linkedin(self):
        webbrowser.open("https://www.linkedin.com/in/dasigjp2024/")




    # ---- UI Layout ----
    def build_ui(self):
        main_layout = QHBoxLayout(self)

        # LEFT PANEL
        left_panel = QVBoxLayout()
        left_panel.setSpacing(5)

        # HEADER
         # LEFT PANEL
        left_panel = QVBoxLayout()
        left_panel.setSpacing(5)

        # HEADER
        logo_label = QLabel()

        pixmap = QPixmap(LOGO_PATH)

        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
            # scaled_pixmap = pixmap.scaledToWidth(
                300, 120,
                Qt.KeepAspectRatio,                 
                Qt.SmoothTransformation
            )

            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)




        # Title Row
        title_row = QHBoxLayout()

        title = QLabel("GeoTagger Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:26px; font-weight:600;")

        self.beta_label = QLabel("BETA")
        self.beta_label.setStyleSheet("""
            background-color:#FF9800;
            color:black;
            padding:5px 12px;
            border-radius:12px;
            font-weight:700;
            font-size:12px;
        """)


        title_row.addStretch()
        title_row.addWidget(title)
        title_row.addSpacing(10)
        title_row.addWidget(self.beta_label)
        title_row.addStretch()


        subtitle = QLabel("Injects:  Lat / Lon / Alt / Yaw / Pitch / Roll")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color:gray; font-size:13px;")

        left_panel.addWidget(logo_label)
        left_panel.addLayout(title_row)
        left_panel.addWidget(title)
        left_panel.addWidget(subtitle)



        # INPUT FIELDS
        self.img_input = self.create_field("📁 Drag Image Folder Here")
        self.ulg_input = self.create_field("📄 Drag PX4 ULog File Here")
        self.out_input = self.create_field("📦 Drag Output Folder Here")
        self.interval_input = self.create_field("⏱ Sampling Interval (seconds)")
        

        left_panel.addWidget(self.img_input)
        left_panel.addWidget(self.ulg_input)
        left_panel.addWidget(self.out_input)
        left_panel.addWidget(self.interval_input)


        # Checkbox
        self.utc_checkbox = QCheckBox("Apply +8 Hour UTC Offset ( ZR10 CAMERA ONLY )")
        self.utc_checkbox.setChecked(True)  # default ON
        left_panel.addWidget(self.utc_checkbox)


        # PROGRESS BAR
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)

        left_panel.addWidget(self.progress)


        # START BUTTON
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setFixedHeight(45)
        self.start_btn.clicked.connect(self.start_process)

        left_panel.addWidget(self.start_btn)


        # --- Contact Section ---
        contact_row = QHBoxLayout()
        contact_row.addStretch()

        self.fb_btn = AnimatedIconButton(
            os.path.join(FB_ICON)
        )
        self.fb_btn.setIcon(QIcon(os.path.join(FB_ICON)))
        self.fb_btn.setIconSize(QSize(28, 28))
        self.fb_btn.setCursor(Qt.PointingHandCursor)
        self.fb_btn.clicked.connect(self.open_facebook)

        self.gmail_btn = AnimatedIconButton(
            os.path.join(GMAIL_ICON)
        )
        self.gmail_btn.setIcon(QIcon(os.path.join(GMAIL_ICON)))
        self.gmail_btn.setIconSize(QSize(28, 28))
        self.gmail_btn.setCursor(Qt.PointingHandCursor)
        self.gmail_btn.clicked.connect(self.open_gmail)

        self.linkedin_btn = AnimatedIconButton(
            os.path.join(LINKEDIN_ICON)
        )
        self.linkedin_btn.setIcon(QIcon(os.path.join(LINKEDIN_ICON)))
        self.linkedin_btn.setIconSize(QSize(28, 28))
        self.linkedin_btn.setCursor(Qt.PointingHandCursor)
        self.linkedin_btn.clicked.connect(self.open_linkedin)

        contact_row.addWidget(self.fb_btn)
        contact_row.addSpacing(15)
        contact_row.addWidget(self.gmail_btn)
        contact_row.addSpacing(15)
        contact_row.addWidget(self.linkedin_btn)

        contact_row.addStretch()

        left_panel.addSpacing(20)
        left_panel.addLayout(contact_row)

    # ---- Footer ----
        left_panel.addSpacing(30)

        footer = QLabel("GeoTagger Pro • Version 0.1 Beta • © 2025 JP Dasig")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("""
            color: #777;
            font-size: 11px;
        """)

        left_panel.addWidget(footer)

        # ---- RIGHT PANEL STARTS HERE ----
        # RIGHT PANEL (Video Preview)
        right_panel = QVBoxLayout()

        # ---- VIDEO PANEL ----
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        self.video_widget.setAspectRatioMode(Qt.IgnoreAspectRatio)

        right_panel.addWidget(self.video_widget)

        # ---- ADD TO MAIN ----
        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(right_panel, 3)


        # Setup Video Player
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)

        video_path = os.path.join(VIDEO_PATH)
        self.player.setSource(QUrl.fromLocalFile(video_path))

        self.player.setLoops(QMediaPlayer.Infinite)
        self.player.play()
        # ---- Video Panel ENDS HERE ----


        # ---- LOG PANEL ----
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(200)
        self.log_output.setStyleSheet("""
            background-color:#0E0E0E;
            border:1px solid #333;
            border-radius:12px;
            padding:10px;
            color:#00FF99;
            font-family:Consolas;
            font-size:12px;
        """)

        right_panel.addWidget(self.log_output)
        # ---- LOG PANEL ENDS HERE ----
        # ---- UI ENDS HERE -----


    # ---- Styled Input Field ----
    def create_field(self, placeholder):
        field = DropLineEdit()
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(42)
        return field

    # ---- Styling ----
    def apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color:#121212;
                color:white;
                font-family:Segoe UI;
            }

            QLineEdit {
                background:#1e1e1e;
                padding:10px;
                border-radius:10px;
                border:1px solid #2c2c2c;
            }

            QLineEdit:focus {
                border:1px solid #6200EE;
            }

            QPushButton {
                background-color:#6200EE;
                border-radius:12px;
                font-size:14px;
                padding:6px;
            }

            QPushButton:hover {
                background-color:#7F39FB;
            }

            QPushButton:disabled {
                background-color:#333;
                color:#777;
            }

            QProgressBar {
                background:#1e1e1e;
                border-radius:4px;
            }

            QProgressBar::chunk {
                background:#03DAC6;
                border-radius:4px;
            }
            QToolButton {
                border: none;
            }

            QToolButton:hover {
                background-color: rgba(255,255,255,0.1);
                border-radius: 8px;
            }
                           
            QPlainTextEdit {
                background-color: #0E0E0E;
                border: 1px solid #333;
                border-radius: 10px;
                padding: 10px;
                color: #00FF99;
                font-family: Consolas;
                font-size: 12px;
            }
        """)

    # ---- Animated Progress ----
    def animate_progress(self, value):
        self.anim = QPropertyAnimation(self.progress, b"value")
        self.anim.setDuration(400)
        self.anim.setStartValue(self.progress.value())
        self.anim.setEndValue(value)
        self.anim.start()

    # ---- Log Console output ----
    def append_log(self, message):
        self.log_output.appendPlainText(message)
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )


    # ---- Start Processing ----
    def start_process(self):

        image_folder = self.img_input.text().strip()
        ulg_file = self.ulg_input.text().strip()
        output_folder = self.out_input.text().strip()
        interval_text = self.interval_input.text().strip()
        apply_offset = self.utc_checkbox.isChecked()


        # ---- FIELD VALIDATION ----

        if not image_folder:
            QMessageBox.warning(self, "Missing Field",
                                "Please select an Image Folder.")
            return

        if not os.path.isdir(image_folder):
            QMessageBox.warning(self, "Invalid Path",
                                "Image folder does not exist.")
            return

        if not ulg_file:
            QMessageBox.warning(self, "Missing Field",
                                "Please select a ULog file.")
            return

        if not os.path.isfile(ulg_file):
            QMessageBox.warning(self, "Invalid File",
                                "ULog file not found.")
            return

        if not output_folder:
            QMessageBox.warning(self, "Missing Field",
                                "Please select an Output Folder.")
            return

        # Interval validation (if still used)
        if not interval_text:
            QMessageBox.warning(self, "Missing Field",
                                "Please enter interval seconds.")
            return

        try:
            interval = float(interval_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input",
                                "Interval must be a number.")
            return

        # ---- START WORKER ----


        self.log_output.clear()
        self.append_log(
            f"========== Session Started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =========="
        )
        self.append_log("")

        self.start_btn.setEnabled(False)

        self.worker = Worker(
            image_folder,
            ulg_file,
            output_folder,
            interval,
            apply_offset
            
        )

        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.processing_done)
        self.worker.error.connect(self.processing_error)

        self.start_btn.setEnabled(False)
        self.worker.start()

    

    from PySide6.QtWidgets import QMessageBox

    # ---- Notification Area ----
    def processing_done(self, violations):

        self.start_btn.setEnabled(True)

        # No violations → success
        if not violations:
            QMessageBox.information(
                self,
                "Geotagging Completed",
                "All images successfully validated and injected."
            )

            self.log_output.appendPlainText("\n✅ Geotagging SUCCESS.")
            return

        # Violations exist → failure
        max_show = 20
        display_list = violations[:max_show]

        message = (
            "Geotagging FAILED.\n\n"
            "The following images did not match telemetry:\n\n"
        )

        message += "\n".join(display_list)

        message += (
            "\n\nRecommended Actions:\n"
            "• Verify image DateTimeOriginal values.\n"
            "• Ensure correct ULog file is selected.\n"
            "• Enable +8 hour offset if needed.\n"
            "• Remove images captured outside this flight.\n"
        )

        if len(violations) > max_show:
            message += (
                f"\n\n... and {len(violations) - max_show} more."
            )

        QMessageBox.warning(
            self,
            "Geotagging Failed",
            message
        )

        self.log_output.appendPlainText("\n❌ Geotagging FAILED.")
        self.log_output.appendPlainText(
            f"{len(violations)} image(s) rejected."
        )







    def processing_error(self, message):
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, "Processing Error", message)
        print("Error:", message)


# ---- Entry Point ----
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
