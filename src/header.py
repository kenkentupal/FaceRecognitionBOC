from PySide2.QtWidgets import QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide2.QtCore import Qt


def create_header(parent):
    """Creates the header layout."""
    header_layout = QHBoxLayout()

    # Create Header label (You can add a logo or title here)
    header_label = QLabel("Bureau of Customs - Intelligence Group", parent)
    header_label.setStyleSheet("color: black; font-size: 20px; font-weight: regular;")
    header_label.setAlignment(Qt.AlignCenter)
    header_label.setFixedHeight(20)  # Set fixed height for the header label
    header_layout.addWidget(header_label)

    # Add a spacer item to ensure that the header takes up exactly 20px height
    header_layout.addItem(QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Fixed))

    return header_layout
