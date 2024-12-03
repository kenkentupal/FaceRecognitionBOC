from PySide2.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide2.QtCore import Qt

class DetailsSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        # Main label to display details
        self.label = QLabel("Details Section", self)
        self.label.setStyleSheet("color: black; font-size: 18px;")
        self.label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        # Add a border around the widget with smooth edges
        self.setStyleSheet("""
            border: 2px solid #000000; 
            border-radius: 15px; 
            padding: 10px;
        """)  # Black border with rounded corners

    def update_details(self, details):
        # Update the label with new details if available
        if details:
            formatted_details = "\n".join(f"{key}: {value}" for key, value in details.items())
            self.label.setText(formatted_details)
        else:
            self.label.setText("No data found.")
