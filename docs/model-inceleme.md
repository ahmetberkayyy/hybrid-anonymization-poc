# Presidio, Türkçe NER ve GLiNER incelemesi

Bu belge mimari ve model kartı incelemesidir. Gerçek PoC ölçümleri yalnız [deney raporunda](deney-raporu.md) ve makinece üretilen `benchmark_results.json` dosyasında yer alır.

## Presidio

Presidio Analyzer, farklı `recognizer` çıktılarının metin konumlarını ve skorlarını toplar. `PatternRecognizer` regex desenleriyle; özel recognizer kodu checksum veya kurum veritabanıyla çalışabilir. NLP engine aracılığıyla NER bağlanabilir. Anonymizer tespit edilen konumlarda `replace`, `redact`, `mask`, `hash` veya şifreleme gibi operatörleri uygular. PoC, Türkçe için `NoOpNlpEngine` ve custom pattern recognizer seçer; bu tercih Presidio'nun hazır İngilizce NLP modelini yanlışlıkla Türkçe çalıştırmaz. Metin sonunda hem Presidio anonymizer hem Python maskeleyici seçilebilir. [Analyzer mimarisi](https://github.com/data-privacy-stack/presidio/blob/main/docs/analyzer/index.md), [recognizer geliştirme](https://github.com/data-privacy-stack/presidio/blob/main/docs/analyzer/developing_recognizers.md), [anonimleştirme operatörleri](https://microsoft.github.io/presidio/anonymizer/).

**Türkçe sınır:** Presidio'nun çok dilli çalışması konfigürasyon ve ilgili dilde recognizer/model gerektirir. Kurumun TCKN, plaka, poliçe ve hasar kuralları burada tanımlanmalıdır. Semantik “kanında etanol saptandı” gibi içerik custom regex ile güvenilir biçimde çözülemez. [Dil konfigürasyonu](https://github.com/data-privacy-stack/presidio/blob/main/docs/analyzer/languages.md), [NLP modeli özelleştirme](https://github.com/data-privacy-stack/presidio/blob/main/docs/analyzer/customizing_nlp_models.md).

## Sabit etiketli Türkçe NER

Token classification modelinde her token `B-`, `I-` veya dışarıda (`O`) etiketi alır; token parçaları bir span'a birleştirilir. PoC adayı [ModernBERT-TR PII](https://huggingface.co/ytu-ce-cosmos/modernbert-tr-pii-ner) Türkçe için 25 KVKK odaklı sınıf bildirir. Gerçek [etiket konfigürasyonu](https://huggingface.co/ytu-ce-cosmos/modernbert-tr-pii-ner/raw/main/config.json) `KISI_AD_SOYAD`, `TCKN`, `TELEFON`, `EMAIL`, `ADRES`, `PLAKA`, `IBAN_TR`, `SAGLIK_BILGISI` içerir; poliçe ve hasar kimliği içermez. Bu yüzden model çıktısı PoC entity sözlüğüne açık eşlemeyle bağlanır. Kartın yayımladığı overlap micro-F2, burada kullanılan tam span F1 ile karşılaştırılamaz.

Genel kişi/kurum/yer baseline için [BERTurk NER](https://huggingface.co/savasy/bert-base-turkish-ner-cased) düşünülebilir. Tıbbi terimleri ayrı değerlendirmek için [MedNER-TR](https://huggingface.co/tugrulkaya/medner-tr) hastalık, ilaç, semptom, organ ve test etiketleri sunar. MedNER kartındaki yüksek iç test puanı küçük kontrollü kümeden gelir; sigorta hasar metni başarısı olarak yorumlanmamalıdır.

**Custom entity:** Hazır checkpoint sınıfları sabittir. Yeni `POLICY_NUMBER` veya `ALCOHOL_STATUS` için anotasyonla yeniden eğitim/fine-tuning ya da kural/GLiNER katmanı gerekir. CPU'da yerel inference mümkündür; GPU gecikmeyi azaltabilir. Gerçek RAM/VRAM ve süre PoC donanımında ayrıca ölçülmelidir.

## GLiNER multilingual v2.1

GLiNER aranacak etiketleri inference anında alır ve bu etiketler için span tahmin eder. `insurance policy number`, `medical condition`, `medication` gibi tanımlar PoC'ta prompt niteliğinde kullanılır; ağırlık eğitimi gerektirmeden yeni taxonomy denenebilir. [Model kartı](https://huggingface.co/urchade/gliner_multi-v2.1) multilingual v2.1 için yaklaşık 209 milyon parametre ve Apache 2.0 lisans bildirir; Türkçe sigorta için ayrı bir başarı garantisi bildirmez. [Kütüphane belgeleri](https://github.com/urchade/GLiNER/blob/main/docs/intro.md) yerel çalışma ve fine-tuning yolunu gösterir.

**Testte dikkat:** İngilizce veya Türkçe label metni, eşik (`0.35` aday üretimi; PoC ortak eşik `0.5`), cümle uzunluğu ve alan terimleri sonucu değiştirebilir. GLiNER'ın verdiği skor, Presidio veya klasik NER skoru ile kalibre edilmiş olasılık değildir. TCKN/IBAN çıktısı modelden gelse de format ve checksum yeniden kontrol edilmelidir. Üretim için yanlış negatif maliyeti ve CPU/GPU gecikmesi aynı test setinde karşılaştırılmalıdır.

## Yerel LLM ikinci kontrol

İlk iki katman belirsiz veya eksik bıraktığında yerel modelden yalnız `quote` ve `label` JSON çıktısı istenir. PoC'nin isteğe bağlı Ollama adapter'ı sunucu adresini `127.0.0.1:11434` ile sınırlar ve yalnız metinde birebir, tek kez görülen alıntıları kabul eder. Kesin kural eşleşmelerini LLM reddi ile kaldırmaz. LLM yanıtı her durumda şema, kaynak metin ve span sınırı doğrulamasından geçmelidir. [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md). Yerel model bulunmadığından gerçek kalite veya gecikme ölçümü yoktur.

## Deney protokolü

1. Model kimliği, sürümü ve ağırlık kaynağını sabitle; gerçek kişi verisi kullanma.
2. `data/synthetic_tr.jsonl` üzerinde regex, Presidio, ModernBERT-TR, GLiNER ve birleşimi ayrı çalıştır.
3. Tam span precision/recall/F1 ve etiket bazlı kırılımı kaydet. Yanlış pozitif/negatif metinlerini elle incele.
4. İlk yükleme süresi, ısınmış çıkarım süresi, CPU/GPU bellek, eşik ve uzun metin davranışını hedef donanımda ölç.
5. Geliştirme verisinden farklı, kurum onaylı kör test setiyle tekrarla; yalnız bu sonuç model seçimi için kullanılmalı.
