from PySide2.QtCore import QTimer, QEventLoop
from PySide2.QtWidgets import QPushButton, QVBoxLayout, QWidget
from PySide2.QtGui import QIcon
import os
import cv2
import pickle
from facenet_pytorch import MTCNN
import torch


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
mtcnn = MTCNN(keep_all=True, device=device)


def detect_and_save_left_face(input_dir, output_dir):
    """
    Detect and save the face on the left side of the image with extra hair and neck coverage

    :param input_dir: Directory containing source images
    :param output_dir: Directory to save detected faces
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Face cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Get all image files in the input directory
    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

    if not image_files:
        print("No images found in the input directory.")
        return None

    # Process the most recent image (assuming the last file is the most recent)
    latest_image_path = os.path.join(input_dir, image_files[-1])

    try:
        # Read the image
        image = cv2.imread(latest_image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100),  # Minimum face size
            maxSize=(500, 500)  # Maximum face size
        )

        if len(faces) > 0:
            # Filter faces on the left side of the image
            left_faces = [face for face in faces if face[0] < image.shape[1] / 2]

            if not left_faces:
                print("No face detected on the left side of the image.")
                return None

            # Choose the leftmost face if multiple left-side faces are detected
            face = min(left_faces, key=lambda f: f[0])
            (x, y, w, h) = face

            # Expand the face region to include more hair and neck
            # Increase vertical padding significantly
            top_padding = int(h * 0.5)  # Add 50% more space above the face for hair
            bottom_padding = int(h * 0.3)  # Add 30% more space below the face for neck
            left_padding = int(w * 0.2)  # Add some side padding

            new_x = max(0, x - left_padding)
            new_y = max(0, y - top_padding)
            new_w = min(image.shape[1] - new_x, w + 2 * left_padding)
            new_h = min(image.shape[0] - new_y, h + top_padding + bottom_padding)

            # Crop the expanded face region
            expanded_face_img = image[new_y:new_y + new_h, new_x:new_x + new_w]

            # Generate output filename
            # Use a fixed output filename instead of dynamically changing based on the image name
            output_filename = os.path.join(output_dir, 'face_capture.png')

            # Save the expanded face image
            cv2.imwrite(output_filename, expanded_face_img)

            print(f"Left-side face with hair and neck detected and saved to {output_filename}")
            return output_filename
        else:
            print("No faces detected in the image.")
            return None

    except Exception as e:
        print(f"Error processing image: {e}")
        return None


def ControlSection(parent):
    widget = QWidget(parent)
    layout = QVBoxLayout()

    # Button with an icon (scanner.png) and text "Rescan"
    fetch_button = QPushButton("Scan", widget)
    fetch_button.setIcon(QIcon("../assets/images/scanner.png"))
    fetch_button.setFixedSize(120, 50)
    fetch_button.setIconSize(fetch_button.size() * 0.8)
    fetch_button.setStyleSheet("""
        border: 2px solid Black;
        padding: 5px;
        text-align: left;
        font-size: 18px;    
        padding-top: 15px;
        padding-bottom: 15px;
        border-radius: 10px;
        background-color: white;
        transition: background-color 0.3s ease; /* Smooth transition for animation */
    """)

    def set_button_color(button, color, duration_ms):
        """
        Change the button's background color temporarily and force the button to repaint.

        :param button: QPushButton instance
        :param color: Color to set (e.g., "red", "#ffcc00")
        :param duration_ms: Duration in milliseconds to keep the color before reverting
        """
        original_style = button.styleSheet()  # Save the original style
        button.setStyleSheet(f"""
            border: 2px solid Black;
            padding: 5px;
            text-align: left;
            font-size: 18px;    
            padding-top: 15px;
            padding-bottom: 15px;
            border-radius: 10px;
            background-color: {color};
            transition: background-color 0.3s ease;
        """)
        button.repaint()  # Force the button to repaint immediately

        # Revert the button's color after the specified duration
        QTimer.singleShot(duration_ms, lambda: restore_button_style(button, original_style))

    def restore_button_style(button, original_style):
        """
        Restore the button's original stylesheet.

        :param button: QPushButton instance
        :param original_style: The original stylesheet to restore
        """
        button.setStyleSheet(original_style)
        button.repaint()  # Force
    # Modified click handler to include left-side face detection, image reload, and animation
    def rescan_and_detect_left_face():
        """
        Handler for the Scan button click. Detects the left-side face in the image,
        saves it, computes the face encoding, and saves it in the encodefile.p.
        """
        # Indicate button click with color animation
        set_button_color(fetch_button, "#ffcc00", 300)  # Yellow highlight for 300ms

        # Call the parent's fetch_mdb_data method
        parent.fetch_mdb_data()

        # Detect and save the left-side face
        input_dir = r'C:\Users\Public\Documents\Plustek-SecureScan\Image'
        output_dir = '../capture'
        output_filename = detect_and_save_left_face(input_dir, output_dir)

        if output_filename:
            # Compute and save face encoding
            try:
                # Load the saved face image
                face_image = cv2.imread(output_filename)
                face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

                # Detect faces and get encodings using MTCNN
                boxes, _ = mtcnn.detect(face_rgb)
                if boxes is not None:
                    print(f"Faces detected: {len(boxes)}")
                    cropped_faces = [face_rgb[int(y1):int(y2), int(x1):int(x2)] for (x1, y1, x2, y2) in boxes]
                    print(f"Cropped faces count: {len(cropped_faces)}")
                    if cropped_faces:
                        print("Encoding face...")
                        encoding = mtcnn(cropped_faces[0])
                        print(f"Encoding generated: {encoding}")
                        encoding_file = os.path.join(output_dir, "encodefile.p")
                        with open(encoding_file, "wb") as f:
                            pickle.dump(encoding.cpu().numpy(), f)
                        print(f"Face encoding saved to {encoding_file}")

                        # Check if encoding file was created and is not empty
                        if os.path.exists(encoding_file) and os.path.getsize(encoding_file) > 0:
                            print("Encoding file created and is not empty.")
                        else:
                            print("Encoding file was not created or is empty.")
                    else:
                        print("No cropped faces available for encoding.")
                else:
                    print("No faces detected by MTCNN.")
            except Exception as e:
                print(f"Error during encoding: {e}")

            # Reload images in the parent after processing
            parent.reloadImages(output_filename, "")  # Reload with the captured face image
        else:
            # Clear details if no valid image is found
            parent.clear_details()

    fetch_button.clicked.connect(rescan_and_detect_left_face)
    layout.addWidget(fetch_button)
    widget.setLayout(layout)
    widget.setFixedHeight(70)

    return widget
