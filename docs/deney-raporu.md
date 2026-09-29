# PoC deney ve gözlem raporu

## Ortam ve yöntem

- Tarih: 28–29 Eylül 2026
- Ortam: Windows 11, Python 3.12.14 sanal ortamı. Standart kütüphane testleri ayrıca Python 3.14.2 ile çalıştı.
- Ekran kartı: NVIDIA GeForce RTX 3060 Laptop GPU, 6 GiB VRAM (`nvidia-smi`). Kurulu PyTorch 2.14.0+cpu sürümü CUDA kullanmıyor; NER ölçümü CPU ile yapıldı.
- Veri: `data/synthetic_tr.jsonl`; 17 sentetik metin, 23 etiketli span. Geliştirme veri setidir; bağımsız test değildir.
- Ölçü: başlangıç, bitiş ve entity adının tam eşleşmesi. Aynı veri ve eşik (`0.5`) bütün motorlar için kullanılacaktır.

| Motor | Durum | TP | FP | FN | Precision | Recall | F1 | Not |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Regex/kurallar | Çalıştırıldı | 19 | 0 | 4 | 1.000 | 0.826 | 0.905 | Dar bağlam dışındaki 4 örneği kaçırdı |
| Presidio custom recognizer | Çalıştırıldı | 10 | 0 | 13 | 1.000 | 0.435 | 0.606 | Yalnız yapısal desenler tanımlı; sürüm 2.2.364 |
| Regex + Presidio | Çalıştırıldı | 19 | 0 | 4 | 1.000 | 0.826 | 0.905 | Bu küçük kümede Presidio kural dışı yeni span eklemedi |
| ModernBERT-TR PII NER + format kontrolü | Çalıştırıldı | 7 | 2 | 16 | 0.778 | 0.304 | 0.438 | CPU; tam span eşleşmesi |
| Regex + Presidio + Türkçe NER | Çalıştırıldı | 19 | 0 | 4 | 1.000 | 0.826 | 0.905 | Kural span'larını koruyan çakışma önceliği |
| GLiNER multilingual v2.1 + format kontrolü | Çalıştırıldı | 10 | 2 | 13 | 0.833 | 0.435 | 0.571 | CPU; özel label'lar; doğrulama sonrası |
| Regex + Presidio + Türkçe NER + GLiNER | Çalıştırıldı | 22 | 0 | 1 | 1.000 | 0.957 | 0.978 | Geliştirme kümesinde ayarlanmış kurallar |
| Yerel LLM ikinci kontrol | Adapter sahte yanıtla doğrulandı; model çalıştırılmadı | — | — | — | — | — | — | Yerel model/uç nokta sağlanmadı |

## Gözlemler

- İlk ölçümde boşluklu IBAN desenindeki hane sayısı nedeniyle 1 kaçırma vardı; desen düzeltildi. Daha zor 4 örnek eklenince kural katmanı 23 etiketin 19'unu buldu.
- Kaçırılanlar: bağlamsız kişi adı, kuruma özgü alternatif poliçe biçimi, dolaylı sağlık ifadesi ve HbA1c ölçümü. Model katmanlarının katacağı değeri bu örnekler sınayacak.
- İstekteki `12345678901` geçerli TCKN değildir. Açık “TC kimlik” bağlamında maskeleme yapılıyor; bağlamsız aynı sayı maskelenmiyor.
- Kişi adı kuralı yalnız belirli “Ad Soyad'ın TCKN...” biçimini yakalıyor. Sağlık sözlüğü dolaylı durum anlatımını anlayamaz.
- Maskelenen span'dan sonraki Türkçe ek korunuyor. Örnekteki plaka son eki kaynak metindeki gibi `'tür` kalıyor.
- Skorlar çok küçük ve kolay sentetik kümeye ait olduğundan model karşılaştırması veya üretim doğruluğu olarak kullanılmamalı.
- Presidio 2.2.364 ile ilk çalıştırma, `NoOpNlpEngine` için `models` konfigürasyonu eksik olduğundan hata verdi. Türkçe için açık boş NLP konfigürasyonu eklenince analyzer çalıştı.
- Presidio Anonymizer `replace` operatörüyle örnek metin maskelendi. Presidio-only koşusu kişi/adres/sağlık kurallarını içermediği için regex-only koşusundan düşük kapsamlıdır; bu sayılar Presidio ürününün genel kalitesini sıralamaz.
- `benchmark_results.json` süreleri bütün 17 metnin tek işlemde çalışmasına aittir: regex 0.001 sn, Presidio ilk yükleme dahil 1.415 sn, ardından regex+Presidio önbellek ısınmışken 0.002 sn. Bu sıra ve önbellek etkisi nedeniyle donanım/üretim gecikme karşılaştırması değildir.
- ModernBERT-TR PII ağırlıkları 29 Eylül'de indirildi ve 17 örneğin tamamında çalıştırıldı. İlk format filtresi öncesinde 7 TP, 4 FP, 16 FN görüldü. Kısmi e-posta ve geçersiz IBAN parçaları gibi yapısal hatalar filtrelenince FP 2'ye düştü. Kişi ve sağlık ifadelerinde kaçırmalar sürdü.
- İlk birleşik koşuda NER'ın eksik adres span'ı kuralın tam span'ını bastırdı ve sonuç 18 TP'ye geriledi. Kaynak önceliği düzeltildikten sonra birleşim 19 TP'ye döndü; bu veri setinde NER yeni doğru span katmadı.
- Kurulu sürümler: GLiNER 0.2.29, Transformers 5.16.1 ve PyTorch 2.14.0+cpu. İlk GLiNER indirme denemesi otomatik onay incelemesinin kullanım sınırına takıldı; bildirilen yeniden deneme saatinden sonra indirme ve gerçek ölçüm tamamlandı.

### 29 Eylül GLiNER devamı

- Otomatik onay incelemesinin bildirdiği yeniden deneme saatinden sonra GLiNER ağırlıkları indirildi. İlk yükleme eksik `protobuf` nedeniyle durdu; bağımlılık eklendikten sonra model gerçek metinde ve 17 örneğin tamamında çalıştı.
- İlk GLiNER koşusu 10 TP, 8 FP, 13 FN; ilk tam hibrit koşusu 20 TP, 6 FP, 3 FN verdi. `Sigortalı`/`Sürücü` gibi rol adlarını `PERSON`, “kan şekeri” ve engellilik oranını `BAC_VALUE` sayma hataları görüldü.
- Model kaynaklı `PERSON` için çok sözcüklü özel ad koşulu, `BAC_VALUE` için promil biçimi doğrulaması ve bilinen sağlık terimlerinde kural span önceliği eklendi. Sonuçlar tabloda gösterilmiştir. Bunlar aynı geliştirme veri setinden öğrenilen kararlar olduğu için bağımsız başarı tahmini değildir.
- Son hibrit koşusunda tek kaçırılan span “kan şekeri ölçümü” idi. Bu, dolaylı sağlık bilgisinin hâlâ eksik kaldığını gösterir.
- GLiNER yüklenirken Transformers, `mdeberta-v3-base` tokenizer'ının regex örüntüsü için uyarı verdi. Model çalıştı; tokenizer uyumluluğu ve farklı sürümle sonuç değişimi ayrıca doğrulanmalıdır.

## Sonraki deney kapıları

1. En az 100 ayrı, kör ve farklı yazım biçimli Türkçe örnekle sonucu yeniden sınamak; kurum verisi kullanılacaksa kontrollü etiketleme yapmak.
2. Sağlık ve alkol için kişiyle ilişkili durum ile genel bilgi ayrımını; poliçe/hasar için gerçek kurum formatlarını eklemek.
3. GPU destekli PyTorch ve tokenizer uyumluluğunu hedef ortamda sınayıp soğuk/ısınmış gecikme ile RAM/VRAM tüketimini ölçmek.
4. Yerel LLM modeli sağlandığında adapter ile ikinci kontrolü ölçmek; span sınırı metinden tekrar doğrulansın, ham metin kurum dışına çıkmasın.
