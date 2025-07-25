import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
import os
import sys
import time
from threading import Thread

# Tambahan dari testing_webcam_external.py
class VideoStream:
    def __init__(self, src):
        self.stream = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        Thread(target=self.update, args=(), daemon=True).start()

    def update(self):
        while not self.stopped:
            if self.stream.isOpened():
                self.grabbed, self.frame = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

class SimpleDetector:
    def __init__(self, model_path="data/keras_model.h5", labels_path="data/labels.txt", confidence_threshold=0.8):
        self.model_path = model_path
        self.labels_path = labels_path
        self.confidence_threshold = confidence_threshold
        self.input_shape = (224, 224)
        self.class_names = []
        self.start_time = None
        self.detected = False

        self.load_model()
        self.load_labels()

    def load_model(self):
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file tidak ditemukan: {self.model_path}")

            print("🔄 Mencoba memuat model...")

            print("🔧 Mencoba perbaikan manual untuk parameter 'groups'...")

            import tensorflow.keras.layers as layers
            class FixedDepthwiseConv2D(layers.DepthwiseConv2D):
                def __init__(self, **kwargs):
                    kwargs.pop('groups', None)
                    super().__init__(**kwargs)

            custom_objects_fixed = {
                'DepthwiseConv2D': FixedDepthwiseConv2D
            }

            self.model = keras.models.load_model(
                self.model_path,
                compile=False,
                custom_objects=custom_objects_fixed
            )
            print(f"✅ Model berhasil dimuat: {self.model_path}")

            input_shape = self.model.input_shape
            if len(input_shape) >= 3:
                self.input_shape = (input_shape[1], input_shape[2])

            print(f"📐 Input shape: {self.input_shape}")
            print(f"🎯 Confidence threshold: {self.confidence_threshold:.0%}")

        except Exception as e:
            print(f"❌ Error loading model: {e}")
            sys.exit(1)

    def load_labels(self):
        try:
            if not os.path.exists(self.labels_path):
                raise FileNotFoundError(f"Labels file tidak ditemukan: {self.labels_path}")

            with open(self.labels_path, "r", encoding="utf-8") as f:
                self.class_names = [line.strip() for line in f.readlines()]

            print(f"✅ Labels berhasil dimuat: {len(self.class_names)} kelas")
        except Exception as e:
            print(f"❌ Error loading labels: {e}")
            sys.exit(1)

    def preprocess(self, frame):
        resized = cv2.resize(frame, self.input_shape)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = rgb.astype(np.float32) / 255.0
        return np.expand_dims(normalized, axis=0)

    def predict(self, frame):
        processed = self.preprocess(frame)
        predictions = self.model.predict(processed, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = predictions[0][class_idx]
        return self.class_names[class_idx], confidence
    
    def stable_detect(self, frame, now):
        label, conf = self.predict(frame)

        if conf >= self.confidence_threshold:
            if not hasattr(self, 'start_time') or self.start_time is None:
                self.start_time = now
            elif not hasattr(self, 'detected') or not self.detected:
                if now - self.start_time >= 1.0:
                    self.detected = True
                    return label, conf, True  # Deteksi stabil
        else:
            self.start_time = None
            self.detected = False

        return label, conf, False

    def run(self, camera_index="rtsp://192.168.100.10:8554/mystream"):
        vs = VideoStream(camera_index)

        print("🎥 Deteksi dimulai. Tekan 'q' untuk keluar.")
        start_time = None
        detected = False

        while True:
            frame = vs.read()
            if frame is None:
                continue

            label, conf = self.predict(frame)
            now = time.time()

            if conf >= self.confidence_threshold:
                if start_time is None:
                    start_time = now
                elif not detected and (now - start_time) >= 1.0:
                    print(f"✅ Ikan terdeteksi: {label} ({conf:.1%})")
                    detected = True
            else:
                start_time = None
                detected = False

            # Tampilan
            if conf >= self.confidence_threshold:
                text = f"{label}: {conf:.1%}"
                cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "🔍 Mencari objek...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)

            cv2.imshow("Deteksi Realtime", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        vs.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    if not os.path.exists("data/keras_model.h5") or not os.path.exists("data/labels.txt"):
        print("❌ File model atau label tidak ditemukan.")
    else:
        detector = SimpleDetector("data/keras_model.h5", "data/labels.txt")
        detector.run()