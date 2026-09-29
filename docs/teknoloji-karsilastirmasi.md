# Teknoloji ve yöntem karşılaştırması

Bu tablo ürün belgeleri ve model kartlarına dayanır; `deney-raporu.md` içindeki çalıştırma sonuçlarıyla karıştırılmamalıdır. CPU/GPU sütunu bir gereksinim tahmini değil, desteklenen çalışma biçimini belirtir. Gerçek kaynak tüketimi için hedef donanımda ölçüm gerekir.

ModernBERT-TR PII model kartı yaklaşık 150 milyon parametre ve kendi 300 belgeli testinde örtüşme esaslı micro-F2 sonucu bildirir. GLiNER multilingual v2.1 kartı yaklaşık 209 milyon parametre bildirir. Bu yayımlanmış metrikler PoC'nin tam span eşleşmeli F1 ölçüsüyle doğrudan karşılaştırılamaz.

| Yöntem | Çalışma mantığı | Türkçe ve özel entity | CPU/GPU ve on-prem | Güçlü taraf | Sınır |
|---|---|---|---|---|---|
| Regex + checksum | Desen, bağlam sözcüğü ve kontrol basamağı | Türkçe bağlam ve kurum formatı elle yazılır | CPU; tamamen yerel | Açıklanabilir, hızlı, kararlı | İma edilen sağlık bilgisi ve serbest biçimler kaçabilir |
| Presidio Analyzer/Anonymizer | Recognizer sonuçlarını toplar, sonra seçilen operatörle anonimleştirir | Custom recognizer ve dil konfigürasyonu gerekir; Türkçe hazır PII kapsamasını varsaymamak gerekir | CPU ile yerel kurulabilir; bağlı NER ayrıca kaynak ister | Tek API ile regex, checksum, bağlam ve harici modeller | Türkçe ve sigorta entity'leri için uyarlama ve test gerekir |
| Klasik Türkçe NER | Sabit BIO/token etiketleriyle span tahmini | ModernBERT-TR PII 25 sınıf içerir; poliçe/hasar sınıfları modelde yok | PyTorch/ONNX ile yerel CPU veya uygun GPU; performans ölçülmeli | Kişi ve adres gibi biçimsiz alanlarda yardımcı | Etiket kümesi sabit; domain kayması ve token sınırı hatası |
| GLiNER multilingual v2.1 | Sorgu anında verilen label'larla span çıkarır | Özel sigorta etiketleri eğitim olmadan denenebilir; Türkçe başarısı ayrıca ölçülmeli | Yerel PyTorch CPU/GPU; ağırlık ve gecikme hedef donanımda ölçülmeli | Hızlı taxonomy denemesi | Sıfır atış başarısı/threshold hassas; format doğrulaması yapmaz |
| MedNER-TR | Tıbbi token sınıflandırması | Hastalık, ilaç, semptom, organ, test; sigorta kimlikleri yok | Yerel CPU/GPU; ölçülmeli | Tıbbi terimlerde aday katman | Model kartındaki yüksek iç skor küçük kontrollü teste dayanır |
| BERTurk genel NER | Sabit kişi/kurum/yer sınıfları | Türkçe kişi adı için ikinci baseline; sigorta taxonomy'si yok | Yerel CPU/GPU; ölçülmeli | Basit genel NER karşılaştırması | Sağlık ve yapısal PII kapsamı sınırlı |
| Yerel LLM | Belirsiz aday span'ın bağlamla doğrulanması ve JSON kararı | Kurum terimleri prompt ile tarif edilebilir | On-prem mümkündür; model boyutuna göre bellek/GPU ve gecikme artar | Dolaylı bağlamı inceleyebilir | Halüsinasyon, değişkenlik, prompt injection; tek karar kaynağı olmamalı |

## Entity ve birincil tespit yöntemi

| Entity | Öncelikli yöntem | İkinci kontrol / politika notu |
|---|---|---|
| TCKN | Regex + kontrol basamağı | Geçersiz ama güçlü `TC kimlik` bağlamlı değer de güvenli tarafta maskelenir; ayrı raporlanır |
| IBAN | Regex + MOD 97 | Boşluk varyantları; geçersiz kodu IBAN sayma |
| Telefon, e-posta | Regex / Presidio recognizer | Yerel yazım biçimleri ve yanlış pozitifler test edilmeli |
| Araç plakası | TR format kuralı | İl kodu/harf/rakam ve bağlam; özel plaka biçimleri eklenmeli |
| Poliçe, hasar no | Kurum formatlı Presidio custom recognizer / regex | Kurum içi format kataloğu ve bağlam sözcüğü gerekli |
| Kişi | Türkçe PII/NER + bağlam | Ad ile şehir/kurum çakışmaları; Türkçe ek sınırları |
| Adres | Türkçe PII/NER + yapı ipuçları | Mahalle, cadde, numara ve serbest adres ifadeleri |
| Hastalık, ilaç, tıbbi test | Medikal NER / Türkçe PII + sözlük | Kişiye bağlı sağlık durumu ile genel bilgi ayrılmalı |
| Alkol durumu, promil | Promil için kural; durum için GLiNER/domain NER | Salt imadan özellik türetme; belirsizde yerel doğrulama |

## Yöntem farkları

- **Yalnız regex:** TCKN, IBAN ve kurumsal kodlarda güçlü; serbest kişi, adres ve dolaylı sağlık ifadelerinde sınırlı.
- **Yalnız NER:** Biçimsiz span'ları yakalayabilir; TCKN/IBAN kontrol basamağını ve kurum formatını kendiliğinden garanti etmez.
- **Hibrit:** Doğrulanabilir biçimleri kuralda tutup biçimsiz alanları modelle tamamlar. Çakışma çözümü, eşik ayarı ve gözlemleme maliyeti doğurur.

## Sağlık ve sigorta için politika önerisi

İlk aşamada `HEALTH_INFORMATION` gibi geniş bir etiket yerine hastalık, ilaç, test sonucu, engellilik ve alkol gibi alt türler ayrı span'lar olarak toplanmalı; çıktı politikası kurumun kullanım amacına göre `MASK`, `TOKENIZE`, `LOCAL_ONLY` veya `BLOCK` seçmelidir. Örneğin “diyabet hastası” ifadesi yalnız `PERSON` maskesiyle korunmuş olmaz. Poliçe/hasar numaraları kişiyi dolaylı tanımlayabileceği için maskelenmeli veya kontrollü token'a dönüştürülmelidir. Bu kararlar hukuk/KVKK ve bilgi güvenliği ekibinin sınıflandırmasına tabidir.

## Birincil kaynaklar

- [Presidio text anonymization](https://microsoft.github.io/presidio/text_anonymization/)
- [Presidio supported entities](https://microsoft.github.io/presidio/supported_entities/)
- [Presidio NLP model customization](https://github.com/data-privacy-stack/presidio/blob/main/docs/analyzer/customizing_nlp_models.md)
- [Presidio anonymizer operators](https://microsoft.github.io/presidio/anonymizer/)
- [GLiNER kaynak kodu ve modeller](https://github.com/urchade/GLiNER/blob/main/docs/intro.md)
- [GLiNER multilingual v2.1 model kartı](https://huggingface.co/urchade/gliner_multi-v2.1)
- [ModernBERT-TR PII model kartı](https://huggingface.co/ytu-ce-cosmos/modernbert-tr-pii-ner)
- [ModernBERT-TR PII etiket konfigürasyonu](https://huggingface.co/ytu-ce-cosmos/modernbert-tr-pii-ner/raw/main/config.json)
- [MedNER-TR model kartı](https://huggingface.co/tugrulkaya/medner-tr)
- [BERTurk genel NER model kartı](https://huggingface.co/savasy/bert-base-turkish-ner-cased)
- [Ollama yerel API ve yapılandırılmış çıktı](https://github.com/ollama/ollama/blob/main/docs/api.md)
