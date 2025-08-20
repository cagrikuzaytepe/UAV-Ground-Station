from fastapi import FastAPI, Query, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import queue

# Bu app nesnesi ana dosyada (main.py) oluşturulacak ve buraya enjekte edilecek.
app = FastAPI()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bu global değişkenler main.py'de ayarlanacak
global_controller = None
frame_queue = queue.Queue(maxsize=50)
counter_value = 0

def setup_api_endpoints(controller):
    global global_controller
    global_controller = controller

    @app.get("/connect")
    async def api_connect():
        return {"status": "Gerçek drone connected"}

    @app.get("/arm_takeoff")
    async def api_arm_takeoff(altitude: int = 10):
        await global_controller.arm_and_takeoff(altitude)
        return {"status": f"Drone {altitude} metreye çıktı"}

    @app.get("/move")
    async def api_move(
        direction: str = Query(
            ...,
            regex="^(forward|backward|left|right|up|down|up_left|up_right|down_left|down_right)$",
        )
    ):
        # Bu kısım orijinal kodda dummy olarak bırakılmış, aynı şekilde bırakıyorum.
        return {"status": f"Drone {direction} hareket etti (dummy)"}

    @app.get("/move3d")
    async def api_move3d(
        velocity_x: float, velocity_y: float, velocity_z: float, duration: float = 1
    ):
        await global_controller.move_3d(velocity_x, velocity_y, velocity_z, duration)
        return {"status": "Drone 3 boyutlu hareket gerçekleştirdi"}

    @app.get("/turn")
    async def api_turn(angle: float):
        await global_controller.turn_by_angle(angle)
        return {"status": f"Drone {angle} derece döndü"}

    @app.get("/move_distance")
    async def api_move_distance(distance: float):
        await global_controller.move_distance(distance)
        return {"status": f"Drone {distance} metre ilerledi"}

    @app.get("/stop")
    async def api_stop():
        await global_controller.stop()
        return {"status": "Drone durdu"}

    @app.get("/land")
    async def api_land():
        await global_controller.land()
        return {"status": "Drone indi"}

    @app.get("/disconnect")
    async def api_disconnect():
        await global_controller.disconnect()
        return {"status": "Drone disconnected"}

    @app.get("/telemetry")
    async def api_telemetry():
        try:
            loc = global_controller.vehicle.location.global_frame
            alt = global_controller.vehicle.location.global_relative_frame.alt
            gps = {"lat": loc.lat, "lon": loc.lon, "alt": alt}
        except Exception:
            gps = {}
        try:
            bat = global_controller.vehicle.battery
            battery = {"voltage": bat.voltage, "current": bat.current, "level": bat.level}
        except Exception:
            battery = {}
        try:
            att = global_controller.vehicle.attitude
            attitude = {"roll": att.roll, "pitch": att.pitch, "yaw": att.yaw}
        except Exception:
            attitude = {}
        return {"gps": gps, "battery": battery, "attitude": attitude}

    @app.post("/upload_frame")
    async def upload_frame(file: UploadFile = File(...)):
        try:
            contents = await file.read()
            if frame_queue.full():
                frame_queue.get()
            frame_queue.put(contents)
            return {"status": "Frame alındı"}
        except Exception as e:
            return {"error": str(e)}

    @app.get("/camera_feed")
    async def api_camera_feed():
        try:
            if not frame_queue.empty():
                frame_data = frame_queue.get()
                return Response(content=frame_data, media_type="image/jpeg")
            else:
                return Response(status_code=503)
        except Exception as e:
            return Response(status_code=500)

    @app.get("/counter")
    def get_counter():
        global counter_value
        return {"counter": counter_value}

    @app.post("/counter/increment")
    def increment_counter():
        global counter_value
        counter_value += 1
        return {"counter": counter_value}

    return app
