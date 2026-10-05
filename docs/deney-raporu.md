# PoC deney ve gözlem raporu

## Ortam ve yöntem

- Son ölçüm: 2 Ekim 2026.
- Ortam: Windows 11 ve Python 3.12 sanal ortamı.
- Ekran kartı: NVIDIA GeForce RTX 3060 Laptop GPU, 6 GiB VRAM. Mevcut PyTorch kurulumu CPU sürümüdür; NER ve GLiNER ölçümleri CPU üzerinde yapılmıştır.
- Veri: `data/synthetic_tr.jsonl`; 110 sentetik metin, 121 etiketli span, 92 pozitif ve 18 negatif örnek.
- Sınıflar: PERSON, TCKN, IBAN, PHONE, EMAIL, VEHICLE_PLATE, POLICY_NUMBER, CLAIM_NUMBER, ADDRESS, HEALTH_INFORMATION ve BAC_VALUE.
- Ölçü: `start`, `end` ve entity sınıfının tam eşleşmesi. Kısmi span eşleşmesi doğru sayılmaz.
- Ortak kabul eşiği: `0.5`.
- Bu küme geliştirme sırasında görüldüğü için bağımsız veya kör test kümesi değildir.

## Veri dağılımı

| Entity | Altın etiket |
|---|---:|
| HEALTH_INFORMATION | 22 |
| PERSON | 17 |
| POLICY_NUMBER | 11 |
| VEHICLE_PLATE | 10 |
| PHONE | 10 |
| CLAIM_NUMBER | 10 |
| ADDRESS | 10 |
| TCKN | 9 |
| EMAIL | 9 |
| IBAN | 7 |
| BAC_VALUE | 6 |
| **Toplam** | **121** |

Veri setinde boşluklu ve bitişik biçimler, Türkçe ekler, büyük/küçük harf çeşitleri, üç sözcüklü kişi adları, farklı poliçe ve hasar numarası biçimleri, dolaylı sağlık anlatımları, birden fazla entity içeren sigorta notları ve yanlış pozitifleri ölçen zor negatifler bulunur.

## Modül sonuçları

| Motor | TP | FP | FN | Precision | Recall | F1 | Süre (sn) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Regex/kurallar | 80 | 9 | 41 | 0.899 | 0.661 | 0.762 | 0.005 |
| Presidio custom recognizer | 63 | 0 | 58 | 1.000 | 0.521 | 0.685 | 9.262 |
| Regex + Presidio | 80 | 9 | 41 | 0.899 | 0.661 | 0.762 | 0.014 |
| ModernBERT-TR PII NER + format kontrolü | 27 | 17 | 94 | 0.614 | 0.223 | 0.327 | 5.700 |
| Regex + Presidio + Türkçe NER | 88 | 14 | 33 | 0.863 | 0.727 | 0.789 | 5.602 |
| GLiNER multilingual v2.1 + format kontrolü | 46 | 21 | 75 | 0.687 | 0.380 | 0.489 | 19.718 |
| **Regex + Presidio + Türkçe NER + GLiNER** | **100** | **20** | **21** | **0.833** | **0.826** | **0.830** | **19.562** |
| Yerel LLM ikinci kontrol | Model kurulumu bekleniyor | — | — | — | — | — | — |

Makine tarafından üretilen ayrıntılı sonuç `docs/benchmark_results.json` dosyasındadır. Süreler koşu sırasından, model önbelleğinden ve ilk yükleme maliyetinden etkilenir; üretim gecikmesi ölçümü olarak değerlendirilmemelidir.

## Tam hibrit entity sonuçları

| Entity | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS | 3 | 12 | 7 | 0.200 | 0.300 | 0.240 |
| BAC_VALUE | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| CLAIM_NUMBER | 9 | 0 | 1 | 1.000 | 0.900 | 0.947 |
| EMAIL | 9 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| HEALTH_INFORMATION | 11 | 7 | 11 | 0.611 | 0.500 | 0.550 |
| IBAN | 7 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| PERSON | 16 | 1 | 1 | 0.941 | 0.941 | 0.941 |
| PHONE | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| POLICY_NUMBER | 10 | 0 | 1 | 1.000 | 0.909 | 0.952 |
| TCKN | 9 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| VEHICLE_PLATE | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Gözlemler

- İlk 17 örnekteki 0.978 hibrit F1 skoru kolay ve küçük geliştirme kümesinden kaynaklanıyordu. Çeşitlilik ve zor negatifler eklendiğinde hibrit F1 0.830 oldu; bu daha gerçekçi bir PoC sinyalidir.
- TCKN, IBAN, telefon, e-posta, plaka, promil ve standart kurum numarası biçimlerinde doğrulamalı kurallar güçlü sonuç verdi.
- En büyük açık ADDRESS sınıfıdır. Modeller tam adres yerine il, ilçe veya cümlenin daha geniş/dar parçalarını seçebildiği için tam span metriğinde 12 FP ve 7 FN oluştu.
- HEALTH_INFORMATION sınıfında sözlük terimleri yüksek kesinlik sağlarken dolaylı hastalık, ilaç, test sonucu ve tedavi anlatımları kaçırıldı. Genel sağlık cümleleri de yanlış pozitif üretebildi.
- Presidio custom recognizer yanlış pozitif üretmedi ancak yalnız tanımlı yapısal desenleri kapsadığı için recall 0.521'de kaldı.
- ModernBERT kişi ve bazı yapısal PII sınıflarında katkı sağladı; sigortacılığa özel numaralar ile geniş sağlık sınıfında düşük kapsam gösterdi.
- GLiNER kişi ve semantik sınıflarda yeni doğru span'lar ekledi, ancak adres ve sağlık ifadelerinde sınır/sınıf hataları nedeniyle 22 yanlış pozitif üretti.
- Tam hibrit yapı 121 altın etiketin 100'ünü buldu. Çakışma çözümü yapısal ve kural tabanlı span'ları koruduğu için tek başına model koşularından daha dengeli sonuç verdi.
- `12345678901` matematiksel olarak geçerli TCKN değildir. Açık “TC kimlik” bağlamında hassas değer olarak maskelenir; bağlamsız kullanım negatif örnektir.
- Veri üreticisi checksum geçerli sentetik TCKN ve IBAN biçimleri üretir, benzersiz ID ve konumları doğrular. Dataset testleri her entity sınıfı için minimum örnek sayısını korur.

## Yerel LLM durumu

Qwen3 4B için adapter hazırdır. İkinci kontrol yalnız risk işareti taşıyan metinlerde çalışır, JSON şemalı yanıt ister, düşünme çıktısını kapatır ve yalnız kaynak metinde tek kez birebir bulunan alıntıları kabul eder. “Sigortalı”, “sürücü”, “eksper” ve “doktor” gibi roller PERSON olarak kod seviyesinde reddedilir.

Ollama ve `qwen3:4b` ağırlığı henüz kurulmadığı için gerçek local LLM TP/FP/FN ölçümü rapora eklenmemiştir. Model kurulduğunda analiz notebook'u local LLM'yi bağımsız ve hibrit koşuda ayrı ölçer.

## Sonraki deney kapıları

1. Qwen3 4B kurulduktan sonra local LLM bağımsız ve hibrit ölçümlerini kaydetmek.
2. ADDRESS için adres sınırı normalizasyonu ve il/ilçe/sokak bileşenlerini birleştiren son işlem geliştirmek.
3. HEALTH_INFORMATION için kişiye bağlılık ve olumsuzluk bilgisini koruyan sağlık ontolojisi veya özel NER modeli değerlendirmek.
4. Kuruma ait gerçek poliçe ve hasar numarası biçimlerini konfigürasyondan yönetmek.
5. Geliştirme sırasında görülmemiş, kurum onaylı ve elle etiketli ayrı bir kör test kümesi oluşturmak.
6. GPU destekli hedef ortamda soğuk/ısınmış gecikme, RAM ve VRAM kullanımını ölçmek.
