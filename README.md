# Projekt: Inteligentne Miasto - Monitorowanie Jakości Powietrza

Projekt symuluje zaawansowany system detekcji anomalii smogowych w czasie rzeczywistym. Wykorzystuje platformę Apache Kafka do strumieniowania zdarzeń oraz serwer FastAPI z wielowymiarowym modelem Machine Learning (klasyfikator Random Forest) do analizy i oceny odczytów na podstawie pełnego wektora parametrów atmosferycznych (PM2.5, wilgotność, temperatura oraz siła wiatru).

## 📂 Struktura Projektu

Zalecany podział plików w środowisku (np. JupyterLab):
* `api/`
  * `train_model.py`
  * `ml_api.py`
* `generator/`
  * `producer.py`
* `consumers/`
  * `consumer_rules.py`
  * `consumer_ml.py`
* `BI/`
  * `dashboard.ipynb`
  * `generate_raport.py`
* `stop_project.sh`

---

## Jak uruchomić projekt (Krok po Kroku)

Aby uniknąć blokowania portów i zachować pełną kontrolę, każdy element systemu uruchamiamy w **osobnej zakładce terminala**.

### Krok 0: Przygotowanie środowiska

Przed uruchomieniem projektu zatrzymaj uruchomione procesy:
```
bash stop_project.sh
```

### Krok 1: Trening Modelu ML
W pierwszym terminalu przejdź do folderu `api` i wygeneruj model. Robimy to tylko raz.
```
python train_model.py
```
Spodziewany efekt: Skrypt wygeneruje plik smog_model.pkl i wypisze raport z klasyfikacji.

####Interpretacja wyników:

- Precision (anomalie) = 0.83 – 83% alertów to prawdziwe anomalie

- Recall (anomalie) = 0.95 – model wykrywa 95% wszystkich anomalii

- Accuracy = 0.99 – 99% ogólnej skuteczności klasyfikacji

Dane syntetyczne celowo wykorzystują nakładające się na siebie rozkłady prawdopodobieństwa (szum informacyjny), aby zasymulować warunki rzeczywiste. Wyniki nie są idealne, co pokazuje zdolność modelu do radzenia sobie z fałszywymi alarmami oraz subtelnymi anomaliami bez przerysowanych uproszczeń.

### Krok 2: Uruchomienie Serwera API
W tym samym terminalu wystaw wytrenowany model przez FastAPI.

```
uvicorn ml_api:app --host 0.0.0.0 --port 8001
```
Spodziewany efekt: Komunikat Application startup complete. Serwer czeka na zapytania.

💡 W razie problemu "Address already in use" na porcie 8001, użyj komendy
```
pkill -f uvicorn
```
aby zabić zawieszone procesy API.

### Krok 3: Uruchomienie Konsumentów (Nasłuch)
Otwórz dwa nowe terminale i przejdź w nich do folderu consumers.

W Terminalu 2 uruchom: 
``` 
python consumer_rules.py
```
W Terminalu 3 uruchom: 
``` 
python consumer_ml.py
```
Spodziewany efekt: Skrypty nawiążą połączenie z brokerem, wypiszą komunikaty powitalne i zawisną w pętli, oczekując na pojawienie się nowych wiadomości z topicu Kafki.

### Krok 4: Start Generatora Danych
Otwórz czwarty terminal, przejdź do folderu **generator** i uruchom sieć czujników:
```
python producer.py
```
Spodziewany efekt: Na ekranie zaczną pojawiać się wysyłane odczyty (np. Wysłano: SENSOR_04 | PM2.5:  21.33 | Temp:  -1.9°C | Wiatr:  8.8m/s | Wilgotność:  80.8).

Czego się spodziewać (Logi i Alerty)
Gdy system pracuje, obserwuj otwarte terminale:

Terminal 1 (API):
Zaczną spływać logi serwera HTTP z kodami 200 OK przy każdym żądaniu na endpoint /score, co oznacza, że konsument ML nieustannie przesyła wektory cech do analizy.

Terminal 2 (Konsument Regułowy):
Przez większość czasu okno pozostanie puste. Jeśli generator zasymuluje awarię techniczną (czujnik wyśle 5 razy pod rząd dokładnie taką samą wartość z powodu zawieszenia), konsument stanowy natychmiast to wychwyci i wyśle alert:
ALERT REGUŁOWY: Czujnik SENSOR_02 zawiesił się na wartości 15.30!

Terminal 3 (Konsument ML):
Gdy w systemie pojawi się kombinacja niepokojących cech (np. wysoki poziom pyłów wygenerowany przez pożar, niska temperatura i brak wiatru), wdrożony model oceni prawdopodobieństwo anomalii. Log zawiera pełne, urealnione podsumowanie pogodowe:
ALERT ML [53%]: SENSOR_04 
  ├─ PM2.5: 244.22 µg/m³
  ├─ Pogoda: 14.6°C | Wiatr: 2.5 m/s | Wilg: 48%
  └─ Wniosek: Ekstremalnie wysokie stężenie bazowe PM2.5

### Krok 5: LIVE Dashboard i generowanie raportu
Otwórz folder **BI** i otwórz: 
```
dashboard.ipynb
```
w Jupyterze wykonaj kolejno:
- Komórka 1 – Uruchom konsumenta Kafki
- Komórka 2 – Wyświetlanie wykresów

Po zebraniu danych (dashboard zapisuje je do dane_pomiarowe.json), możesz wygenerować statyczny raport:
```
python generate_raport.py
```
Raport zawiera:

- Podstawowe statystyki (średnia, max, min, odchylenie std)
- Wykres PM2.5 w czasie z oznaczonymi alertami
- Legendę alertów z numerami odpowiadającymi oznaczeniom na wykresie

Wykres zostanie zapisany jako raport_wykres.png.

