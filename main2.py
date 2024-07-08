import os
import pickle
import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, db, storage
import face_recognition
import pygame
import multiprocessing
import time
from EncodeGenerator import generateEncodedData
from collections import defaultdict

# Enable OpenCL acceleration for OpenCV
cv2.ocl.setUseOpenCL(True)


def init_firebase():
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://facialrecognition-4bee2-default-rtdb.firebaseio.com/",
        'storageBucket': "facialrecognition-4bee2.appspot.com"
    })
    return storage.bucket()


def load_encoded_data():
    try:
        #print("Loading Encoded File...")
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
        queue.put((encode_list_known, user_ids))
        #print("Encoded data reloaded")


def capture_frame(counter, mode_type, img, img_background, encode_list_known, user_ids, user_images):
    user_info = None
    img_user = None
    if counter == 0:
        # Crop the sides of the image, keeping the top and bottom portions intact
        img_height, img_width, _ = img.shape
        crop_width = img_width // 2
        start_x = (img_width - crop_width) // 2
        end_x = start_x + crop_width
        cropped_img = img[:, start_x:end_x]

        cv2.imwrite('captured_frame.jpg', cropped_img)
        img_s = cv2.imread("captured_frame.jpg")
        face_cur_frame = face_recognition.face_locations(img_s)
        encode_cur_frame = face_recognition.face_encodings(img_s, face_cur_frame)

        # Find the largest face
        largest_face_index = None
        largest_face_size = 0
        for index, (top, right, bottom, left) in enumerate(face_cur_frame):
            face_size = (right - left) * (bottom - top)
            if face_size > largest_face_size:
                largest_face_size = face_size
                largest_face_index = index

        if largest_face_index is not None:
            encode_face = encode_cur_frame[largest_face_index]
            matches = face_recognition.compare_faces(encode_list_known, encode_face)
            face_dis = face_recognition.face_distance(encode_list_known, encode_face)
            match_index = np.argmin(face_dis)

            if matches[match_index] and face_dis[match_index] < 0.50:
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


def main():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 60)
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

    queue = multiprocessing.Queue()
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

        if not queue.empty():
            encode_list_known, user_ids = queue.get()

        img_width, img_height = img.shape[1], img.shape[0]
        middle_x = img_width // 2
        roi_top = 0
        roi_bottom = img_height
        roi_left = middle_x - img_width // 4
        roi_right = middle_x + img_width // 4

        face_locations = face_recognition.face_locations(img[roi_top:roi_bottom, roi_left:roi_right])
        face_locations = [(top + roi_top, right + roi_left, bottom + roi_top, left + roi_left) for
                          (top, right, bottom, left) in face_locations]

        if face_locations:
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
                    img_background, mode_type, user_info, img_user = capture_frame(counter, mode_type, img,
                                                                                   img_background, encode_list_known,
                                                                                   user_ids, user_images)

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
