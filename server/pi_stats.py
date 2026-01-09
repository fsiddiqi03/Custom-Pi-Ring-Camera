from gpiozero import CPUTemperature
import psutil
import requests
from config import TEMP_API_URL

cpu = CPUTemperature()


def get_pi_stats():
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    cpu_usage = psutil.cpu_percent(interval=0.1)
    
    home_temp = 0
    try:
        response = requests.get(TEMP_API_URL, timeout=1)
        if response.status_code == 200:
            data = response.json()
            # Convert to int as requested
            home_temp = int(data.get('temperature', 0))
    except Exception as e:
        # Silently fail or log if needed, keep stats working
        print(f"Error fetching home temp: {e}")
    
    return {
        'cpu_temperature': int(round(cpu.temperature)),
        'cpu_usage': cpu_usage,
        'ram_usage': ram.percent,
        'disk_usage': disk.percent,
        'home_temperature': home_temp
    }

