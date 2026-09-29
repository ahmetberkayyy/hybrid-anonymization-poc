# Hibrit Anonimleştirme PoC Çalışma Planı

## Amaç ve sınır

Türkçe sigortacılık metnindeki doğrudan tanımlayıcıları ve bağlama bağlı hassas ifadeleri bulup, metindeki yerlerini koruyarak maskeleyen yerel bir Python PoC hazırlanacak. Girdi düz metindir; taranmış belge ve OCR bu PoC kapsamına alınmaz. Test verileri bütünüyle sentetiktir. Üretim kullanımı için kurum verisiyle doğrulama ve hukuk/bilgi güvenliği onayı gerekir.

## Teslimatlar

1. `README.md`: kurulum, örnek çalıştırma, yöntem seçimi ve mimari diyagram.
2. `src/`: regex, isteğe bağlı Presidio ve NER/GLiNER algılayıcıları; çakışma çözümü; maskeleme; komut satırı arayüzü.
3. `data/`: kimlik, iletişim, adres, araç, poliçe/hasar ve sağlık örnekleri içeren küçük, etiketli sentetik Türkçe veri seti.
4. `tests/` ve ölçüm aracı: span/entity düzeyinde precision, recall, F1; örnek çıktı ve hatalar.
5. `docs/`: teknoloji ve entity/yöntem tabloları, kaynaklar, deney ortamı, gerçek test sonuçları, eksikler ve geliştirme önerileri.

## Uygulama sırası

### 1. Ölçüm zemini

- Tek bir entity sözlüğü tanımla: `PERSON`, `TCKN`, `IBAN`, `PHONE`, `EMAIL`, `VEHICLE_PLATE`, `POLICY_NUMBER`, `CLAIM_NUMBER`, `ADDRESS`, `HEALTH_INFORMATION` ve gerektiğinde alt türler.
- En az 12 sentetik Türkçe örnek oluştur. Gerçek kişi verisi kullanma. Karşı örnekler ekle: geçersiz TCKN/IBAN, genel hastalık bilgisi, poliçe/hasar numarası olmayan benzer kodlar.
- Örnekleri karakter başlangıç/bitiş konumları ve entity etiketleriyle kaydet. Aynı veri setini bütün yaklaşımlarda kullan.

### 2. Çalışan temel akış

- Python standart kütüphanesiyle regex ve doğrulama kurallarını uygula. TCKN ve IBAN için kontrol basamaklarını; telefon, plaka, poliçe ve hasar numaralarında bağlam/formatı açıkça belirt.
- Algılayıcıları ortak `EntitySpan` arayüzüne bağla. Farklı katmanlardan gelen örtüşen span'ları öncelik, doğrulama ve güven puanına göre birleştir.
- Maskeleri sağdan sola yerleştir; Türkçe kesme işareti ve ekleri koru. Çıktıda kaynak metni tekrar yazma veya loglama.
- CLI ile tek metin ve veri seti değerlendirmesi sağla.

### 3. Model ve servis karşılaştırması

- Presidio Analyzer/Anonymizer için Türkçe custom recognizer entegrasyonunu dene. Hazır Presidio algılayıcılarının Türkçe için otomatik olarak çalıştığını varsayma.
- Sabit entity sözlüklü bir Türkçe token-classification NER modelini ve GLiNER multilingual modelini aynı veri setiyle dene. Model kimliği, sürüm, lisans, eşik, CPU/GPU, bellek ve süreyi kaydet.
- İsteğe bağlı yerel LLM katmanı için yalnız belirsiz span'ları inceleyen, şema doğrulamalı bir arayüz tanımla. Yerel model sağlanmadıkça ölçülmüş başarı iddiasında bulunma.
- Regex, Presidio+regex, klasik NER ve GLiNER, hibrit birleşim sonuçlarını aynı ölçülerle karşılaştır.

### 4. Raporlama ve kabul koşulları

- Mimari diyagram, teknoloji karşılaştırma tablosu ve entity/yöntem tablosunu tamamla.
- Her yöntemde gerçek çalıştırma ile literatür/model kartı bilgisini ayrı göster. Çalıştırılamayan deneyleri `çalıştırılmadı` olarak işaretle ve nedenini yaz.
- Son raporda false positive/false negative örnekleri, Türkçe ekler, bağlamsal sağlık bilgisi, veri sızıntısı ve gecikme konularını değerlendir.
- Kabul: temiz kurulum yönergesi; çalışan CLI; etiketli test seti; tekrarlanabilir ölçüm komutu; örnekte beklenen maske; gözlem raporunda doğrulanabilir ortam ve sonuçlar.

## İlk teknik kararlar

- Tespit ve politika/maskeleme ayrı katmanlar olacak. Varsayılan PoC politikası saptanan entity'yi `<ENTITY>` ile değiştirecek.
- Kesin biçimli alanlar öncelikle doğrulamalı kurallarla; kişi/adres ve semantik sağlık alanları NER/GLiNER ile değerlendirilecek.
- Model çıktısı otomatik olarak doğru kabul edilmeyecek; overlap ve düşük güven durumları kaydedilecek. LLM, tek güvenlik bariyeri olmayacak.
- Belgedeki `12345678901` örneği checksum açısından ayrıca değerlendirilecek. Demo ile doğrulama kuralı arasındaki fark açıkça raporlanacak.

## İlerleme durumu

- Tamamlandı: sentetik 17 örnek ve 23 span, regex/doğrulama akışı, çakışma çözümü, maskeleme, CLI, temel testler, mimari ve kaynaklı karşılaştırma.
- Tamamlandı: Presidio 2.2.364 ile custom recognizer, Presidio Anonymizer ve regex+Presidio karşılaştırması.
- Tamamlandı: ModernBERT-TR PII ağırlıklarıyla Türkçe NER ve regex+Presidio+NER ölçümü; yapısal model çıktısı doğrulaması ve çakışma düzeltmesi.
- Tamamlandı: GLiNER multilingual v2.1 ve dört katmanlı hibrit ölçümü; 17 sentetik örnekte yöntem ve hata karşılaştırması.
- Sonraki adım: bağımsız, kör Türkçe test kümesi; hedef ortamda GPU/bellek ölçümü; kurum poliçe biçimleri; yerel LLM modeli sağlanırsa gerçek ikinci kontrol deneyi.
