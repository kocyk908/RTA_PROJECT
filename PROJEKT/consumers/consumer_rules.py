####

## Czyta sensor_readings z Kafki
## Przechowuje 5 ostatnich odczytów dla każdego czujnika
## Sprawdza czy 5 odczytów jest identycznych
## Wysyła alert STUCK_SENSOR do topicu alerts

####


from kafka import KafkaConsumer, KafkaProducer
import json
from collections import defaultdict

consumer = KafkaConsumer(
    'sensor_readings',
    bootstrap_servers='broker:9092',
    auto_offset_reset='latest',
    group_id='rules-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

alert_producer = KafkaProducer(
    bootstrap_servers='broker:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Przechowujemy 5 ostatnich odczytów dla każdego czujnika
sensor_history = defaultdict(list)

print("Nasłuchuję anomalii regułowych (Stuck Sensor)...")

for message in consumer:
    data = message.value
    s_id = data['sensor_id']
    pm25 = data['pm25']
    
    sensor_history[s_id].append(pm25)
    
    # Utrzymujemy tylko 5 ostatnich odczytów
    if len(sensor_history[s_id]) > 5:
        sensor_history[s_id].pop(0)
        
    # Jeśli mamy 5 odczytów i wszystkie są identyczne (zbiór ma długość 1)
    if len(sensor_history[s_id]) == 5 and len(set(sensor_history[s_id])) == 1:
        alert = {**data, 'alert_type': 'STUCK_SENSOR', 'alert': True}
        alert_producer.send('alerts', value=alert)
        print(f"ALERT REGUŁOWY: Czujnik {s_id} zawiesił się na wartości {pm25}!")
        sensor_history[s_id].clear() # Resetujemy po alercie