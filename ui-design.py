import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import os
import json
import time
from computer_vision import SimpleDetector

class App(ctk.CTk):
    def load_settings(self):
        self.settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        if os.path.exists(self.settings_path):
            with open(self.settings_path, "r") as f:
                try:
                    self.settings_data = json.load(f)
                except Exception:
                    self.settings_data = {}
        else:
            self.settings_data = {}

    def save_settings(self):
        with open(self.settings_path, "w") as f:
            json.dump(self.settings_data, f, indent=2)
            
    def ensure_box_manager_structure(self):
        box_data = self.json_data.get("box_manager")
        if not isinstance(box_data, dict):
            # fallback only if rusak total
            box_data = {
                "A1": "0", "A2": "0", "A3": "0",
                "B1": "0", "B2": "0", "B3": "0",
                "C1": "0", "C2": "0", "C3": "0"
            }
        else:
            # pastikan semua key ada
            for key in ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]:
                if key not in box_data:
                    box_data[key] = "0"
                elif not isinstance(box_data[key], str):
                    box_data[key] = str(box_data[key])
        self.json_data["box_manager"] = box_data

    def center_window(self, window):
        window.update_idletasks()
        w = window.winfo_width()
        h = window.winfo_height()
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        window.geometry(f"{w}x{h}+{x}+{y}")

    def __init__(self):
        super().__init__()

        self.load_settings()

        # -- Konfigurasi Jendela Utama --
        self.title("Fish Sorting UI")
        # self.geometry("1400x800")
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda event: self.attributes("-fullscreen", False))
        self.configure(fg_color="#f3f4f6")
        self.settings_window = None
        self.timer_label = None # Inisialisasi timer label
        self.system_running = False
        self.computer_vision = SimpleDetector("data/keras_model.h5", "data/labels.txt", confidence_threshold=0.8)

        # Grid utama
        self.grid_columnconfigure(0, weight=2, uniform="a")
        self.grid_columnconfigure(1, weight=2, uniform="a")
        self.grid_columnconfigure(2, weight=1)  # Log Activity column narrower
        self.grid_rowconfigure(0, weight=3, uniform="a")
        self.grid_rowconfigure(1, weight=2, uniform="a")

        # Section
        self.create_camera_capture_frame()
        self.create_info_widgets()
        self.create_box_manager_frame()
        self.create_velocity_manager_frame()
        self.create_log_activity_frame()
        self.synchronize_section_heights()

    def synchronize_section_heights(self):
        self.update_idletasks()
        # Get frames
        cam = self.camera_frame
        info = getattr(self, 'info_frame', None)
        box = getattr(self, 'box_frame', None)
        accel = getattr(self, 'accel_frame', None)
        # Synchronize heights
        if cam and box:
            max_top = max(cam.winfo_height(), box.winfo_height())
            cam.configure(height=max_top)
            box.configure(height=max_top)
        if info and accel:
            max_bottom = max(info.winfo_height(), accel.winfo_height())
            info.configure(height=max_bottom)
            accel.configure(height=max_bottom)

    def create_camera_capture_frame(self):
        # Frame utama Camera Capture
        self.camera_frame = ctk.CTkFrame(self, fg_color="#2563eb", corner_radius=16)
        self.camera_frame.grid(row=0, column=0, sticky="nsew", padx=(30,10), pady=(30,5))
        self.camera_frame.grid_columnconfigure(0, weight=1)
        self.camera_frame.grid_rowconfigure(1, weight=1)

        # Judul
        ctk.CTkLabel(self.camera_frame, text="Camera Capture", font=ctk.CTkFont(size=24, weight="bold"), text_color="white").grid(row=0, column=0, sticky="nw", padx=25, pady=(25,10))

        # Frame konten
        self.cam_content = ctk.CTkFrame(self.camera_frame, fg_color="white", corner_radius=15)
        self.cam_content.grid(row=1, column=0, sticky="nsew", padx=25, pady=(0,25))
        self.cam_content.grid_columnconfigure(0, weight=1)
        self.cam_content.grid_rowconfigure(0, weight=3) # Area Webcam
        self.cam_content.grid_rowconfigure(1, weight=1) # Area Info

        self.webcam_label = ctk.CTkLabel(self.cam_content, text="")
        self.webcam_label.grid(row=0, column=0, padx=20, pady=(20,10), sticky="nsew")
        self.cap = cv2.VideoCapture(0)
        self.update_webcam()

        # Frame info objek dan waktu
        info_frame = ctk.CTkFrame(self.cam_content, fg_color="#e0e7ff", corner_radius=10)
        info_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        info_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Jenis Objek
        jenis_frame = ctk.CTkFrame(info_frame, fg_color="#e0e7ff")
        jenis_frame.grid(row=0, column=0, sticky="w", padx=10, pady=20)
        ctk.CTkLabel(jenis_frame, text="Jenis Objek", font=ctk.CTkFont(size=13), text_color="#222").pack(anchor="w")
        ctk.CTkLabel(jenis_frame, text="Tuna", font=ctk.CTkFont(size=15, weight="bold"), text_color="#222").pack(anchor="w")
        
        # Berat Objek
        berat_frame = ctk.CTkFrame(info_frame, fg_color="#e0e7ff")
        berat_frame.grid(row=0, column=1, sticky="w", padx=10, pady=20)
        ctk.CTkLabel(berat_frame, text="Berat Objek", font=ctk.CTkFont(size=13), text_color="#222").pack(anchor="w")
        ctk.CTkLabel(berat_frame, text="0.9 Kg", font=ctk.CTkFont(size=15, weight="bold"), text_color="#222").pack(anchor="w")
        
        # Waktu
        waktu_frame = ctk.CTkFrame(info_frame, fg_color="#e0e7ff")
        waktu_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        self.timer_label = ctk.CTkLabel(waktu_frame, text="00:00:00", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2563eb")
        self.timer_label.pack(anchor="e")

    def update_webcam(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        now = time.time()
        # label, conf, is_detected = self.predict(frame, now)
        label, conf, is_detected = self.computer_vision.stable_detect(frame, now)

        if is_detected:
            print(f"✅ Ikan terdeteksi: {label} ({conf:.1%})")

        # Tampilkan ke UI
        if conf >= self.computer_vision.confidence_threshold:
            cv2.putText(frame, f"{label}: {conf:.1%}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "🔍 Mencari objek...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (150, 150, 150), 2)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((640, 400))
        imgtk = ImageTk.PhotoImage(image=img)

        self.webcam_label.imgtk = imgtk
        self.webcam_label.configure(image=imgtk)

        self.after(17, self.update_webcam)

    # Informasi pada objek terdeteksi
    def create_info_widgets(self):
        self.info_frame = ctk.CTkFrame(self, fg_color="#f3f4f6")
        self.info_frame.grid(row=1, column=0, sticky="nsew", padx=(30,5), pady=(5,30))
        self.info_frame.grid_columnconfigure((0,1), weight=1)
        self.info_frame.grid_rowconfigure((0,1), weight=1)

        self.info_data_labels = []
        info_descs = [
            "Jumlah Pcs Tersortir",
            "Jumlah Kg Tersortir",
            "Jumlah Pcs / jam",
            "Jumlah Kg / jam",
        ]
        for i, desc in enumerate(info_descs):
            box = ctk.CTkFrame(self.info_frame, fg_color="#e0e7ff", corner_radius=15)
            box.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")
            box.grid_rowconfigure(0, weight=1)
            box.grid_rowconfigure(1, weight=1)
            box.grid_columnconfigure(0, weight=1)
            val_label = ctk.CTkLabel(box, text="0", font=ctk.CTkFont(size=28, weight="bold"), text_color="#2563eb")
            val_label.grid(row=0, column=0, pady=(15,5), sticky="nsew")
            ctk.CTkLabel(box, text=desc, font=ctk.CTkFont(size=14), text_color="#222").grid(row=1, column=0, pady=(0,15), sticky="nsew")
            self.info_data_labels.append(val_label)

    def show_box_alert(self, row, col):
        box_name = chr(65+col) + str(row+1)
        msg = f"Ambil box ikan di posisi {box_name}?"
        alert = ctk.CTkToplevel(self)
        alert.title("Konfirmasi Pengambilan Box")
        alert.geometry("350x150")
        alert.transient(self)
        alert.grab_set()
        ctk.CTkLabel(alert, text=msg, font=ctk.CTkFont(size=16, weight="bold"), text_color="#2563eb").pack(pady=20)
        btn_frame = ctk.CTkFrame(alert, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Ya, Reset Box", fg_color="#4ade80", hover_color="#22c55e", font=ctk.CTkFont(size=15, weight="bold"), command=lambda: self.reset_box_value(row, col, alert)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Batal", fg_color="#ef4444", hover_color="#b50000", font=ctk.CTkFont(size=15, weight="bold"), command=alert.destroy).pack(side="left", padx=10)
        self.center_window(alert)

    def show_trash_alert(self):
        alert = ctk.CTkToplevel(self)
        alert.title("Konfirmasi Pengambilan Box Sampah")
        alert.geometry("350x150")
        alert.transient(self)
        alert.grab_set()
        ctk.CTkLabel(alert, text="Ambil box sampah?", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ef4444").pack(pady=20)
        btn_frame = ctk.CTkFrame(alert, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Ya, Ambil", fg_color="#ef4444", hover_color="#b50000", font=ctk.CTkFont(size=15, weight="bold"), command=lambda: self.reset_trash_value(alert)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Batal", fg_color="#2563eb", hover_color="#0037ac", font=ctk.CTkFont(size=15, weight="bold"), command=alert.destroy).pack(side="left", padx=10)
        self.center_window(alert)

    # Box Manager
    def create_box_manager_frame(self):
        self.box_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=20)
        self.box_frame.grid(row=0, column=1, sticky="nsew", padx=(10,10), pady=(30,5))
        self.box_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        ctk.CTkLabel(self.box_frame, text="Box Manager", font=ctk.CTkFont(size=22, weight="bold"), text_color="#2563eb").grid(row=0, column=0, columnspan=5, sticky="nw", padx=25, pady=(25,10))

        ctk.CTkLabel(self.box_frame, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2563eb").grid(row=1, column=0, pady=(0,5))
        for i, h in enumerate(["A","B","C"]):
            ctk.CTkLabel(self.box_frame, text=h, font=ctk.CTkFont(size=16, weight="bold"), text_color="#2563eb").grid(row=1, column=i+1, pady=(0,5))

        box_size = 80
        self.box_btns = []
        for r in range(3):
            row_btns = []
            ctk.CTkLabel(self.box_frame, text=str(r+1), font=ctk.CTkFont(size=16, weight="bold"), text_color="#2563eb").grid(row=r+2, column=0, padx=(15,5), pady=15, sticky="nsew")
            for c in range(3):
                btn = ctk.CTkButton(self.box_frame, text="0 Kg", width=box_size, height=box_size, corner_radius=10, fg_color="#e0e7ff", text_color="#222", hover_color="#7eb5fc", font=ctk.CTkFont(size=16, weight="bold"), command=lambda r=r, c=c: self.show_box_alert(r, c))
                btn.grid(row=r+2, column=c+1, padx=10, pady=10, sticky="nsew")
                row_btns.append(btn)
            self.box_btns.append(row_btns)

        # Tombol Trash
        self.trash_btn = ctk.CTkButton(self.box_frame, text="TRASH\n0 Kg", corner_radius=10, fg_color="#ef4444", text_color="white", hover_color="#bc1616", font=ctk.CTkFont(size=16, weight="bold"), command=self.show_trash_alert)
        self.trash_btn.grid(row=2, column=4, rowspan=3, padx=(20,10), pady=10, sticky="nsew")

    # Velocity Manager
    def create_velocity_manager_frame(self):
        self.accel_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=20)
        self.accel_frame.grid(row=1, column=1, sticky="nsew", padx=(10,10), pady=(5,30))
        self.accel_frame.grid_columnconfigure(1, weight=1)
        self.accel_frame.grid_columnconfigure(2, weight=0)
        
        ctk.CTkLabel(self.accel_frame, text="Velocity Manager", font=ctk.CTkFont(size=22, weight="bold"), text_color="#2563eb").grid(row=0, column=0, columnspan=3, sticky="nw", padx=25, pady=(25,10))
        self.conveyor_sliders = []
        self.conveyor_value_labels = []

        conveyor_values = self.settings_data.get("conveyor", {
            "conveyor_1": 0, "conveyor_2": 0, "conveyor_3": 0, "conveyor_4": 0, "conveyor_5": 0
        })
       
        num_sliders = 5
        for i in range(num_sliders):
            ctk.CTkLabel(self.accel_frame, text=f"Conveyor {i+1}", font=ctk.CTkFont(size=16), text_color="#222").grid(row=i+1, column=0, padx=25, pady=5, sticky="w")
            slider = ctk.CTkSlider(self.accel_frame, from_=0, to=20, number_of_steps=20, progress_color="#2563eb", width=220)
            key = f"conveyor_{i+1}"
            val = conveyor_values.get(key, 0)
          
            val = max(0, min(20, val))
            slider.set(val)
            slider.grid(row=i+1, column=1, padx=(25,10), pady=5, sticky="ew")
            
            value_label = ctk.CTkLabel(self.accel_frame, text=str(int(slider.get())), font=ctk.CTkFont(size=15, weight="bold"), width=32)
            value_label.grid(row=i+1, column=2, padx=(0,20), pady=5, sticky="w")
            
            self.conveyor_sliders.append(slider)
            self.conveyor_value_labels.append(value_label)
            
            def make_callback(idx, label, key=key):
                return lambda value: self.on_conveyor_slider_change_named(key, value, label)
            slider.configure(command=make_callback(i, value_label))
        
        self.accel_frame.grid_rowconfigure(num_sliders + 1, weight=1)

    def on_conveyor_slider_change_named(self, key, value, label=None):
        if "conveyor" not in self.settings_data or not isinstance(self.settings_data["conveyor"], dict):
            self.settings_data["conveyor"] = {}
        v = int(round(value))
        v = max(0, min(20, v))
        
        self.settings_data["conveyor"][key] = v
        if label is not None:
            label.configure(text=str(v))
        self.save_settings()

    def create_log_activity_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(5,30), pady=(30,30))
        frame.grid_rowconfigure(0, weight=10)
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_columnconfigure(0, weight=1)

        # Log Activity
        log_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=20, width=180)
        log_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0,15))
        log_frame.grid_rowconfigure(0, weight=0)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_frame, text="Log Activity", font=ctk.CTkFont(size=22, weight="bold"), text_color="#2563eb").grid(row=0, column=0, padx=10, pady=(20,8), sticky="nw")
        self.log_textbox = ctk.CTkTextbox(log_frame, corner_radius=10, fg_color="#e0e7ff", border_width=0, font=ctk.CTkFont(size=14), width=160)
        self.log_textbox.insert("1.0", "")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0,0), sticky="nsew")

        # Tombol kontrol
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="sew")
        btn_frame.grid_columnconfigure((0,1), weight=1)
        btn_frame.grid_rowconfigure((0,1,2,3), weight=1)
        # Start & Stop
        self.start_btn = ctk.CTkButton(btn_frame, text="START", text_color="#000000", corner_radius=10, fg_color="#4ade80", hover_color="#22c55e", font=ctk.CTkFont(size=18, weight="bold"), command=self.start_system)
        self.stop_btn = ctk.CTkButton(btn_frame, text="STOP", text_color="#000000", corner_radius=10, fg_color="#facc15", hover_color="#eab308", font=ctk.CTkFont(size=18, weight="bold"), command=self.stop_system)
        self.start_btn.grid(row=0, column=0, padx=(10,5), pady=(7,3), sticky="ew", ipady=10)
        self.stop_btn.grid(row=0, column=1, padx=(5,10), pady=(7,3), sticky="ew", ipady=10)


        reset_btn = ctk.CTkButton(btn_frame, text="RESET", text_color="#000000", corner_radius=10, fg_color="#f87171", hover_color="#ef4444", font=ctk.CTkFont(size=18, weight="bold"), command=self.confirm_system_reset)
        reset_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=(3,3), sticky="ew", ipady=10)

        try:
            settings_icon_data = Image.open("settings_icon.png")
            settings_icon = ctk.CTkImage(light_image=settings_icon_data, size=(20,20))
            settings_btn = ctk.CTkButton(btn_frame, text=" SETTINGS", image=settings_icon, compound="left", corner_radius=10, fg_color="#BDC3C7", text_color="black", hover_color="#AAB1B5", font=ctk.CTkFont(size=16, weight="bold"), command=self.open_settings_window)
        except FileNotFoundError:
            settings_btn = ctk.CTkButton(btn_frame, text="SETTINGS", corner_radius=10, fg_color="#BDC3C7", text_color="black", hover_color="#AAB1B5", font=ctk.CTkFont(size=16, weight="bold"), command=self.open_settings_window)
        settings_btn.grid(row=2, column=0, columnspan=2, padx=10, pady=(3,5), sticky="ew", ipady=10)



# ------------------------------------ SYSTEM LOGIC -----------------------------------------------------------------------------------------------------------------------------------------------------------------



    def start_system(self):
        if self.system_running:
            return

        self.system_running = True
        
        if not hasattr(self, 'timer_seconds'):
            self.timer_seconds = 0
        self.update_timer()
        self.load_json_data()
        self.update_all_sections()
        self.log_activity("Sistem dimulai.")

    def stop_system(self):
        self.system_running = False
        if hasattr(self, 'timer_job'):
            self.after_cancel(self.timer_job)
        self.log_activity("Sistem dihentikan.")

    def reset_system(self):
        self.system_running = False
        if hasattr(self, 'timer_job'):
            self.after_cancel(self.timer_job)
        self.timer_seconds = 0
        
        if self.timer_label:
            self.timer_label.configure(text=self.format_time(self.timer_seconds))
            
        self.reset_data()
        self.update_all_sections()
        self.log_activity("Sistem direset.")

    def update_timer(self):
        if not hasattr(self, 'timer_seconds'):
            self.timer_seconds = 0
        if self.system_running:
            self.timer_seconds += 1

            # Update waktu_frame
            if self.timer_label:
                self.timer_label.configure(text=self.format_time(self.timer_seconds))
            self.timer_job = self.after(1000, self.update_timer)

    def format_time(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02}"

    def load_json_data(self):
        json_path = os.path.join(os.path.dirname(__file__), "data.json")
        print("Memuat dari:", json_path)
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"File data.json tidak ditemukan di: {json_path}")

        with open(json_path, "r") as f:
            try:
                self.json_data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Gagal memuat data.json: {e}")

    def reset_data(self):
        self.json_data = {
            "info_data": {
                "pcs_sorted": "0", "kg_sorted": "0", "pcs_per_hour": "0", "kg_per_hour": "0"
            },
            "box_manager": {
                "A1": "0", "A2": "0", "A3": "0",
                "B1": "0", "B2": "0", "B3": "0",
                "C1": "0", "C2": "0", "C3": "0"
            },
            "trash": "0",
            "log_activity": []
        }

        json_path = os.path.join(os.path.dirname(__file__), "data.json")
        with open(json_path, "w") as f:
            json.dump(self.json_data, f, indent=4)

        # Kosongkan log di UI
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def update_all_sections(self):
        self.ensure_box_manager_structure()
        info_data = self.json_data.get("info_data", {})
        info_keys = ["pcs_sorted", "kg_sorted", "pcs_per_hour", "kg_per_hour"]
        for i, key in enumerate(info_keys):
            val = info_data.get(key, "0")
            self.info_data_labels[i].configure(text=val)

        box_data = self.json_data.get("box_manager", {})
        if isinstance(box_data, list):
            raise TypeError("box_manager harus berupa dictionary, bukan list. Cek file data.json!")
        box_keys = [
            ["A1", "B1", "C1"],
            ["A2", "B2", "C2"],
            ["A3", "B3", "C3"]
        ]
        for r in range(3):
            for c in range(3):
                key = f"{chr(65+c)}{r+1}"
                value = box_data.get(key, "0")
                self.box_btns[r][c].configure(text=f"{value} Kg")


        self.trash_btn.configure(text=f"TRASH\n{self.json_data.get('trash', '0')} Kg")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        for entry in self.json_data.get("log_activity", []):
            self.log_textbox.insert("end", entry+"\n")
        self.log_textbox.configure(state="disabled")

    def log_activity(self, msg):
        import datetime
        now = datetime.datetime.now().strftime("[%H:%M:%S|%d/%m]")
        entry = f"{now} {msg}"
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", entry+"\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def confirm_system_reset(self):
        alert = ctk.CTkToplevel(self)
        alert.title("Konfirmasi Reset Sistem")
        alert.geometry("350x150")
        alert.transient(self)
        alert.grab_set()
        ctk.CTkLabel(alert, text="Apakah Anda yakin ingin mereset mesin?", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        btn_frame = ctk.CTkFrame(alert, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Ya, Reset", fg_color="#ef4444", hover_color="#b50000", font=ctk.CTkFont(size=15, weight="bold"), command=lambda: self.reset_system_with_popup(alert)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Batal", fg_color="#2563eb", hover_color="#0037ac", font=ctk.CTkFont(size=15, weight="bold"), command=alert.destroy).pack(side="left", padx=10)
        self.center_window(alert)

    def reset_system_with_popup(self, alert_window):
        self.reset_system()
        if alert_window:
            alert_window.destroy()

    def reset_box_value(self, row, col, alert_window):
        key = f"{chr(65 + col)}{row + 1}"
        self.json_data['box_manager'][key] = "0"
        self.update_all_sections()
        self.log_activity(f"Box {key} direset.")
        if alert_window:
            alert_window.destroy()

    def reset_trash_value(self, alert_window):
        self.json_data['trash'] = "0"
        self.update_all_sections()
        self.log_activity("Box sampah direset.")
        if alert_window:
            alert_window.destroy()

    def open_settings_window(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.focus()
            return

        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title("Settings")
        self.settings_window.geometry("700x500")
        self.settings_window.configure(fg_color="#e5e7eb")
        self.settings_window.resizable(False, True)
        self.settings_window.transient(self)
        self.settings_window.grab_set()
        self.settings_window.protocol("WM_DELETE_WINDOW", self.on_settings_close)
        self.center_window(self.settings_window)
        self.settings_window.grid_columnconfigure(0, weight=1)
        self.settings_window.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkScrollableFrame(self.settings_window, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10,0))
        main_frame.grid_columnconfigure(0, weight=1)

        # 1. Camera Settings
        cam_frame = ctk.CTkFrame(main_frame, fg_color="white", border_width=1, border_color="#d1d5db", corner_radius=10)
        cam_frame.grid(row=0, column=0, sticky="new", padx=10, pady=10)
        cam_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(cam_frame, text="Camera Settings", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))
        
        def create_slider_row(parent, label_text, row, key):
            ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=14)).grid(row=row, column=0, sticky="w", padx=(20, 10))
            slider = ctk.CTkSlider(parent, from_=-100, to=100, number_of_steps=200, progress_color="#60a5fa", button_color="#2563eb", button_hover_color="#1d4ed8")
            # Load value from settings
            cam_settings = self.settings_data.get("camera", {})
            slider.set(cam_settings.get(key, 0))
            slider.grid(row=row, column=1, sticky="ew", padx=10, pady=10)
            value_label = ctk.CTkLabel(parent, text=str(int(slider.get())), width=60, font=ctk.CTkFont(size=14, weight="bold"))
            value_label.grid(row=row, column=2, sticky="e", padx=(10, 20))
            def update_label_and_save(value):
                value_label.configure(text=f"{int(value)}")
                if "camera" not in self.settings_data:
                    self.settings_data["camera"] = {}
                self.settings_data["camera"][key] = int(value)
                self.save_settings()
            slider.configure(command=update_label_and_save)

        slider_labels = [
            ("Brightness", "brightness"),
            ("Exposure", "exposure"),
            ("Contrast", "contrast"),
            ("Gain", "gain"),
            ("Hue", "hue")
        ]
        for i, (label, key) in enumerate(slider_labels):
            create_slider_row(cam_frame, label, i + 1, key)

        def on_auto_checkbox_change():
            if "camera" not in self.settings_data:
                self.settings_data["camera"] = {}
            self.settings_data["camera"]["auto"] = bool(auto_var.get())
            self.save_settings()

        auto_var = ctk.IntVar(value=1 if self.settings_data.get("camera", {}).get("auto", False) else 0)
        auto_checkbox = ctk.CTkCheckBox(cam_frame, text="Auto", variable=auto_var, command=on_auto_checkbox_change)
        auto_checkbox.grid(row=len(slider_labels) + 1, column=2, sticky="e", padx=20, pady=10)

        # 2. Range Settings
        range_frame = ctk.CTkFrame(main_frame, fg_color="white", border_width=1, border_color="#d1d5db", corner_radius=10)
        range_frame.grid(row=2, column=0, sticky="new", padx=10, pady=10)
        range_frame.grid_columnconfigure([0,1,2,3], weight=1)
        ctk.CTkLabel(range_frame, text="Koordinat Penempatan", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(15, 10))
        
        self.range_entries = {}
        def create_range_input(parent, label, row, col):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.grid(row=row, column=col, padx=10, pady=5)
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 5))
            entry_x = ctk.CTkEntry(frame, width=50)
            entry_x.pack(side="left")
            ctk.CTkLabel(frame, text="x").pack(side="left", padx=3)
            entry_y = ctk.CTkEntry(frame, width=50)
            entry_y.pack(side="left")
            ctk.CTkLabel(frame, text="y").pack(side="left", padx=3)
            self.range_entries[label] = (entry_x, entry_y)

        range_settings = self.settings_data.get("range", {})
        range_cols = ["A", "B", "C"]
        for c, col_label in enumerate(range_cols):
            for r in range(3):
                key = f"{col_label}{r+1}"
                create_range_input(range_frame, key, r+1, c)
        create_range_input(range_frame, "TRASH", 1, 3) 

        for key, (entry_x, entry_y) in self.range_entries.items():
            val = range_settings.get(key, ["", ""])
            if isinstance(val, (list, tuple)) and len(val) == 2:
                entry_x.delete(0, 'end')
                entry_x.insert(0, str(val[0]))
                entry_y.delete(0, 'end')
                entry_y.insert(0, str(val[1]))
            else:
                entry_x.delete(0, 'end')
                entry_y.delete(0, 'end')

        def save_range_settings():
            if "range" not in self.settings_data:
                self.settings_data["range"] = {}
            for key, (entry_x, entry_y) in self.range_entries.items():
                x_val = entry_x.get()
                y_val = entry_y.get()
                self.settings_data["range"][key] = [x_val, y_val]
            self.save_settings()

        ctk.CTkButton(range_frame, text="Save", width=80, fg_color="#22c55e", hover_color="#16a34a", command=save_range_settings).grid(row=4, column=3, sticky="e", padx=10, pady=(5,15))
        button_bar = ctk.CTkFrame(self.settings_window, fg_color="transparent")
        button_bar.grid(row=1, column=0, sticky="sew", padx=20, pady=(10,15))
        button_bar.grid_columnconfigure(0, weight=1)
        btn_container = ctk.CTkFrame(button_bar, fg_color="transparent")
        btn_container.pack(side="right")

        ctk.CTkButton(btn_container, text="Cancel", command=self.on_settings_close, width=120, height=35, fg_color="#ef4444", hover_color="#dc2626", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

        # 3. Database Settings
        db_frame = ctk.CTkFrame(main_frame, fg_color="white", border_width=1, border_color="#d1d5db", corner_radius=10)
        db_frame.grid(row=1, column=0, sticky="new", padx=10, pady=10)
        db_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(db_frame, text="Database Settings", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))
        
        db_entries = {"Database Host": "localhost", "Database Name": "", "Username": "", "Password": "", "Port": ""}
        for i, (label, placeholder) in enumerate(db_entries.items()):
            ctk.CTkLabel(db_frame, text=label, font=ctk.CTkFont(size=14)).grid(row=i+1, column=0, sticky="w", padx=20, pady=8)
            show_char = "*" if label == "Password" else ""
            entry = ctk.CTkEntry(db_frame, placeholder_text=placeholder, show=show_char)
            entry.grid(row=i+1, column=1, sticky="ew", padx=20, pady=8)
        ctk.CTkButton(db_frame, text="Save", width=80, fg_color="#22c55e", hover_color="#16a34a").grid(row=len(db_entries)+1, column=1, sticky="e", padx=20, pady=(5,15))

        

        def on_apply_clicked():
            save_range_settings()
            self.on_settings_close()

        ctk.CTkButton(btn_container, text="Apply", width=120, height=35, fg_color="#22c55e", hover_color="#16a34a", font=ctk.CTkFont(weight="bold"), command=on_apply_clicked).pack(side="left", padx=(5,0))

    def on_settings_close(self):
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = App()
    app.mainloop()