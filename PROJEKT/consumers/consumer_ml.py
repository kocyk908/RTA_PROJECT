####

##  Czyta odczyty z czujników z topicu 'sensor_readings' z Kafki.
##  Wysyła zapytanie do serwera predykcyjnego (ml_api.py) z danymi o pyłach i pogodzie.
##  Sprawdza, czy model Random Forest sklasyfikował odczyt jako anomalię.
##  Jeśli wykryto anomalię, generuje czytelny powód zdarzenia (np. zastój powietrza, niska temperatura).
##  Wysyła alert LOCAL_EXPLOSION do topicu alerts, powód i prawdopodobieństwo

####


from kafka import KafkaConsumer, KafkaProducer
import json, requests

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
        response = requests.post(API_URL, json=features, timeout=2)
        result = response.json()
    except requests.RequestException as e:
        print(f"API niedostępne: {e}")
        continue

    if result.get('is_anomaly'):
        pm = data['pm25']
        wind = data.get('wind_speed', 3.0)
        temp = data.get('temperature', 10.0)
        hum = data.get('humidity', 50.0)
        
        # --- NOWA LOGIKA: Tłumaczenie decyzji modelu ---
        reasons = []
        
        # 1. Sprawdzamy stężenie pyłu
        if pm >= 150:
            reasons.append("Ekstremalnie wysokie stężenie bazowe PM2.5")
        
        # 2. Sprawdzamy wiatr
        if wind <= 1.5:
            reasons.append("Brak wiatru (zastój powietrza)")
            
        # 3. Sprawdzamy temperaturę (inwersja termiczna / dogrzewanie domów)
        if temp < 2.0:
            reasons.append("Niska temperatura (wzrost emisji z kominów)")
            
        # 4. Sprawdzamy wilgotność
        if hum >= 75:
            reasons.append("Wysoka wilgotność (sprzyja gęstnieniu pyłów)")

        # Jeśli PM jest niskie (szara strefa), ale model wyłapał anomalię pogody
        if pm < 110 and not reasons:
             context_msg = "Złożona korelacja pogodowa sprzyjająca kumulacji pyłów"
        else:
             # Łączymy powody przecinkami, jeśli jakiekolwiek znaleziono
             context_msg = " | ".join(reasons) if reasons else "Znaczne stężenie PM2.5"

        # Wzbogacamy oryginalne dane o flagi z modelu oraz nasze wyjaśnienie
        alert = {
            **data,
            'anomaly_probability': result['anomaly_probability'],
            'alert_source': 'ml_model',
            'alert_type': 'LOCAL_EXPLOSION',
            'alert_reason': context_msg,
            'alert': True
        }
        alert_producer.send('alerts', value=alert)
        
        # Rozbudowany, czytelniejszy komunikat w terminalu
        print(
            f"ALERT ML [{result['anomaly_probability']:.0%}]: {data['sensor_id']} \n"
            f"  ├─ PM2.5: {pm} µg/m³\n"
            f"  ├─ Pogoda: {temp:.1f}°C | Wiatr: {wind:.1f} m/s | Wilg: {hum:.0f}%\n"
            f"  └─ Wniosek: {context_msg}\n"
        )
        
alert_producer.flush()