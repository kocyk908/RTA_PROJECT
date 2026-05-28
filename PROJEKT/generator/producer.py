####

## Symuluje 5 czujników - wybiera losowy co 0.5 sekundy
## Generuje odczyty:
##    - W większości przypadków wysyła normalne, codzienne stężenia pyłów.
##    - Czasem losuje drastyczny (LOCAL_EXPLOSION) smogu (rzędu 200-350 µg/m³).
## Generuje zablokowane czujniki (STUCK_SENSOR) - 5% szans, 5 razy ta sama wartość
## Dodaje dane o pogodzie (wiatr, temperaturę, wilgotność) i wysyła całość
##    do Kafki (na topic 'sensor_readings').

####


from kafka import KafkaProducer
import json, random, time
from datetime import datetime

# Konfiguracja producenta na wzór ćwiczeń
producer = KafkaProducer(
    bootstrap_servers='broker:9092',
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
         # 2. Wartości z podziałem na 3 zakresy
        r = random.random()
        
        if r < 0.92:           # niskie normalne (10-40)
            reading = round(random.uniform(10.0, 40.0), 2)
        elif r < 0.95:         # podwyższone (60-110)
            reading = round(random.uniform(60.0, 110.0), 2)
        elif r < 0.97:         # wysokie (120-180)
            reading = round(random.uniform(120.0, 180.0), 2)
        else:                  # anomalie (200-350) - obniżone z 500 do 350
            reading = round(random.uniform(200.0, 350.0), 2)

    return {
        'sensor_id': sensor_id,
        'lat': 52.2297 + random.uniform(-0.01, 0.01), # nie używane w analizie
        'lon': 21.0122 + random.uniform(-0.01, 0.01), # nie używane w analizie
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
    print(f"{data['sensor_id']} | "
          f"PM2.5: {data['pm25']:6.2f} | "
          f"Temp: {data['temperature']:5.1f}°C | "
          f"Wiatr: {data['wind_speed']:4.1f}m/s | "
          f"Wilgotność: {data['humidity']:5.1f}")
    time.sleep(0.5)