import os
import pickle
import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, db, storage
import pygame
import multiprocessing
import time
from EncodeGenerator import generateEncodedData
from collections import defaultdict
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import multiprocessing

# Enable OpenCL acceleration for OpenCV
cv2.ocl.setUseOpenCL(True)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

mtcnn = MTCNN(keep_all=True, device=device)
facenet = InceptionResnetV1(pretrained='vggface2').eval().to(device)


def init_firebase():
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://facialrecognition-4bee2-default-rtdb.firebaseio.com/",
        'storageBucket': "facialrecognition-4bee2.appspot.com"
    })
    return storage.bucket()





def load_encoded_data():
    try:
        with open('scripts/EncodeFile.p', 'rb') as file:
            encode_list_known_with_ids = pickle.load(file)
        encode_list_known, user_ids = encode_list_known_with_ids
        return encode_list_known, user_ids
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        print(f"Error loading encoded data: {e}")
        return [], []

def preload_user_images(bucket, user_ids):
    user_images = defaultdict(lambda: None)
    for user_id in user_ids:
        for extension in ['png', 'jpg', 'jpeg']:
            blob = bucket.get_blob(f'Passport/{user_id}.{extension}')
            if blob:
                try:
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    img = cv2.imdecode(array, cv2.IMREAD_COLOR)
                    user_images[user_id] = img
                    break
                except Exception as e:
                    print(f"Error decoding image for user {user_id}: {e}")
    return user_images


def reload_encoded_data(queue):
    while True:
        time.sleep(10)
        encode_list_known, user_ids = load_encoded_data()
        generateEncodedData()
        try:
            if not queue.full():  # Check if queue is not full before putting new data
                queue.put((encode_list_known, user_ids))
        except Exception as e:
            print(f"Queue operation error: {e}")
        print("Encoded data reloaded")



def capture_frame(counter, mode_type, img, img_background, encode_list_known, user_ids, user_images):
    user_info = None
    img_user = None
    if counter == 0:
        # Crop the sides of the image
        img_height, img_width, _ = img.shape
        crop_width = img_width // 2
        start_x = (img_width - crop_width) // 2
        end_x = start_x + crop_width
        cropped_img = img[:, start_x:end_x]

        cv2.imwrite('captured_frame.jpg', cropped_img)
        img_s = cv2.imread("captured_frame.jpg")

        # Use MTCNN for face detection
        boxes, _ = mtcnn.detect(img_s)

        if boxes is None:
            return img_background, mode_type, user_info, img_user

        # Find the largest face
        largest_face_index = np.argmax([(right - left) * (bottom - top) for (left, top, right, bottom) in boxes])
        left, top, right, bottom = boxes[largest_face_index]
        face_img = img_s[int(top):int(bottom), int(left):int(right)]

        # Get face encoding using FaceNet
        face_tensor = torch.tensor(face_img).permute(2, 0, 1).unsqueeze(0).float().to(device)
        encode_face = facenet(face_tensor).detach().cpu().numpy().flatten()

        # Compare with known encodings
        face_dis = np.linalg.norm(encode_list_known - encode_face, axis=1)
        match_index = np.argmin(face_dis)

        if face_dis[match_index] < 0.40:  # Adjust threshold
            user_id = user_ids[match_index]
            img_user = user_images.get(user_id)
            if img_user is not None:
                try:
                    user_info = db.reference(f'ResultTable/{user_id}').get()
                except Exception as e:
                    print(f"Error fetching user info for {user_id}: {e}")
                    user_info = None
            img_user_resized = cv2.resize(img_user, (235, 235))
            img_background = cv2.imread('Resources/success.png')
            img_background[125:360, 895:1130] = img_user_resized
            mode_type = 2
            sound_effect = pygame.mixer.Sound('Resources/Sound/success.mp3')
            sound_effect.play()
        else:
            img_background = cv2.imread('Resources/tryagain.png')
            sound_effect = pygame.mixer.Sound('Resources/Sound/denied.mp3')
            sound_effect.play()
    return img_background, mode_type, user_info, img_user

def reload_encoded_data(queue):
    while True:
        time.sleep(10)
        encode_list_known, user_ids = load_encoded_data()
        generateEncodedData()
        try:
            if not queue.full():  # Check if queue is not full before putting new data
                queue.put((encode_list_known, user_ids))
        except PermissionError as e:
            print(f"PermissionError during queue operation: {e}")
        except Exception as e:
            print(f"Unexpected error during queue operation: {e}")
        print("Encoded data reloaded")

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
    cap.set(3, 640)
    cap.set(4, 360)

    pygame.mixer.init()

    bucket = init_firebase()

    img_background = cv2.imread('Resources/background2.png')
    trace = cv2.imread('Resources/bgfront.png', cv2.IMREAD_UNCHANGED)
    mode_type = 0

    encode_list_known, user_ids = load_encoded_data()

    folder_mode_path = 'Resources/Modes'
    mode_path_list = os.listdir(folder_mode_path)
    img_mode_list = [cv2.imread(os.path.join(folder_mode_path, path)) for path in mode_path_list]

    user_images = preload_user_images(bucket, user_ids)

    multiprocessing.set_start_method('spawn', force=True)  # Ensure proper process start method on Windows
    manager = multiprocessing.Manager()
    queue = manager.Queue(maxsize=1)  #
    reload_process = multiprocessing.Process(target=reload_encoded_data, args=(queue,))
    reload_process.daemon = True
    reload_process.start()

    counter = 4
    start_time = time.time()
    user_info = None
    img_user = None

    while True:
        success, img = cap.read()
        if not success:
            break

        try:
            if not queue.empty():
                encode_list_known, user_ids = queue.get_nowait()
        except queue.Empty:
            pass

        img_width, img_height = img.shape[1], img.shape[0]
        middle_x = img_width // 2
        roi_top = 0
        roi_bottom = img_height
        roi_left = middle_x - img_width // 4
        roi_right = middle_x + img_width // 4

        # Use MTCNN for face detection
        boxes, _ = mtcnn.detect(img[roi_top:roi_bottom, roi_left:roi_right])
        if boxes is not None and len(boxes) > 0:
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1:
                counter -= 1
                start_time = time.time()
                if counter == 3:
                    mode_type = 0
                    img_user = None
                    user_info = None

                    img_background = cv2.imread('Resources/wait3.png')
                elif counter == 2:
                    img_background = cv2.imread('Resources/wait2.png')
                elif counter == 1:
                    img_background = cv2.imread('Resources/wait1.png')
                elif counter == 0:
                    img_background, mode_type, user_info, img_user = capture_frame(counter, mode_type, img, img_background, encode_list_known, user_ids, user_images)

                if counter == -3:
                    counter = 4
        else:
            counter = 4
            img_background = cv2.imread('Resources/background2.png')
            start_time = time.time()

        bg_front_resized = cv2.resize(trace, (img.shape[1], img.shape[0]))
        alpha_mask_bg_front = bg_front_resized[:, :, 3] / 255.0
        alpha_inv_bg_front = 1.0 - alpha_mask_bg_front

        for c in range(0, 3):
            img[:, :, c] = (alpha_mask_bg_front * bg_front_resized[:, :, c] + alpha_inv_bg_front * img[:, :, c])

        img_background[162:522, 55:695] = img
        img_background[44:677, 808:1222] = img_mode_list[mode_type]

        if user_info and mode_type == 2:
            display_user_info(img_background, user_info)

        if img_user is not None:
            img_user_resized = cv2.resize(img_user, (235, 235))
            img_background[125:360, 895:1130] = img_user_resized

        cv2.imshow("Face Attendance", img_background)
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or cv2.getWindowProperty("Face Attendance", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
    reload_process.terminate()



def display_user_info(img_background, user_info):
    def draw_text(text, y_pos):
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
        offset = (414 - w) // 2
        cv2.putText(img_background, text, (808 + offset, y_pos), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1,
                    cv2.LINE_AA)

    draw_text(f"{user_info['First Name']} ", 423)
    draw_text(f"{user_info['Last Name']}", 467)
    draw_text(f"{user_info['Document Number']}", 508)
    draw_text(f"{user_info['Nationality']}", 552)

if __name__ == "__main__":
    main()
