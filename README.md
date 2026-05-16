# Projekt: Inteligentne Miasto - Monitorowanie Jakości Powietrza

Projekt symuluje zaawansowany system detekcji anomalii smogowych w czasie rzeczywistym. Wykorzystuje platformę Apache Kafka do strumieniowania zdarzeń oraz serwer FastAPI z wielowymiarowym modelem Machine Learning (klasyfikator Random Forest) do analizy i oceny odczytów na podstawie pełnego wektora parametrów atmosferycznych (PM2.5, wilgotność, temperatura oraz siła wiatru).

## 📂 Struktura Projektu

Zalecany podział plików w środowisku (np. JupyterLab):
* `api/`
  * `train_model.py` (Skrypt generujący i trenujący model RF)
  * `ml_api.py` (Serwer FastAPI wystawiający model do scoringu)
* `generator/`
  * `producer.py` (Generator danych z czujników)
* `consumers/`
  * `consumer_rules.py` (Wykrywa błąd "stuck sensor" - zawieszony czujnik)
  * `consumer_ml.py` (Wykrywa piki zanieczyszczeń odpytując API)

---

## 🚀 Jak uruchomić projekt (Krok po Kroku)

Aby uniknąć blokowania portów i zachować pełną kontrolę, każdy element systemu uruchamiamy w **osobnej zakładce terminala**.

### Krok 1: Trening Modelu ML
W pierwszym terminalu przejdź do folderu `api` i wygeneruj model. Robimy to tylko raz.
```bash
python train_model.py
```
Spodziewany efekt: Skrypt wygeneruje plik smog_model.pkl i wypisze raport z klasyfikacji.

#### Uwaga analityczna na zaliczenie:
Dane syntetyczne celowo wykorzystują nakładające się na siebie rozkłady prawdopodobieństwa (szum informacyjny), aby zasymulować warunki rzeczywiste. Wyniki celowo nie są idealne (Precision dla anomalii wynosi ok. 0.92, a Recall ok. 0.85). Pokazuje to zdolność modelu do radzenia sobie z fałszywymi alarmami oraz subtelnymi anomaliami bez przerysowanych uproszczeń.

### Krok 2: Uruchomienie Serwera API
W tym samym terminalu wystaw wytrenowany model przez FastAPI.

```Bash
uvicorn ml_api:app --host 0.0.0.0 --port 8001
```
Spodziewany efekt: Komunikat Application startup complete. Serwer czeka na zapytania.

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

``` Bash
python producer.py
```
Spodziewany efekt: Na ekranie zaczną pojawiać się wysyłane odczyty (np. Wysłano: SENSOR_03 | PM2.5: 22.45).

📊 Czego się spodziewać (Logi i Alerty)
Gdy system pracuje, obserwuj otwarte terminale:

Terminal 1 (API):
Zaczną spływać logi serwera HTTP z kodami 200 OK przy każdym żądaniu na endpoint /score, co oznacza, że konsument ML nieustannie przesyła wektory cech do analizy.

Terminal 2 (Konsument Regułowy):
Przez większość czasu okno pozostanie puste. Jeśli generator zasymuluje awarię techniczną (czujnik wyśle 5 razy pod rząd dokładnie taką samą wartość z powodu zawieszenia), konsument stanowy natychmiast to wychwyci i wyśle alert:
🚨 ALERT REGUŁOWY: Czujnik SENSOR_02 zawiesił się na wartości 15.30!

Terminal 3 (Konsument ML):
Gdy w systemie pojawi się kombinacja niepokojących cech (np. wysoki poziom pyłów wygenerowany przez pożar, niska temperatura i brak wiatru), wdrożony model oceni prawdopodobieństwo anomalii. Log zawiera pełne, urealnione podsumowanie pogodowe:
🔥 ALERT ML [92%]: SENSOR_04 | PM2.5: 185.50 | Temp: -2.3°C | Wiatr: 1.0 m/s

💡 W razie problemu "Address already in use" na porcie 8001, użyj komendy **pkill -f uvicorn** aby zabić zawieszone procesy API.
