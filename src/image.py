from PySide2.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QPixmap


class ImageSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(600)  # Set the fixed height of the ImageSection to 600
        self.layout = QVBoxLayout(self)

        # Create a horizontal layout for the two image containers
        self.image_layout = QHBoxLayout()

        # Create the first image container and get the label to update later
        self.container1, self.label1 = self.createImageContainer("", "../assets/images/id.png", "ID Image")
        # Create the second image container and get the label to update later
        self.container2, self.label2 = self.createImageContainer("", "../assets/images/camera.png", "Live Photo")

        # Add the containers to the horizontal layout
        self.image_layout.addWidget(self.container1)
        self.image_layout.addWidget(self.container2)

        # Add the image layout to the main layout
        self.layout.addLayout(self.image_layout)

        # Initial image load
        self.reloadImages("../capture/face_capture.png", "")

        # Timer that will reload images every second
        self.startImageReloadTimer()

    def createImageContainer(self, image_path, icon_path, text):
        container = QWidget(self)
        layout = QVBoxLayout(container)

        # Image with a black border
        label = QLabel(container)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("border: 2px solid black;")  # Set border color and size

        # Initially set a default empty pixmap
        label.setPixmap(QPixmap())

        # Icon for the image
        icon = QLabel(container)
        pixmap_icon = QPixmap(icon_path)  # Replace with actual icon path
        icon.setPixmap(pixmap_icon.scaled(30, 30, Qt.KeepAspectRatio))  # Adjust icon size
        icon.setAlignment(Qt.AlignLeft)

        # Text label for the image
        text_label = QLabel(text, container)  # Text to display beside the image
        text_label.setAlignment(Qt.AlignLeft)
        text_label.setWordWrap(True)  # Allow text to wrap within the label
        text_label.setMaximumHeight(20)  # Limit the height of the text label (adjust as needed)

        # Set font size via stylesheet
        text_label.setStyleSheet("font-size: 14px;")  # Change font size here (e.g., 14px)

        # Create a horizontal layout for the icon and text
        text_icon_layout = QHBoxLayout()
        text_icon_layout.addWidget(icon)
        text_icon_layout.addWidget(text_label)
        text_icon_layout.setAlignment(Qt.AlignLeft)

        # Add the icon + text layout and image to the container's main layout
        layout.addLayout(text_icon_layout)
        layout.addWidget(label)

        # Set the layout for the container widget
        container.setLayout(layout)

        return container, label

    def reloadImages(self, image1_path, image2_path):
        # Clear the current pixmap first
        self.label1.clear()
        self.label2.clear()

        # Load the new pixmaps and set them to the labels
        # Scaling the images to a larger size (e.g., 500x500)
        self.label1.setPixmap(QPixmap(image1_path).scaled(500, 500, Qt.KeepAspectRatio))
        self.label2.setPixmap(QPixmap(image2_path).scaled(500, 500, Qt.KeepAspectRatio))

        # Force widget update
        self.label1.update()
        self.label2.update()

        # Repaint the widget to force refresh
        self.repaint()  # Force the parent widget to refresh

    def startImageReloadTimer(self):
        # Make the timer a class-level variable to prevent it from being destroyed
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.reloadImages("../capture/face_capture.png", ""))
        self.timer.start(1000)  # 1-second interval
        print("Image reload timer started")


# Example of how to use this in a main application window
if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    window = ImageSection()
    window.showMaximized()

    sys.exit(app.exec_())
