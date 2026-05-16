from kafka import KafkaProducer
import json, random, time
from datetime import datetime

# Konfiguracja producenta na wzór ćwiczeń
producer = KafkaProducer(
    bootstrap_servers='broker:9092', # <-- ZMIANA TUTAJ
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

sensors = [f"SENSOR_{i:02d}" for i in range(1, 6)]

# Stan dla zablokowanych czujników ("stuck sensor")
stuck_sensor_state = {}

def generate_sensor_reading():
    sensor_id = random.choice(sensors)
    
    # 1. Symulacja błędu "stuck sensor" (czujnik się zawiesza i wysyła to samo)
    if random.random() < 0.05 and sensor_id not in stuck_sensor_state:
        stuck_sensor_state[sensor_id] = {'pm25': round(random.uniform(10, 30), 2), 'ticks_left': 5}
        
    if sensor_id in stuck_sensor_state:
        reading = stuck_sensor_state[sensor_id]['pm25']
        stuck_sensor_state[sensor_id]['ticks_left'] -= 1
        if stuck_sensor_state[sensor_id]['ticks_left'] <= 0:
            del stuck_sensor_state[sensor_id] # Czujnik "odwiesza się"
    else:
        # Normalny odczyt z lekką fluktuacją
        reading = round(random.uniform(10.0, 40.0), 2)
        
        # 2. Symulacja "lokalnego wybuchuv"
        if random.random() < 0.02:
            reading = round(random.uniform(200.0, 500.0), 2)

    return {
        'sensor_id': sensor_id,
        'lat': 52.2297 + random.uniform(-0.01, 0.01),
        'lon': 21.0122 + random.uniform(-0.01, 0.01),
        'pm25': reading,
        'humidity': round(random.uniform(40.0, 90.0), 2),
        'temperature': round(random.uniform(-5.0, 15.0), 2),
        'wind_speed': round(random.uniform(0.0, 10.0), 2),
        'timestamp': datetime.now().isoformat()
    }

print("Uruchamiam sieć czujników smogu...")
while True:
    data = generate_sensor_reading()
    producer.send('sensor_readings', value=data)
    print(f"Wysłano: {data['sensor_id']} | PM2.5: {data['pm25']}")
    time.sleep(1)