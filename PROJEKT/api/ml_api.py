####

## Ładuje smog_model.pkl
## Uruchamia FastAPI na porcie 8001
## Endpoint /score

####


from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import pandas as pd

app = FastAPI(title="Smog Anomaly API")

# Wczytanie modelu
try:
    model = pickle.load(open('smog_model.pkl', 'rb'))
except FileNotFoundError:
    print("UWAGA: Nie znaleziono pliku 'smog_model.pkl'.")

class SensorData(BaseModel):
    sensor_id: str
    pm25: float
    lat: float
    lon: float
    humidity: float
    temperature: float
    wind_speed: float

@app.post("/score")
def score(data: SensorData):
    # Tworzymy DataFrame zawierający wszystkie cechy, na których model się uczył
    X = pd.DataFrame([{
        "pm25": data.pm25,
        "humidity": data.humidity,
        "temperature": data.temperature,
        "wind_speed": data.wind_speed
    }])
    
    # Przewidujemy prawdopodobieństwo
    proba = model.predict_proba(X)[0, 1] 
    
    return {
        "is_anomaly": bool(proba >= 0.5),
        "anomaly_probability": round(float(proba), 4)
    }

@app.get("/health")
def health():
    return {"status": "ok"}