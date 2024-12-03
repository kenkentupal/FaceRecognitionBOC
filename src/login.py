import sys
from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QPixmap, QPainter, QColor
from PySide2.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox)
import requests
import json
import subprocess


class CustomLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D44;
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                background-color: #363652;
            }
        """)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(45)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Window setup
        self.setWindowTitle("Airport Face Recognition - Login")
        self.setFixedSize(440, 650)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create main container
        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #1E1E2F;
                border-radius: 20px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addWidget(self.container)

        # Container layout
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(30, 30, 30, 30)

        # Title bar with close button
        title_bar = QHBoxLayout()
        close_button = QPushButton("×", self)
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6D6D8D;
                font-size: 20px;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #FF5252;
                color: white;
            }
        """)
        title_bar.addStretch()
        title_bar.addWidget(close_button)
        container_layout.addLayout(title_bar)

        logo_label = QLabel(self)
        try:
            pixmap = QPixmap("../assets/images/ciis.png")
            # Scale the logo to fit within a max width and height, keeping aspect ratio
            max_width = 100  # Set max width
            max_height = 80  # Set max height
            pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        except Exception as e:
            print("Logo not found:", e)
        logo_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(logo_label)

        # Title
        title_label = QLabel("Bureau of Customs", self)
        title_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 0px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Intelligence Group", self)
        subtitle_label.setStyleSheet("color: #6D6D8D; font-size: 14px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(subtitle_label)

        container_layout.addSpacing(20)

        # Email input
        email_label = QLabel("Email", self)
        email_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        container_layout.addWidget(email_label)

        self.email_entry = CustomLineEdit(placeholder="Enter your email")
        container_layout.addWidget(self.email_entry)

        # Password input
        password_label = QLabel("Password", self)
        password_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        container_layout.addWidget(password_label)

        self.password_entry = CustomLineEdit(placeholder="Enter your password")
        self.password_entry.setEchoMode(QLineEdit.Password)
        container_layout.addWidget(self.password_entry)

        container_layout.addSpacing(20)

        # Login button
        self.login_button = QPushButton("Sign In", self)
        self.login_button.setFixedHeight(45)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.login)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4E9F3D;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45903A;
            }
            QPushButton:pressed {
                background-color: #3D8B37;
            }
        """)
        container_layout.addWidget(self.login_button)

        container_layout.addStretch()

        # Footer
        footer_label = QLabel("Need help? Contact support@customs.gov", self)
        footer_label.setStyleSheet("color: #6D6D8D; font-size: 12px;")
        footer_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(footer_label)


    def login(self):
        email = self.email_entry.text()
        password = self.password_entry.text()

        # Show loading state on button
        self.login_button.setEnabled(False)
        self.login_button.setText("Signing in...")

        # Firebase API URL
        firebase_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyAQW87P2nBfvOX4AbCWoOuG5C650y5v5Kk"

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            response = requests.post(
                firebase_api_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            response_data = response.json()

            # Inside the login method of login.py
            if response.status_code == 200:
                # On successful login, pass details to details.py
                with open("user_details.json", "w") as file:
                    json.dump({"email": email}, file)
                # Run details.py (this is where the logged-in account is passed)
                subprocess.Popen(["python", "main_window.py"])
                QTimer.singleShot(500, self.close)  # Close login window after a short delay

                loading_dialog = QMessageBox(self)
                loading_dialog.setWindowTitle("Loading")
                loading_dialog.setText("Loading, please wait...")
                loading_dialog.setStandardButtons(QMessageBox.NoButton)
                loading_dialog.setStyleSheet("""
                    QMessageBox {
                        background-color: #1E1E2F;
                        color: white;
                        border: none;
                    }
                    QLabel {
                        color: white;
                        font-size: 14px;
                    }
                """)
                loading_dialog.show()


            else:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                error_dialog = QMessageBox(self)
                error_dialog.setIcon(QMessageBox.Critical)
                error_dialog.setWindowTitle("Login Failed")
                error_dialog.setText(f"<b>Error:</b> {error_message}")
                error_dialog.setInformativeText("Please check your credentials and try again.")
                error_dialog.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
                error_dialog.setDefaultButton(QMessageBox.Retry)
                error_dialog.setStyleSheet("""
                    QMessageBox {
                        background-color: #2D2D44;
                        color: white;
                        border: none;
                        border-radius: 12px;
                        padding: 20px;
                    }
                    QLabel {
                        color: white;
                        font-size: 14px;
                    }
                    QPushButton {
                        background-color: #4E9F3D;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #45903A;
                    }
                    QPushButton:pressed {
                        background-color: #3D8B37;
                    }
                    QMessageBox QPushButton {
                        min-width: 100px;
                    }
                """)
                error_dialog.exec_()

                # Reset button state
                self.login_button.setEnabled(True)
                self.login_button.setText("Sign In")

        except Exception as e:
            QMessageBox.critical(self, "Login Failed", f"An error occurred: {e}")
            self.login_button.setEnabled(True)
            self.login_button.setText("Sign In")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
