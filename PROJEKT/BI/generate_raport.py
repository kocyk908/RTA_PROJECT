####

## Czyta dane pomiarowe z pliku JSON (dane_pomiarowe.json)
## Oblicza podstawowe statystyki: średnia, max, min, odchylenie std
## Rysuje wykres PM2.5 w czasie z oznaczeniem progów alertów (60 i 110)
## W przypadku dużej liczby alertów (>20) pokazuje tylko 20 równomiernie rozłożonych
## Zapisuje wykres do pliku 'raport_wykres.png'
## Wyświetla legendę alertów z pełnym kontekstem pogodowym dla oznaczonych punktów

####

import textwrap
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

# Wczytaj dane z pliku
DATA_FILE = 'dane_pomiarowe.json'

try:
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    readings = data['readings']
    alerts = data['alerts']
    sensor_data = data.get('sensor_data', {})
    
    # Konwersja timestampów z powrotem na datetime
    for r in readings:
        r['timestamp'] = datetime.fromisoformat(r['timestamp'])
    for a in alerts:
        a['timestamp'] = datetime.fromisoformat(a['timestamp'])
    
except FileNotFoundError:
    print(f"Plik {DATA_FILE} nie istnieje. Uruchom najpierw dashboard")
    readings = []
    alerts = []
    sensor_data = {}

# ===== STATYSTYKI =====
if readings:
    pm25_vals = [r.get('pm25', 0) for r in readings]
    
    print("\n" + "=" * 60)
    print("STATYSTYKI ZEBRANYCH DANYCH")
    print("=" * 60)
    print(f"Liczba odczytow:     {len(readings)}")
    print(f"Liczba alertow:      {len(alerts)}")
    print(f"Sredni PM2.5:        {np.mean(pm25_vals):.1f} µg/m³")
    print(f"Maksymalny PM2.5:    {max(pm25_vals):.1f} µg/m³")
    print(f"Minimalny PM2.5:     {min(pm25_vals):.1f} µg/m³")
    print(f"Odchylenie std:      {np.std(pm25_vals):.1f}")
    print("=" * 60)
    
    # ===== PRZYGOTOWANIE ALERTÓW - RÓWNOMIERNE ROZŁOŻENIE =====
    MAX_ALERTS_ON_PLOT = 20  # Maksymalna liczba alertów na wykresie
    
    # Przygotuj listę alertów z pełnym kontekstem pogodowym (XAI)
    alert_list = []
    for a in alerts:
        alert_list.append({
            'time': a['timestamp'],
            'pm25': a.get('pm25', 0),
            'type': a.get('alert_type', 'UNKNOWN'),
            'sensor_id': a.get('sensor_id', '?'),
            'temp': a.get('temperature', 'N/A'),
            'wind': a.get('wind_speed', 'N/A'),
            'hum': a.get('humidity', 'N/A'),
            'reason': a.get('alert_reason', 'Analiza modelu ML')
        })
    
    # Posortuj chronologicznie
    alert_list.sort(key=lambda x: x['time'])
    total_alerts = len(alert_list)
    
    # ===== RÓWNOMIERNE WYBRANIE ALERTÓW =====
    if total_alerts > MAX_ALERTS_ON_PLOT:
        indices = np.linspace(0, total_alerts - 1, MAX_ALERTS_ON_PLOT, dtype=int)
        alerts_to_show = [alert_list[i] for i in indices]
        print(f"\nUWAGA: {total_alerts} alertow - pokazuje {MAX_ALERTS_ON_PLOT} rownomiernie rozlozonych")
    else:
        alerts_to_show = alert_list
        print(f"\nPokazuje wszystkie {total_alerts} alerty")
    
    # ===== LEGENDA ALERTÓW Z POGODĄ =====
    if alerts_to_show:
        print("\nLEGENDA ALERTOW (numery na wykresie):")
        print("-" * 120)
        for i, a in enumerate(alerts_to_show, 1):
            czas_str = a['time'].strftime('%H:%M:%S')
            
            # Wypisujemy główną linię
            print(f"{i:2d}. [{a['type']}] | Czujnik: {a['sensor_id']} | PM2.5: {a['pm25']:6.1f} | Czas: {czas_str}")
            
            # Jeśli to alert ML, dopisujemy warunki i powód
            # Jeśli to alert ML, dopisujemy warunki i powód
            if a['type'] == 'LOCAL_EXPLOSION':
                print(f"    ├─ Pogoda: Temp: {a['temp']}°C | Wiatr: {a['wind']}m/s | Wilg: {a['hum']}%")
                
                # Używamy wrappera do zawinięcia tekstu
                # width=100 określa max długość linii w konsoli
                # subsequent_indent to 17 spacji, które wyrównują nową linijkę idealnie pod tekstem diagnozy
                wrapped_reason = textwrap.fill(
                    a['reason'], 
                    width=100, 
                    subsequent_indent="                 " 
                )
                
                print(f"    └─ Diagnoza: {wrapped_reason}")
            print("-" * 120)
    else:
        print("\nBRAK ALERTOW w zebranych danych")
    
    # ===== WYKRES =====
    fig, ax = plt.subplots(figsize=(16, 8))
    
    times = [r['timestamp'] for r in readings]
    pm25_vals = [r.get('pm25', 0) for r in readings]
    
    # Wykres liniowy
    ax.plot(times, pm25_vals, 'b-', linewidth=0.8, alpha=0.6, label='PM2.5')
    
    ax.axhline(y=60, color='gold', linestyle=':', linewidth=1.5, alpha=0.7, label='Dolna granica anomalii (60)')
    ax.axhline(y=110, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='Maksymalna normalna (110)')
    
    # Oznacz wybrane alerty numerami na wykresie
    for i, a in enumerate(alerts_to_show, 1):
        ax.scatter(a['time'], a['pm25'], color='red', s=70, zorder=5, marker='o')
        ax.annotate(str(i), (a['time'], a['pm25']), 
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=9, fontweight='bold', color='red',
                   bbox=dict(boxstyle='circle', facecolor='white', 
                             edgecolor='red', linewidth=1.5, pad=0.3))
    
    # Formatowanie osi czasu
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    
    # Automatyczne dostosowanie zakresu Y
    max_pm = max(pm25_vals) if pm25_vals else 300
    ax.set_ylim(0, min(max_pm + 50, 600))
    
    # Etykiety i tytuł
    ax.set_xlabel('Czas')
    ax.set_ylabel('PM2.5 [µg/m³]')
    ax.set_title(f'PM2.5 w czasie - {len(readings)} odczytow\nPokazano {len(alerts_to_show)} z {total_alerts} alertow (rownomiernie rozlozone)', 
                 fontsize=14)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Zapisz wykres do pliku
    plt.savefig('raport_wykres.png', dpi=150, bbox_inches='tight')
    print("\nWykres zapisany jako 'raport_wykres.png'")
    plt.show()
    
else:
    print("Brak danych do wyświetlenia.")
