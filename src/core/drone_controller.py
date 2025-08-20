import asyncio
import time
from dronekit import connect, VehicleMode

class RealDroneController:
    def __init__(self, connection_string="127.0.0.1:5760"):
        """
        Raspberry Pi 4B üzerinden Pixhawk'a seri bağlantı için örnek bağlantı dizesi.
        Kendi donanımınıza göre güncellenebilir.
        """
        self.connected = False
        self.connection_string = connection_string
        self.vehicle = None
        self.log("Gerçek drone bağlantısı oluşturuluyor...")
        self._connect_drone()

    def log(self, message):
        print(message)

    def _connect_drone(self):
        try:
            # Pixhawk'a Raspberry Pi üzerinden seri bağlantı kuruluyor.
            self.vehicle = connect(self.connection_string, wait_ready=True, timeout=60)
            self.connected = True
            self.log("Drone bağlantısı başarılı.")
        except Exception as e:
            self.log(f"Drone bağlantı hatası: {e}")
            self.connected = False

    async def arm_and_takeoff(self, target_altitude):
        if not self.connected:
            self.log("Drone bağlı değil. Lütfen bağlantıyı kontrol edin.")
            return
        await asyncio.get_event_loop().run_in_executor(
            None, self._arm_and_takeoff_blocking, target_altitude
        )

    def _arm_and_takeoff_blocking(self, target_altitude):
        vehicle = self.vehicle
        self.log("Arm işlemi başlatılıyor...")
        while not vehicle.is_armable:
            self.log("Drone arm edilebilir durumda değil, bekleniyor...")
            time.sleep(1)
        vehicle.mode = VehicleMode("GUIDED")
        vehicle.armed = True
        while not vehicle.armed:
            self.log("Drone arm oluyor, bekleniyor...")
            time.sleep(1)
        self.log("Drone armed, kalkışa geçiliyor...")
        vehicle.simple_takeoff(target_altitude)
        while True:
            alt = vehicle.location.global_relative_frame.alt
            self.log(f"Mevcut irtifa: {alt:.2f} m")
            if alt >= target_altitude * 0.95:
                break
            time.sleep(1)
        self.log("Hedef irtifaya ulaşıldı.")

    async def send_ned_velocity(self, velocity_x, velocity_y, velocity_z, duration=1):
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._send_ned_velocity_blocking,
            velocity_x,
            velocity_y,
            velocity_z,
            duration,
        )

    def _send_ned_velocity_blocking(self, velocity_x, velocity_y, velocity_z, duration):
        vehicle = self.vehicle
        msg = vehicle.message_factory.set_position_target_local_ned_encode(
            0,
            0,
            0,
            0b0000111111000111,  # Sadece hız bileşenleri aktif
            0,
            0,
            0,
            velocity_x,
            velocity_y,
            velocity_z,
            0,
            0,
            0,
            0,
            0,
        )
        for _ in range(int(duration * 10)):
            vehicle.send_mavlink(msg)
            time.sleep(0.1)
        self.log(
            f"{duration} saniye boyunca (x:{velocity_x}, y:{velocity_y}, z:{velocity_z}) hızı gönderildi."
        )

    async def move_3d(
        self,
        velocity_x: float,
        velocity_y: float,
        velocity_z: float,
        duration: float = 1,
    ):
        self.log(
            f"3 boyutlu hareket: x:{velocity_x}, y:{velocity_y}, z:{velocity_z} için {duration} saniye."
        )
        await self.send_ned_velocity(velocity_x, velocity_y, velocity_z, duration)

    async def turn_by_angle(self, angle):
        await asyncio.get_event_loop().run_in_executor(
            None, self._turn_by_angle_blocking, angle
        )

    def _turn_by_angle_blocking(self, angle):
        vehicle = self.vehicle
        self.log(f"{angle:.2f} derece dönme komutu gönderiliyor...")
        msg = vehicle.message_factory.command_long_encode(
            0, 0, 115, 0, angle, 0, 1, 1, 0, 0, 0  # MAV_CMD_CONDITION_YAW
        )
        vehicle.send_mavlink(msg)
        time.sleep(3)
        self.log(f"{angle:.2f} derece dönüş tamamlandı.")

    async def stop(self):
        self.log("Drone durduruluyor...")
        await self.send_ned_velocity(0, 0, 0)

    async def land(self):
        if not self.connected:
            self.log("Drone bağlı değil.")
            return
        await asyncio.get_event_loop().run_in_executor(None, self._land_blocking)

    def _land_blocking(self):
        vehicle = self.vehicle
        self.log("İniş komutu gönderiliyor...")
        vehicle.mode = VehicleMode("LAND")
        time.sleep(10)
        self.log("Drone indi.")

    async def disconnect(self):
        await asyncio.get_event_loop().run_in_executor(None, self._disconnect_blocking)

    def _disconnect_blocking(self):
        if self.vehicle:
            self.log("Drone bağlantısı kesiliyor...")
            self.vehicle.close()
            self.connected = False
            self.log("Drone bağlantısı kesildi.")

    async def move_distance(self, distance):
        self.log(f"Drone {distance:.2f} metre ileri hareket edecek.")
        duration = abs(distance) / 1.0
        await self.send_ned_velocity(1 if distance >= 0 else -1, 0, 0, duration)
