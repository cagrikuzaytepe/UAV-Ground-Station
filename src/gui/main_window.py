import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import asyncio
import threading
from io import BytesIO

# ------------------------------------------------- 
# Stil / Tema Ayarları (Modern Arayüz)
# ------------------------------------------------- 
def setup_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#1E1E1E")
    style.configure(
        "TLabel", background="#1E1E1E", foreground="white", font=("Arial", 10)
    )
    style.configure(
        "TButton",
        background="#4CAF50",
        foreground="white",
        font=("Arial", 10, "bold"),
        borderwidth=0,
    )
    style.map("TButton", background=[("active", "#45a049")])
    style.configure("Header.TLabel", font=("Arial", 14, "bold"), foreground="#FFD700")


class DroneGUI:
    def __init__(self, root, controller, async_loop):
        self.root = root
        self.controller = controller
        self.async_loop = async_loop
        self.connected = False
        self.root.title("IHA Kontrol Paneli (Gerçek Drone - Pixhawk / Raspberry Pi)")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        setup_style()

        self.mode = "autonomous"
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.grid(row=0, column=0, columnspan=5, sticky="ew", pady=(0, 10))
        self.header_label = ttk.Label(
            self.header_frame, text="Drone Kontrol Paneli", style="Header.TLabel"
        )
        self.header_label.pack(fill="x")

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(0, 10))
        self.connect_button = ttk.Button(
            self.button_frame, text="Drone Bağlan", width=20, command=self.connect_drone
        )
        self.connect_button.grid(row=0, column=0, padx=5, pady=5)
        self.manual_button = ttk.Button(
            self.button_frame,
            text="Manuel Mod",
            width=20,
            command=self.start_manual,
            state="disabled",
        )
        self.manual_button.grid(row=0, column=1, padx=5, pady=5)
        self.auto_button = ttk.Button(
            self.button_frame,
            text="Otonom Mod",
            width=20,
            command=self.start_autonomous,
            state="disabled",
        )
        self.auto_button.grid(row=0, column=2, padx=5, pady=5)
        self.land_button = ttk.Button(
            self.button_frame,
            text="İniş",
            width=20,
            command=self.land,
            state="disabled",
        )
        self.land_button.grid(row=0, column=3, padx=5, pady=5)
        self.disconnect_button = ttk.Button(
            self.button_frame,
            text="Drone Bağlantısını Kes",
            width=20,
            command=self.disconnect_drone,
            state="disabled",
        )
        self.disconnect_button.grid(row=0, column=4, padx=5, pady=5)

        self.video_frame = ttk.Frame(self.main_frame, width=640, height=480)
        self.video_frame.grid(
            row=2, column=0, columnspan=3, sticky="nsew", pady=(0, 10)
        )
        self.video_frame.grid_propagate(False)
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack(fill="none", expand=True)

        self.manual_frame = ttk.Frame(self.main_frame)
        self._build_manual_panel()
        self.manual_frame.grid(row=2, column=3, sticky="nsew", padx=10, pady=10)
        self.manual_frame.grid_forget()

        self.info_frame = ttk.Frame(self.main_frame)
        self.info_frame.grid(row=3, column=0, columnspan=5, sticky="ew", pady=(0, 10))
        self.info_text = tk.Text(
            self.info_frame, height=10, width=100, bg="#1E1E1E", fg="white"
        )
        self.info_text.pack(fill="both", expand=True)
        self.log("Drone kontrol paneli başlatıldı...")

        self.telemetry_frame = ttk.Frame(self.main_frame)
        self.telemetry_frame.grid(
            row=4, column=0, columnspan=5, sticky="ew", pady=(0, 10)
        )
        self.telemetry_label = ttk.Label(
            self.telemetry_frame, text="Telemetri: Bekleniyor...", font=("Courier", 10)
        )
        self.telemetry_label.pack(anchor="w")

        self.root.bind("<Configure>", self.on_resize)
        self.root.after(1000, self.check_intersection_api)
        self.root.after(1000, self.check_image_analysis_api)
        self.root.after(1000, self.check_path_api)
        self.root.after(2000, self.check_crowd_api)
        self.root.after(30000, self.check_traffic_analysis_api)
        self.update_telemetry()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_resize(self, event):
        try:
            imgtk = getattr(self.video_label, "imgtk", None)
            if imgtk:
                image = ImageTk.getimage(imgtk)
                resized_image = image.resize(
                    (event.width - 20, event.height - 20), Image.ANTIALIAS
                )
                new_imgtk = ImageTk.PhotoImage(resized_image)
                self.video_label.config(image=new_imgtk)
                self.video_label.imgtk = new_imgtk
        except Exception:
            pass

    def log(self, message):
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        print(message)

    def _build_manual_panel(self):
        directions = [
            ("⬆️", "forward", 0, 1),
            ("⬅️", "left", 1, 0),
            ("⬇️", "backward", 2, 1),
            ("➡️", "right", 1, 2),
            ("↖️", "up_left", 0, 0),
            ("↗️", "up_right", 0, 2),
            ("↙️", "down_left", 2, 0),
            ("↘️", "down_right", 2, 2),
            ("⏫", "up", 1, 1),
            ("⏬", "down", 3, 1),
        ]
        for emoji, dir_name, r, c in directions:
            btn = ttk.Button(
                self.manual_frame,
                text=emoji,
                width=5,
                command=lambda d=dir_name: self.manual_control(d),
            )
            btn.grid(row=r, column=c, padx=3, pady=3)

    def connect_drone(self):
        if self.connected:
            self.log("Drone zaten bağlı.")
            return
        self.log("Drone bağlantısı sağlanıyor...")
        if self.controller.connected:
            self.connected = True
            self.log("Drone bağlantısı sağlandı.")
            self.manual_button.config(state="normal")
            self.auto_button.config(state="normal")
            self.land_button.config(state="normal")
            self.disconnect_button.config(state="normal")
        else:
            self.log("Drone bağlantısı yapılamadı.")

    def disconnect_drone(self):
        if not self.connected:
            self.log("Drone zaten bağlantısız.")
            return
        self.log("Drone bağlantısı kesiliyor...")
        asyncio.run_coroutine_threadsafe(self.controller.disconnect(), self.async_loop)
        self.connected = False
        self.manual_button.config(state="disabled")
        self.auto_button.config(state="disabled")
        self.land_button.config(state="disabled")
        self.disconnect_button.config(state="disabled")
        self.log("Drone bağlantısı kesildi.")

    def start_manual(self):
        if not self.connected:
            self.log("Lütfen önce drone bağlantısını kurun.")
            return
        self.mode = "manual"
        self.log("Manuel mod aktif.")
        self.manual_frame.grid(row=2, column=3, sticky="nsew", padx=10, pady=10)
        asyncio.run_coroutine_threadsafe(self.controller.arm_and_takeoff(5), self.async_loop)

    def start_autonomous(self):
        if not self.connected:
            self.log("Lütfen önce drone bağlantısını kurun.")
            return
        self.mode = "autonomous"
        self.log("Otonom mod aktif.")
        self.manual_frame.grid_forget()

    def manual_control(self, direction):
        if not self.connected:
            self.log("Lütfen önce drone bağlantısını kurun.")
            return
        self.log(f"Manuel kontrol: {direction}")
        mapping = {
            "forward": (1, 0, 0),
            "backward": (-1, 0, 0),
            "left": (0, -1, 0),
            "right": (0, 1, 0),
            "up": (0, 0, -1),  # DroneKit'te Z ekseni ters yönde yukarıdır.
            "down": (0, 0, 1),
            "up_left": (1, -1, -1),
            "up_right": (1, 1, -1),
            "down_left": (-1, -1, 1),
            "down_right": (-1, 1, 1),
        }
        if direction in mapping:
            vx, vy, vz = mapping.get(direction)
            asyncio.run_coroutine_threadsafe(
                self.controller.move_3d(vx, vy, vz, duration=1), self.async_loop
            )
        else:
            self.log(f"Bilinmeyen yön: {direction}")

    def land(self):
        if not self.connected:
            self.log("Lütfen önce drone bağlantısını kurun.")
            return
        self.log("İniş komutu gönderildi.")
        asyncio.run_coroutine_threadsafe(self.controller.land(), self.async_loop)

    def on_closing(self):
        asyncio.run_coroutine_threadsafe(self.controller.disconnect(), self.async_loop)
        self.root.destroy()

    def update_video(self):
        def fetch_and_update():
            try:
                response = requests.get(
                    "http://localhost:5000/camera_feed", timeout=0.5
                )
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((640, 480), Image.LANCZOS)
                    imgtk = ImageTk.PhotoImage(img)
                    self.video_label.after(
                        0, lambda: self.video_label.configure(image=imgtk)
                    )
                    self.video_label.imgtk = imgtk
                elif response.status_code == 503:
                    self.log("Kamera akışı bekleniyor...")
                else:
                    self.log(f"Kamera hatası: {response.status_code}")
            except Exception as e:
                self.log(f"Görüntü alınamadı: {str(e)}")

        threading.Thread(target=fetch_and_update, daemon=True).start()
        self.root.after(50, self.update_video)

    def update_telemetry(self):
        if not self.controller.connected:
            self.telemetry_label.config(text="Telemetri: Drone bağlı değil...")
            self.root.after(1000, self.update_telemetry)
            return
        try:
            loc = self.controller.vehicle.location.global_frame
            alt = self.controller.vehicle.location.global_relative_frame.alt
            gps = f"Lat: {loc.lat:.6f}, Lon: {loc.lon:.6f}, Alt: {alt:.2f} m"
        except Exception:
            gps = "GPS bilgisi alınamadı."
        try:
            bat = self.controller.vehicle.battery
            battery = f"Voltage: {bat.voltage} V, Current: {bat.current} A, Level: {bat.level} %"
        except Exception:
            battery = "Batarya bilgisi alınamadı."
        try:
            att = self.controller.vehicle.attitude
            attitude = (
                f"Roll: {att.roll:.2f}, Pitch: {att.pitch:.2f}, Yaw: {att.yaw:.2f}"
            )
        except Exception:
            attitude = "Attitude bilgisi alınamadı."
        telemetry_str = (
            f"Control Mode: {self.mode}\n"
            f"GPS: {gps}\n"
            f"Batarya: {battery}\n"
            f"Attitude: {attitude}\n"
        )
        self.telemetry_label.config(text=telemetry_str)
        self.root.after(1000, self.update_telemetry)

    def check_intersection_api(self):
        if not self.connected or self.mode != "autonomous":
            self.root.after(1000, self.check_intersection_api)
            return

        def fetch():
            try:
                response = requests.get(
                    "http://10.225.217.213:8000/intersection", timeout=1
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("is_intersection", False):
                        self.root.after(
                            0,
                            lambda:
                            self.log(
                                "4’lü kavşak tespit edildi! Drone durduruluyor..."
                            ),
                        )
                        asyncio.run_coroutine_threadsafe(
                            self.controller.stop(), self.async_loop
                        )
                        details_response = requests.get(
                            "http://localhost:5000/intersection_details", timeout=1
                        )
                        if details_response.status_code == 200:
                            details = details_response.json()
                            angle = details.get("angle")
                            distance = details.get("distance")
                            self.root.after(
                                0,
                                lambda:
                                self.log(
                                    f"Kavşak detayları: Açısı = {angle:.2f}, Mesafe = {distance:.2f}"
                                ),
                            )
                            asyncio.run_coroutine_threadsafe(
                                self.controller.turn_by_angle(angle), self.async_loop
                            )
                            asyncio.run_coroutine_threadsafe(
                                self.controller.move_distance(distance), self.async_loop
                            )
                        else:
                            self.root.after(
                                0, lambda: self.log("Intersection details API hatalı.")
                            )
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Intersection API hatası: {e}"))

        threading.Thread(target=fetch, daemon=True).start()
        self.root.after(1000, self.check_intersection_api)

    def check_image_analysis_api(self):
        if not self.connected or self.mode != "autonomous":
            self.root.after(1000, self.check_image_analysis_api)
            return

        def fetch():
            try:
                response = requests.get(
                    "http://localhost:5000/image_analysis", timeout=1
                )
                if response.status_code == 200:
                    data = response.json()
                    analysis_info = f"Görüntü Analizi: {data.get('analysis')}, Sayım: {data.get('count')}"
                    self.root.after(0, lambda: self.log(analysis_info))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Görüntü analiz API hatası: {e}"))

        threading.Thread(target=fetch, daemon=True).start()
        self.root.after(1000, self.check_image_analysis_api)

    def check_crowd_api(self):
        if not self.connected or self.mode != "autonomous":
            self.root.after(2000, self.check_crowd_api)
            return

        def fetch():
            try:
                response = requests.get(
                    "http://localhost:5000/crowd_details", timeout=1
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("crowd_found", False):
                        angle = data.get("angle")
                        distance = data.get("distance")
                        self.root.after(
                            0,
                            lambda:
                            self.log(
                                f"Kalabalık alan tespit edildi: Açısı = {angle:.2f}, Mesafe = {distance:.2f}"
                            ),
                        )
                        asyncio.run_coroutine_threadsafe(
                            self.controller.turn_by_angle(angle), self.async_loop
                        )
                        asyncio.run_coroutine_threadsafe(
                            self.controller.move_distance(distance), self.async_loop
                        )
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Crowd API hatası: {e}"))

        threading.Thread(target=fetch, daemon=True).start()
        self.root.after(2000, self.check_crowd_api)

    def check_path_api(self):
        if not self.connected or self.mode != "autonomous":
            self.root.after(1000, self.check_path_api)
            return

        def fetch():
            try:
                response = requests.get(
                    "http://localhost:5000/path_direction", timeout=1
                )
                if response.status_code == 200:
                    data = response.json()
                    angle = data.get("angle")
                    distance = data.get("distance")
                    self.root.after(
                        0,
                        lambda:
                        self.log(
                            f"Yol tespiti: Açısı = {angle:.2f}, Mesafe = {distance:.2f}"
                        ),
                    )
                    asyncio.run_coroutine_threadsafe(
                        self.controller.turn_by_angle(angle), self.async_loop
                    )
                    asyncio.run_coroutine_threadsafe(
                        self.controller.move_distance(distance), self.async_loop
                    )
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Path API hatası: {e}"))

        threading.Thread(target=fetch, daemon=True).start()
        self.root.after(1000, self.check_path_api)

    def check_traffic_analysis_api(self):
        if not self.connected or self.mode != "autonomous":
            self.root.after(30000, self.check_traffic_analysis_api)
            return

        def fetch():
            try:
                response = requests.get(
                    "http://localhost:5000/analyze_traffic", timeout=2
                )
                if response.status_code == 200:
                    data = response.json()
                    busiest_road = data.get("busiest_road")
                    vehicle_count = data.get("vehicle_count")
                    pedestrian_count = data.get("pedestrian_count")
                    self.root.after(
                        0,
                        lambda:
                        self.log(
                            f"Trafik Analizi: En kalabalık yol = {busiest_road}, Araç = {vehicle_count}, Yaya = {pedestrian_count}"
                        ),
                    )
                    opt_response = requests.get(
                        "http://localhost:5000/optimize_traffic_lights", timeout=2
                    )
                    if opt_response.status_code == 200:
                        opt_data = opt_response.json()
                        self.root.after(
                            0,
                            lambda: self.log(
                                f"Akıllı Trafik Işığı: {opt_data.get('status')}"
                            ),
                        )
                    else:
                        self.root.after(
                            0, lambda: self.log("Trafik analizi API hatalı.")
                        )
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Trafik analizi API hatası: {e}"))

        threading.Thread(target=fetch, daemon=True).start()
        self.root.after(30000, self.check_traffic_analysis_api)
