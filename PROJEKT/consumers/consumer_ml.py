from kafka import KafkaConsumer, KafkaProducer
import json, requests

# UWAGA: Upewnij się, że adres API jest poprawny (localhost vs IP z ćwiczeń)
BROKER = "broker:9092"
API_URL = "http://127.0.0.1:8001/score" 

consumer = KafkaConsumer(
    'sensor_readings',
    bootstrap_servers=BROKER,
    group_id='ml-scoring-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

alert_producer = KafkaProducer(
    bootstrap_servers=BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("Konsument ML uruchomiony...")

for message in consumer:
    data = message.value
    
    # Bezpieczne pobieranie wartości z zabezpieczeniem przed starszymi wiadomościami
    features = {
        "sensor_id": data['sensor_id'],
        "pm25": data['pm25'],
        "lat": data['lat'],
        "lon": data['lon'],
        "humidity": data.get('humidity', 50.0),
        "temperature": data.get('temperature', 10.0),
        "wind_speed": data.get('wind_speed', 3.0)
    }
    
    try:
        # Timeout chroni konsumenta przed zawieszeniem
        response = requests.post(API_URL, json=features, timeout=2)
        result = response.json()
    except requests.RequestException as e:
        print(f"API niedostępne: {e}")
        continue

    if result.get('is_anomaly'):
        # Wzbogacamy oryginalne dane (w tym pogodowe) o flagi z modelu
        alert = {
            **data,
            'anomaly_probability': result['anomaly_probability'],
            'alert_source': 'ml_model',
            'alert_type': 'LOCAL_EXPLOSION'
        }
        alert_producer.send('alerts', value=alert)
        
        # Bardziej analityczny komunikat w terminalu
        print(
            f"🔥 ALERT ML [{result['anomaly_probability']:.0%}]: {data['sensor_id']} | "
            f"PM2.5: {data['pm25']} | Temp: {data.get('temperature', 'N/A'):.1f}°C | "
            f"Wiatr: {data.get('wind_speed', 'N/A'):.1f} m/s"
        )
        
alert_producer.flush()