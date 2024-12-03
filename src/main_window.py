import sys
import os
import time
import hashlib
import pyodbc
from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide2.QtCore import Qt, QTimer
from header import create_header
from sidebar import create_sidebar
from image import ImageSection
from control import ControlSection
from details import DetailsSection

class CustomWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_image)
        self.timer.start(1000)  # Check every second
        self.latest_image_hash = None  # Store the hash of the latest image

    def initUI(self):
        self.setWindowTitle("Window with Header, Sidebar, and Sections")
        self.setStyleSheet("background-color: #FFFFF;")

        # Main Layout
        main_layout = QVBoxLayout()

        # Add Header
        header_layout = create_header(self)
        main_layout.addLayout(header_layout)

        # Add Sidebar
        sidebar_widget = QWidget(self)
        sidebar_widget.setFixedWidth(350)
        sidebar_layout = create_sidebar(self)
        sidebar_widget.setLayout(sidebar_layout)

        # Main Content Layout
        content_layout = QVBoxLayout()

        # Upper Section (Image)
        image_section = ImageSection(self)
        content_layout.addWidget(image_section)

        # Center Section (Control)
        control_section = ControlSection(self)
        content_layout.addWidget(control_section)

        # Lower Section (Details)
        self.details_section = DetailsSection(self)  # Ensure this is set
        content_layout.addWidget(self.details_section)

        # Lock Sidebar and Combine Layouts
        locked_layout = QHBoxLayout()
        locked_layout.addWidget(sidebar_widget)  # Sidebar remains locked
        locked_layout.addLayout(content_layout)  # Main content

        # Add Everything to Main Layout
        main_layout.addLayout(locked_layout)
        self.setLayout(main_layout)

    def fetch_mdb_data(self):
        # This function is now triggered when the button is clicked
        mdb_path = r"C:\Users\Public\Documents\Plustek-SecureScan\Result.mdb"
        details = self.get_latest_mdb_value(mdb_path)  # Call the MDB method

        # Update the details section with the fetched data
        if self.details_section:
            self.details_section.update_details(details)

    def get_latest_mdb_value(self, mdb_path):
        # Connect to the MDB file and get the latest record with additional fields
        conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + mdb_path
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Query to get the latest record with required fields
            query = """
                SELECT TOP 1 
                    [First Name], [Last Name], [Valid Until], [Document Number], 
                    [Gender], [Nationality], [Index]
                FROM Result
                ORDER BY [Index] DESC
            """
            cursor.execute(query)

            # Fetch the result and return a dictionary with the fields
            row = cursor.fetchone()
            if row:
                return {

                    "First Name": row[0],
                    "Last Name": row[1],
                    "Valid Until": row[2],
                    "Document Number": row[3],
                    "Gender": row[4],
                    "Nationality": row[5],
                    "Date of Birth": row[6]
                }
        except Exception as e:
            print(f"Error accessing MDB file: {e}")
        return None

    def update_label(self, image_path):
        # Update the content label with the new image and MDB value
        # DO NOT call get_latest_mdb_value here since you want it to run only on button click
        pass

    def check_for_image(self):
        # Directory to monitor for new image
        image_directory = r"C:\Users\Public\Documents\Plustek-SecureScan\Image"
        latest_image = self.get_latest_image(image_directory)

        if latest_image:
            latest_image_hash = self.calculate_file_hash(latest_image)
            if self.latest_image_hash != latest_image_hash:
                # A truly new image is found

                self.latest_image_hash = latest_image_hash
                self.update_label(latest_image)



    def get_latest_image(self, directory):
        # Get the latest modified image in the directory
        images = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if images:
            latest_image = max(images, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
            latest_image_path = os.path.join(directory, latest_image)
            return latest_image_path
        return None

    def calculate_file_hash(self, filepath):
        # Calculate a hash for the file to ensure content uniqueness
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def clear_details(self):
        """Clear the text/content in the details section."""
        if self.details_section:
            self.details_section.update_details(
                None)  # Assuming `update_details` can handle a `None` value to clear the display


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the window
    window = CustomWindow()
    window.showMaximized()  # Display the window in maximized mode

    sys.exit(app.exec_())
