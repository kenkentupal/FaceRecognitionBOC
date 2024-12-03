import os
import shutil
from PySide2.QtWidgets import QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QHBoxLayout
from PySide2.QtGui import QPixmap
from PySide2.QtCore import Qt
from PySide2.QtCore import QSize

def delete_folder_contents(folder_path):
    """Deletes all files inside the given folder."""
    try:
        # Loop through all files in the folder and delete them
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        print(f"All contents in {folder_path} have been deleted.")
    except Exception as e:
        print(f"Error clearing folder: {e}")

def create_sidebar(parent):
    """Creates the sidebar layout."""
    sidebar_layout = QVBoxLayout()

    # Add spacing before "ID Scan" section
    sidebar_layout.addItem(QSpacerItem(0, 50, QSizePolicy.Minimum, QSizePolicy.Fixed))  # Spacer for vertical space

    # Create the horizontal layout for ID icon and label
    id_scan_layout = QHBoxLayout()

    id_icon_label = QLabel(parent)
    id_icon_label.setPixmap(QPixmap("../assets/images/id.png"))  # Load the icon from the path
    id_scan_layout.setSpacing(10)
    id_icon_label.setScaledContents(True)  # Ensure the image scales properly
    id_icon_label.setFixedSize(40, 25)  # Set fixed size for the icon

    id_scan_label = QLabel("ID Scan", parent)
    id_scan_label.setStyleSheet("color: #000000; font-size: 25px; font-weight: regular;")

    id_scan_layout.addWidget(id_icon_label)
    id_scan_layout.addWidget(id_scan_label)

    # Add the horizontal layout to the sidebar layout
    sidebar_layout.addLayout(id_scan_layout)

    # Add static sidebar buttons
    sidebar_button_1 = QPushButton("Valid", parent)
    sidebar_button_1.setStyleSheet("background-color: #4CAF50; color: white; font-size: 35px;")
    sidebar_button_1.setEnabled(False)  # Make the button non-clickable
    sidebar_layout.addWidget(sidebar_button_1)

    # Add spacing before "Biometric" section
    sidebar_layout.addItem(QSpacerItem(0, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))  # Spacer for vertical space

    # Create the horizontal layout for Biometric icon and label
    biometric_layout = QHBoxLayout()

    biometric_icon_label = QLabel(parent)
    biometric_icon_label.setPixmap(QPixmap("../assets/images/biometric.png"))  # Use a new icon path for biometric
    biometric_layout.setSpacing(10)
    biometric_icon_label.setScaledContents(True)  # Ensure the image scales properly
    biometric_icon_label.setFixedSize(25, 25)  # Set fixed size for the icon

    biometric_label = QLabel("Biometric", parent)
    biometric_label.setStyleSheet("color: #000000; font-size: 25px; font-weight: regular;")

    biometric_layout.addWidget(biometric_icon_label)
    biometric_layout.addWidget(biometric_label)

    # Add the horizontal layout to the sidebar layout
    sidebar_layout.addLayout(biometric_layout)

    sidebar_button_2 = QPushButton("Match", parent)
    sidebar_button_2.setStyleSheet("background-color: #4CAF50; color: white; font-size: 35px;")
    sidebar_button_2.setEnabled(False)  # Make the button non-clickable
    sidebar_layout.addWidget(sidebar_button_2)

    # Add a spacer to push content to the top
    sidebar_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

    # Create a horizontal layout for "Clear" and "Blur" buttons
    button_layout = QHBoxLayout()

    # Add the Clear button with border, black font, and trash icon
    clear_button = QPushButton(parent)
    clear_button.setStyleSheet("""
        border: 2px solid #000000;
        color: #000000;
        font-size: 35px;
        padding: 10px;
        border-radius: 15px;  /* Smooth rounded edges */
    """)
    clear_icon = QPixmap("../assets/images/trash.png")  # Path to the trash icon image
    clear_button.setIcon(clear_icon)
    clear_button.setIconSize(QSize(30, 30))  # Set the size of the icon next to the text
    clear_button.setText("Clear")
    clear_button.clicked.connect(lambda: [
        delete_folder_contents(r'C:\Users\Public\Documents\Plustek-SecureScan\Image'),
        # Clear the images in this directory
        delete_folder_contents('../capture'),  # Clear the images in the capture directory
        parent.clear_details()  # Additional cleanup for the parent widget (if needed)
    ])

    button_layout.addWidget(clear_button)

    # Add the Blur button with border, black font, and eye icon
    blur_button = QPushButton(parent)
    blur_button.setStyleSheet("""
        border: 2px solid #000000;
        color: #000000;
        font-size: 35px;
        padding: 10px;
        border-radius: 15px;  /* Smooth rounded edges */
    """)
    blur_icon = QPixmap("../assets/images/eye.png")  # Path to the eye icon image
    blur_button.setIcon(blur_icon)
    blur_button.setIconSize(QSize(30, 30))  # Set the size of the icon next to the text
    blur_button.setText("Blur")
    button_layout.addWidget(blur_button)

    # Add the button layout to the sidebar
    sidebar_layout.addLayout(button_layout)

    return sidebar_layout
