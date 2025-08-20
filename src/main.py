import asyncio
import threading
import tkinter as tk
import uvicorn

from core.drone_controller import RealDroneController
from gui.main_window import DroneGUI
from api.endpoints import setup_api_endpoints


def run_api(app):
    uvicorn.run(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    # Asenkron olay döngüsünü ayarla ve ayrı bir thread'de çalıştır
    async_loop = asyncio.new_event_loop()
    threading.Thread(target=async_loop.run_forever, daemon=True).start()

    # Drone kontrolcüsünü başlat
    # Bağlantı dizesini simülasyon için güncelleyin
    # Mission Planner SITL için: "udp:127.0.0.1:14550"
    drone_controller = RealDroneController(connection_string="udp:127.0.0.1:14550")

    # FastAPI uygulamasını ve endpoint'lerini ayarla
    app = setup_api_endpoints(drone_controller)

    # API sunucusunu ayrı bir thread'de başlat
    api_thread = threading.Thread(target=run_api, args=(app,), daemon=True)
    api_thread.start()

    # Tkinter tabanlı GUI'yi başlat
    root = tk.Tk()
    app_gui = DroneGUI(root, drone_controller, async_loop)
    
    # Video akışını başlatmak için bu satırın yorumunu kaldırabilirsiniz
    # app_gui.update_video() 
    
    root.mainloop()
