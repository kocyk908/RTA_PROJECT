import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle

# Ziarno losowości dla powtarzalności wyników
np.random.seed(42)

N_NORMAL = 5000
N_ANOMALY = 200

print("Generowanie rozszerzonych danych syntetycznych...")

# Normalne odczyty: typowa pogoda
normal_data = pd.DataFrame({
    # Rozkład log-normalny: zazwyczaj niska wartość, ale "ogon" potrafi dobić do 110!
    'pm25': np.random.lognormal(mean=3.2, sigma=0.6, size=N_NORMAL).clip(5, 110),
    'humidity': np.random.normal(65, 15, N_NORMAL).clip(0, 100),
    'temperature': np.random.normal(8, 10, N_NORMAL),
    # Poisson: wiatr średnio 3 m/s, ale często też 0 lub 1
    'wind_speed': np.random.poisson(lam=3.0, size=N_NORMAL),
    'is_anomaly': 0
})

anomaly_data = pd.DataFrame({
    # UWAGA: Anomalie zaczynamy już od 80! Będą się mocno mieszać z gorszymi dniami "w normie"
    'pm25': np.random.uniform(80, 250, N_ANOMALY),
    'humidity': np.random.normal(80, 10, N_ANOMALY).clip(0, 100),
    'temperature': np.random.normal(0, 8, N_ANOMALY),
    # Poisson: przy smogu wiatr jest słaby (średnio 1 m/s), ale pokrywa się z dniami w normie
    'wind_speed': np.random.poisson(lam=1.0, size=N_ANOMALY), 
    'is_anomaly': 1
})

# Łączenie i mieszanie danych
df = pd.concat([normal_data, anomaly_data], ignore_index=True).sample(frac=1, random_state=42)

# Teraz model faktycznie ma z czego pobrać te kolumny!
features = ['pm25', 'humidity', 'temperature', 'wind_speed']
X = df[features]
y = df['is_anomaly']

# Podział na zbiór treningowy i testowy
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

print("Trenowanie zaawansowanego modelu Random Forest...")
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Ocena i zapis
y_pred = clf.predict(X_test)
print("\nRaport z klasyfikacji:")
print(classification_report(y_test, y_pred))

with open('smog_model.pkl', 'wb') as f:
    pickle.dump(clf, f)

print("Nowy model zapisany pomyślnie do pliku 'smog_model.pkl'!")