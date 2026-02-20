


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


Python paketleri
Bash
Kodu kopyala
pip install -r requirements.txt
MQTT Broker (Mosquitto)
Windows’ta broker başlatma:
PowerShell
Kodu kopyala
Start-Process "C:\Program Files\mosquitto\mosquitto.exe" -ArgumentList "-v"
Demo (Sensör Yok)
Tek komutla demo:
PowerShell
Kodu kopyala
powershell -ExecutionPolicy Bypass -File .\scripts\jury_demo.ps1
Dashboard:
Kodu kopyala

http://127.0.0.1:8050
Demo (Sensör Var)
ESP32 topic:
Kodu kopyala

piyon/v1/steps
Laptop IPv4 öğren:
PowerShell
Kodu kopyala
ipconfig
ESP32 firmware’de MQTT_HOST = laptop IPv4
Sensör varken fake publisher kapalı olmalı.
Veri Şeması (StepPacket)
JSON
Kodu kopyala
{
  "site_id": "CORRIDOR_1",
  "module_id": "MOD_01",
  "ts": 1700000000,
  "window_s": 1,
  "steps_dir1": 4,
  "steps_dir2": 2
}
Anomali Sistemi
Algılanan anomali tipleri:
SPIKE_EWMA
SPIKE_SEASONAL
ONE_SIDED
LOW_DEMAND_CROWD
Sensör Sağlık İzleme
SENSOR_OFFLINE
STUCK_ZERO
STUCK_CONST
OUTLIER_MODULE
Demo Kapatma
PowerShell
Kodu kopyala
powershell -ExecutionPolicy Bypass -File .\scripts\stop_demo.ps1

## 3.3 Veri Şeması

Sistem MQTT üzerinden aşağıdaki JSON formatında veri bekler.

```json
{
  "site_id": "CORRIDOR_1",
  "module_id": "MOD_01",
  "ts": 1700000000,
  "window_s": 1,
  "steps_dir1": 4,
  "steps_dir2": 2
}
```
## 3.4 Sensör Var Modu (ESP32)

Gerçek sensör ile çalışırken aşağıdaki ayarlar yapılmalıdır.

### MQTT Ayarları
- Topic: `piyon/v1/steps`
- Broker: laptop IPv4 adresi
- Port: 1883

### ESP32 Ayarları
1) Wi-Fi bağlantısı kur
2) MQTT_HOST = laptop IPv4
3) Fake publisher kapalı olmalı

Laptop IPv4 öğrenmek için:

```powershell
ipconfig
```
## 3.5 Anomali Algılama Sistemi

Sistem, yaya akışındaki olağandışı durumları tespit etmek için çok katmanlı bir anomali algılama yaklaşımı kullanır.

Algoritma hem kısa vadeli akış değişimlerini hem de uzun vadeli sezonsal davranışı dikkate alır.

### Kullanılan Yöntemler

**1) EWMA Spike Detection**  
Akış değerleri için üstel ağırlıklı hareketli ortalama (EWMA) kullanılır.  
Bu model ani sıçramaları (spike) tespit eder.

**2) Seasonal Spike Detection**  
Saatlik ve haftalık yoğunluk örüntüsü modellenir.  
Beklenen yoğunluğun üzerinde gerçekleşen akışlar sezonsal anomali olarak işaretlenir.

**3) One-Sided Flow Detection**  
Yaya akışının tek yönde yoğunlaşması durumunda yön oranı incelenir.  
Bu durum kuyruk oluşumu veya yönsel sıkışma göstergesi olabilir.

**4) Low Demand Crowd Detection**  
Düşük yoğunluk beklenen saatlerde yüksek akış görülmesi durumunda alarm üretilir.

### Algılanan Anomali Türleri

- `SPIKE_EWMA`
- `SPIKE_SEASONAL`
- `ONE_SIDED`
- `LOW_DEMAND_CROWD`

Bu yaklaşım, hem ani kalabalık oluşumlarını hem de anormal davranış kalıplarını yakalayarak karar destek sağlar.

## 3.6 Sensör Sağlık İzleme

Sensör verisinin güvenilirliği sistem performansının kritik bir bileşenidir.  
Bu nedenle her sensör modülü için sağlık izleme mekanizması uygulanır.

Sağlık sistemi, sensörün veri üretim sürekliliğini ve veri davranışını analiz eder.

### Sağlık Kontrolleri

**1) Offline Detection**  
Belirli süre veri gelmeyen sensörler offline olarak işaretlenir.

**2) Stuck Zero Detection**  
Uzun süre sıfır değer üreten sensörler hatalı kabul edilir.

**3) Stuck Constant Detection**  
Sabit değer üreten sensörler arızalı veya saturasyon durumunda olabilir.

**4) Outlier Module Detection**  
Aynı alandaki sensörlerin medyan davranışına göre uç değer üreten sensörler tespit edilir.

### Algılanan Sağlık Alarm Türleri

- `SENSOR_OFFLINE`
- `STUCK_ZERO`
- `STUCK_CONST`
- `OUTLIER_MODULE`

Bu mekanizma, hatalı sensör verisinin füzyon ve anomali sonuçlarını bozmasını önler ve bakım planlamasına katkı sağlar.

## 3.7 Troubleshooting

Aşağıdaki sorun giderme rehberi, sistemin kurulum ve çalışma sürecinde karşılaşılabilecek yaygın hataları ve çözüm yollarını özetler.

---

### Python / Environment Hataları

**Hata:** `python is not recognized`  
**Sebep:** Python PATH’e ekli değil veya yanlış terminal kullanılıyor  
**Çözüm:** Anaconda Prompt kullan veya Python PATH’i ayarla

**Hata:** `ModuleNotFoundError`  
**Sebep:** Gerekli paketler kurulmamış  
**Çözüm:**  pip install -r requirements.txt

---

### MQTT / Mosquitto Hataları

**Hata:** `Connection refused`  
**Sebep:** MQTT broker çalışmıyor  
**Çözüm:** Mosquitto’yu verbose modda başlat  
---

### MQTT / Mosquitto Hataları

**Hata:** `Connection refused`  
**Sebep:** MQTT broker çalışmıyor  
**Çözüm:** Mosquitto’yu verbose modda başlat  

Start-Process "C:\Program Files\mosquitto\mosquitto.exe" -ArgumentList "-v"


**Hata:** ESP32 broker’a bağlanamıyor  
**Sebep:** MQTT_HOST yanlış (127.0.0.1 sensörde kullanılamaz)  
**Çözüm:** Laptop IPv4 adresini kullan  
ipconfig

### Dashboard Hataları

**Hata:** Dashboard açılıyor ama grafik boş  
**Sebep:** MQTT veri akışı yok  
**Çözüm:** Fake publisher çalıştır veya sensör publish ediyor mu kontrol et  

python src\fake_publisher.pyconfig

**Hata:** Veri gelmiyor  
**Sebep:** Topic uyuşmuyor  
**Çözüm:** Tüm bileşenlerde topic aynı olmalı:  
`piyon/v1/steps`

**Hata:** `ModuleNotFoundError: common`  
**Sebep:** Yanlış klasörden çalıştırma  
**Çözüm:** Repo root’tan çalıştır  

python src\dashboard.py

---

### Fake Veri Hataları

**Hata:** Sensör varken fake veri karışıyor  
**Sebep:** Fake publisher açık kaldı  
**Çözüm:** Fake terminali `Ctrl + C` ile kapat

---

### Sensör Entegrasyonu Hataları

**Hata:** ESP32 Wi-Fi bağlanmıyor  
**Sebep:** 5GHz ağ veya yanlış şifre  
**Çözüm:** 2.4GHz ağ kullan

**Hata:** JSON parse hatası / BAD_MSG  
**Sebep:** Veri şeması eksik veya yanlış tip  
**Çözüm:** StepPacket alanları eksiksiz olmalı  
- site_id  
- module_id  
- ts  
- window_s  
- steps_dir1  
- steps_dir2  

---

### Anomali Sistemi Hataları

**Hata:** Çok fazla alarm  
**Sebep:** Eşikler düşük  
**Çözüm:** anomaly.py içinde eşikleri artır

**Hata:** Hiç alarm yok  
**Sebep:** Eşikler yüksek  
**Çözüm:** anomaly.py eşiklerini düşür

---

### Sensör Sağlık Sistemi Hataları

**Hata:** SENSOR_OFFLINE yanlış alarm  
**Sebep:** Paket aralığı uzun  
**Çözüm:** offline süresini artır

**Hata:** STUCK_ZERO yanlış alarm  
**Sebep:** Gerçekten uzun süre trafik yok  
**Çözüm:** stuck_zero süresini artır

**Hata:** OUTLIER_MODULE yanlış alarm  
**Sebep:** Sensör kalibrasyonu farklı  
**Çözüm:** Eşik artır veya sensör kalibrasyonu yap

---

### Genel Sistem Hataları

**Hata:** Sistem çalışıyor ama veri yok  
**Sebep:** Broker kapalı / topic farklı / publisher yok  
**Çözüm:**  
1) Mosquitto açık mı kontrol et  
2) Topic aynı mı kontrol et  
3) Sensör veya fake veri publish ediyor mu kontrol et

**Hata:** Prosesler kapanmıyor  
**Sebep:** Arka planda python/mosquitto kaldı  
**Çözüm:**  

powershell -ExecutionPolicy Bypass -File .\scripts\stop_demo.ps1


## 4. Gelecek Çalışmalar

Bu çalışma, yaya akışının sensör tabanlı izlenmesi ve anomali tespiti için bir temel platform sunmaktadır.  
Gelecek çalışmalarda sistemin doğruluk, ölçeklenebilirlik ve karar destek kapasitesinin artırılması hedeflenmektedir.

### 1) Edge AI Entegrasyonu
Mevcut sistem istatistiksel anomali algılama yöntemleri kullanmaktadır.  
Gelecekte, derin öğrenme tabanlı yoğunluk tahmini ve davranış sınıflandırması algoritmalarının edge cihaz üzerinde çalıştırılması planlanmaktadır.

### 2) Dijital İkiz Modeli
Yaya akışının zamansal ve mekânsal davranışını temsil eden bir dijital ikiz geliştirilerek, gerçek zamanlı simülasyon ve senaryo analizi yapılabilir.  
Bu yaklaşım, tahliye planlaması ve kalabalık yönetimi için karar destek sağlayacaktır.

### 3) Çok Sensörlü Veri Füzyonunun Genişletilmesi
Piezo sensör verisine ek olarak kamera, BLE, Wi-Fi probe ve lidar gibi veri kaynaklarının entegre edilmesi ile yoğunluk tahmini doğruluğu artırılabilir.

### 4) Otonom Sensör Kalibrasyonu
Sensör sağlık sistemi, gelecekte otomatik kalibrasyon ve adaptif eşik ayarlama mekanizmaları ile geliştirilebilir.  
Bu sayede sensörler arası varyasyonun etkisi azaltılabilir.

### 5) Mekânsal Yoğunluk Haritalama
Birden fazla sensör noktasından elde edilen veriler kullanılarak gerçek zamanlı yoğunluk haritaları üretilebilir.  
Bu özellik, akıllı kampüs ve akıllı şehir uygulamalarında kullanılabilir.

### 6) Tahmine Dayalı Yoğunluk Analizi
Zaman serisi tahmin modelleri kullanılarak yoğunluk eğilimlerinin önceden öngörülmesi mümkündür.  
Bu yaklaşım, kalabalık oluşmadan önce önlem alınmasını sağlayabilir.

### 7) Bulut ve Edge Hibrit Mimari
Sistemin edge’de gerçek zamanlı analiz, bulutta ise uzun vadeli model eğitimi yapacak şekilde hibrit mimariye genişletilmesi planlanmaktadır.

Bu geliştirmeler, sistemin akıllı şehir altyapıları ve kalabalık yönetimi uygulamalarında daha geniş ölçekte kullanılmasına olanak sağlayacaktır.




