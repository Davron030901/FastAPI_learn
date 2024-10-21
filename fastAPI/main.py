import cv2
import numpy as np
import mediapipe as mp


class VirtualFittingRoom:
    def __init__(self):

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils

    def detect_body_landmarks(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)
        return results.pose_landmarks

    def calculate_body_measurements(self, landmarks):
        # Bu funksiyada tananing asosiy o'lchamlarini hisoblang
        # Masalan: yelka kengligini, ko'krak aylanasini, bel o'lchamini va h.k.
        # Bu yerda oddiy misol sifatida faqat yelka kengligini hisoblaymiz
        left_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        shoulder_width = np.sqrt((left_shoulder.x - right_shoulder.x) ** 2 + (left_shoulder.y - right_shoulder.y) ** 2)
        return {"shoulder_width": shoulder_width}

    def check_clothing_fit(self, measurements, clothing_size):
        # Bu funksiyada o'lchangan tana o'lchamlarini kiyim o'lchamlari bilan solishtiring
        # Va kiyimning mos kelish darajasini qaytaring
        # Bu yerda oddiy misol keltirilgan
        if measurements["shoulder_width"] * 100 < clothing_size["shoulder_width"]:
            return "Kiyim katta"
        elif measurements["shoulder_width"] * 100 > clothing_size["shoulder_width"]:
            return "Kiyim kichik"
        else:
            return "Kiyim mos keladi"

    def process_frame(self, frame, clothing_size):
        landmarks = self.detect_body_landmarks(frame)
        if landmarks:
            measurements = self.calculate_body_measurements(landmarks)
            fit_result = self.check_clothing_fit(measurements, clothing_size)

            # Natijalarni kadrga chizish
            self.mp_drawing.draw_landmarks(frame, landmarks, self.mp_pose.POSE_CONNECTIONS)
            cv2.putText(frame, f"Fit: {fit_result}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return frame


def main():
    cap = cv2.VideoCapture(0)
    fitting_room = VirtualFittingRoom()
    clothing_size = {"shoulder_width": 40}  # sm da

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = fitting_room.process_frame(frame, clothing_size)
        cv2.imshow('Virtual Fitting Room', frame)

        if cv2.waitKey(5) & 0xFF == 27:  # ESC tugmasi bosilganda chiqish
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()