import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QMessageBox,
    QComboBox, QTextEdit, QSpacerItem, QSizePolicy, QFrame, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QIcon, QFont
from PIL import Image
from tqdm import tqdm

class ImageConverterThread(QThread):
    update_progress = pyqtSignal(int, str, int, int)
    conversion_complete = pyqtSignal(bool, str)

    def __init__(self, input_folder, output_format, output_method):
        super().__init__()
        self.input_folder = input_folder
        self.output_format = output_format.upper()
        self.output_method = output_method
        self.canceled = False

    def run(self):
        try:
            image_files = [
                f for f in os.listdir(self.input_folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff'))
                and os.path.isfile(os.path.join(self.input_folder, f))
            ]

            total_files = len(image_files)
            if total_files == 0:
                self.conversion_complete.emit(False, "No image files found in the selected folder!")
                return

            if self.output_method == "new_folder":
                output_folder = os.path.join(self.input_folder, f"converted_to_{self.output_format.lower()}")
                os.makedirs(output_folder, exist_ok=True)
            else:
                output_folder = self.input_folder

            for i, filename in enumerate(tqdm(image_files, desc="Converting images")):
                if self.canceled:
                    break

                try:
                    input_path = os.path.join(self.input_folder, filename)
                    base_name = os.path.splitext(filename)[0]
                    
                    if self.output_format in ('JPG', 'JPEG'):
                        output_filename = f"{base_name}.jpg"
                        save_format = "JPEG"
                    else:
                        output_filename = f"{base_name}.{self.output_format.lower()}"
                        save_format = self.output_format

                    output_path = os.path.join(output_folder, output_filename)

                    # Only modify filename if it already exists and isn't the original file
                    if os.path.exists(output_path) and (not os.path.samefile(input_path, output_path)):
                        counter = 1
                        while True:
                            new_base = f"{base_name} ({counter})"
                            if self.output_format in ('JPG', 'JPEG'):
                                test_filename = f"{new_base}.jpg"
                            else:
                                test_filename = f"{new_base}.{self.output_format.lower()}"
                            
                            test_path = os.path.join(output_folder, test_filename)
                            if not os.path.exists(test_path):
                                output_filename = test_filename
                                output_path = test_path
                                break
                            counter += 1

                    # Convert and save
                    with Image.open(input_path) as img:
                        if save_format == "JPEG":
                            img = img.convert("RGB")
                        img.save(output_path, format=save_format, quality=95)

                    # Delete original only in "Replace" mode and if it's not the same file
                    if self.output_method == "replace" and not os.path.samefile(input_path, output_path):
                        os.remove(input_path)

                    progress = int((i + 1) / total_files * 100)
                    action = "Converted" if self.output_method == "new_folder" else "Replaced"
                    self.update_progress.emit(
                        progress, 
                        f"{action}: {filename} → {output_filename}",
                        i + 1,
                        total_files
                    )

                except Exception as e:
                    self.update_progress.emit(
                        int((i + 1) / total_files * 100),
                        f"<font color='orange'>Error converting {filename}: {str(e)}</font>",
                        i + 1,
                        total_files
                    )

            if self.canceled:
                self.conversion_complete.emit(False, "Conversion canceled by user")
            else:
                action = "Converted" if self.output_method == "new_folder" else "Replaced"
                self.conversion_complete.emit(
                    True,
                    f"Successfully {action.lower()} {len(image_files)} images to {self.output_format}!"
                )

        except Exception as e:
            self.conversion_complete.emit(False, f"Conversion failed: {str(e)}")

    def cancel(self):
        self.canceled = True

class ImageConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.conversion_thread = None
        self.setup_icons()
        self.init_ui()
        self.setup_dark_mode()
        self.setup_styles()
        self.setWindowTitle("Bulk Image Converter")
        self.setMinimumSize(800, 600)

    def setup_icons(self):
        icon_path = os.path.join(self.script_dir, "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        icon_path = os.path.join(self.script_dir, "icon.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            QApplication.setWindowIcon(app_icon)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        instruction = QLabel("Select a folder containing images and choose the output format.")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #a6a6a6;
                padding: 10px;
            }
        """)
        layout.addWidget(instruction)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("border: 1px solid #333333;")
        layout.addWidget(separator)

        folder_layout = QHBoxLayout()
        folder_label = QLabel('Images Folder:')
        folder_label.setFixedWidth(100)
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Click Browse to select folder...")
        browse_button = QPushButton('Browse...')
        browse_button.clicked.connect(self.browse_folder)
        browse_button.setFixedWidth(100)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_button)
        layout.addLayout(folder_layout)

        format_layout = QHBoxLayout()
        format_label = QLabel('Output Format:')
        format_label.setFixedWidth(100)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "JPEG", "WEBP", "BMP", "TIFF"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        method_layout = QHBoxLayout()
        method_label = QLabel('Output Method:')
        method_label.setFixedWidth(100)
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "Create new folder for converted images",
            "Replace original images with converted"
        ])
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.method_combo)
        layout.addLayout(method_layout)

        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% (%v/%m)")
        progress_layout.addWidget(self.progress_bar)
        
        self.queue_count_label = QLabel("0 images in queue")
        self.queue_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.queue_count_label.setStyleSheet("color: #a6a6a6; font-size: 11px;")
        progress_layout.addWidget(self.queue_count_label)
        
        layout.addLayout(progress_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Conversion progress will appear here...")
        self.log_output.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 11px;")
        layout.addWidget(self.log_output, 1)

        button_layout = QHBoxLayout()
        
        self.convert_btn = QPushButton('CONVERT')
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setObjectName("convertButton")
        self.convert_btn.setFixedHeight(40)
        
        self.open_folder_btn = QPushButton('OPEN FOLDER')
        self.open_folder_btn.clicked.connect(self.open_current_folder)
        self.open_folder_btn.setObjectName("openFolderButton")
        self.open_folder_btn.setFixedHeight(40)
        
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.open_folder_btn)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        layout.addLayout(button_layout)

    def open_current_folder(self):
        folder_path = self.folder_input.text()
        if folder_path:
            try:
                if sys.platform == "win32":
                    os.startfile(folder_path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", folder_path])
                else:
                    subprocess.run(["xdg-open", folder_path])
            except Exception as e:
                self.log_output.append(f"<font color='orange'>Error opening folder: {str(e)}</font>")
        else:
            self.log_output.append("<font color='orange'>Please select a folder first</font>")

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder with Images",
            options=QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if folder:
            self.folder_input.setText(folder)
            self.update_queue_count()

    def update_queue_count(self):
        input_folder = self.folder_input.text()
        if input_folder and os.path.isdir(input_folder):
            image_files = [
                f for f in os.listdir(input_folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff'))
                and os.path.isfile(os.path.join(input_folder, f))
            ]
            count = len(image_files)
            self.queue_count_label.setText(f"{count} image{'s' if count != 1 else ''} in queue")
            self.progress_bar.setMaximum(count)
        else:
            self.queue_count_label.setText("0 images in queue")
            self.progress_bar.setMaximum(100)

    def setup_dark_mode(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(32, 32, 32))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Button, QColor(60, 60, 60))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(240, 240, 240))
        QApplication.setPalette(palette)

    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #202020;
                border: 1px solid #444;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                selection-background-color: #0078d7;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #0078d7;
            }
            QComboBox {
                padding-right: 20px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border-left: 1px solid #3a3a3a;
                border-radius: 0 4px 4px 0;
            }
            QComboBox::down-arrow {
                image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12"><path fill="white" d="M6 9L1 2h10z"/></svg>');
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #0078d7;
                border: 1px solid #3a3a3a;
                outline: none;
                padding: 4px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                min-width: 100px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1081dd;
            }
            QPushButton:pressed {
                background-color: #005499;
            }
            QPushButton:disabled {
                background-color: #454545;
                color: #808080;
            }
            #convertButton, #openFolderButton {
                background-color: #0078d7;
                font-size: 14px;
            }
            #convertButton:hover, #openFolderButton:hover {
                background-color: #1081dd;
            }
            #convertButton:pressed, #openFolderButton:pressed {
                background-color: #005499;
            }
            QProgressBar {
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 3px;
            }
            QTextEdit {
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
            }
            QMessageBox {
                background-color: #252525;
            }
            QMessageBox QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1081dd;
            }
        """)

    def start_conversion(self):
        input_folder = self.folder_input.text()
        output_format = self.format_combo.currentText()
        output_method = "new_folder" if self.method_combo.currentIndex() == 0 else "replace"

        if not input_folder or not os.path.isdir(input_folder):
            QMessageBox.warning(self, "Warning", "Please select a valid folder containing images!")
            return

        if output_method == "replace":
            reply = QMessageBox.question(
                self,
                "Confirm Replacement",
                "This will permanently replace your original images. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.convert_btn.setEnabled(False)
        self.log_output.clear()

        self.conversion_thread = ImageConverterThread(input_folder, output_format, output_method)
        self.conversion_thread.update_progress.connect(self.update_progress)
        self.conversion_thread.conversion_complete.connect(self.conversion_finished)
        self.conversion_thread.start()

    def update_progress(self, progress, message, current, total):
        self.progress_bar.setValue(current)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setFormat(f"{progress}% ({current}/{total})")
        self.queue_count_label.setText(f"{total - current} remaining")
        self.log_output.append(message)

    def conversion_finished(self, success, message):
        self.convert_btn.setEnabled(True)
        self.progress_bar.setValue(self.progress_bar.maximum() if success else 0)
        self.queue_count_label.setText("0 images in queue")
        
        if success:
            self.log_output.append(f"<font color='green'>{message}</font>")
            QMessageBox.information(self, "Success", message)
        else:
            self.log_output.append(f"<font color='red'>{message}</font>")
            QMessageBox.warning(self, "Error", message)

    def closeEvent(self, event):
        if self.conversion_thread and self.conversion_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Conversion in Progress',
                "A conversion is in progress. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.conversion_thread.cancel()
                self.conversion_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    converter = ImageConverterGUI()
    converter.show()
    sys.exit(app.exec())