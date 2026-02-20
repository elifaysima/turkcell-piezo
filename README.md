


# PİYON — Edge Gateway Yaya Akış İzleme Sistemi

PİYON, piezo tabanlı adım sensörlerinden alınan veriyi MQTT üzerinden edge gateway’e ileten, burada füzyon, sezonsallık modelleme ve anomali algılama uygulayarak gerçek zamanlı yoğunluk analizi yapan bir IoT veri işleme sistemidir.

Sistem sensörsüz demo (fake veri) ve gerçek ESP32 sensör modunda çalışabilir.

---

# Özellikler

- MQTT tabanlı veri akışı
- Çoklu sensör füzyonu (robust median)
- Sezonsal yoğunluk modeli (hour-of-week)
- EWMA ve sezonsal anomali algılama
- Sensör sağlık izleme (offline, stuck, outlier)
- Canlı dashboard (Dash/Plotly)

---

# Mimari

```mermaid
flowchart LR
  ESP[ESP32 Piezo Sensor]
  MQTT[(MQTT Broker)]
  EDGE[Edge Gateway Python]
  FUS[Fusion Engine]
  SEA[Seasonal Model]
  ANO[Anomaly Detection]
  UI[Dashboard]

  ESP --> MQTT
  MQTT --> EDGE
  EDGE --> FUS
  FUS --> SEA
  SEA --> ANO
  ANO --> UI
```

flowchart TD
  common --> fusion
  common --> anomaly
  common --> health

  fusion --> anomaly
  seasonal --> anomaly

  health --> dashboard
  anomaly --> dashboard
  fusion --> dashboard

  ESP32 → MQTT → Edge Gateway (Python)
          ↓
        Fusion → Seasonal → Anomaly
                          ↓
                       Dashboard


repo
 ├── src
 │ ├── common.py
 │ ├── anomaly.py
 │ ├── fusion.py
 │ ├── seasonal.py
 │ ├── health.py
 │ ├── dashboard.py
 │ └── fake_publisher.py
 │
 ├── scripts
 │ ├── jury_demo.ps1
 │ └── stop_demo.ps1
 │
 ├── requirements.txt
 └── README.md





