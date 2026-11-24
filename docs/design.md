# MarinePDF — Jeneratör Manueli RAG Asistanı (Tasarım)

Tarih: 2026-11-18

## 1. Amaç ve Neden

Gemi makine mühendisi olarak domain'e özgü bir portfolyo projesi. Kullanıcı, HiMSEN H21/32
dizel jeneratör manueline İngilizce soru sorar (arıza giderme, bakım prosedürü, yedek parça,
operasyon verisi); sistem manueldeki ilgili bölümleri bulup bir LLM ile **kaynak gösteren** bir
cevap üretir.

İki hedef:
1. **Öğrenmek:** RAG hattının her katmanını (PDF okuma → chunk → embedding → vector DB →
   arama → LLM) kullanıcı kendisi yazarak öğrenir.
2. **Göstermek:** GitHub'da recruiter'ların görebileceği, temiz, çalıştırılabilir bir proje.

## 2. Çalışma Şekli (önemli kısıt)

- **Kodu kullanıcı yazar, klasörleri kullanıcı oluşturur.** Claude süpervizör: kavramı anlatır,
  adımı tarif eder, yazılan kodu review eder, takılınca ipucu verir. Hazır çözüm yazmaz
  (kullanıcı özellikle isterse küçük örnek snippet olabilir).
- Her aşama bitince çalışır durumda olmalı ve bir git commit ile kapanmalı.

## 3. Kapsam

**Hedefler (v1)**
- Vol I PDF'inin (382 sayfa, metin tabanlı) okunması
- Korece metnin ayıklanması, sadece İngilizce'nin tutulması
- Her chunk'a sayfa no + section kodu/başlığı metadata'sı
- Postgres + pgvector'de saklama, SQLAlchemy ile erişim
- FastAPI `/ask` endpoint'i: soru → cevap + kaynaklar
- Streamlit chat arayüzü, cevabın altında kaynaklar (section, sayfa)
- Docker Compose ile tek komutla çalıştırma
- README: mimari diyagram, kurulum, demo GIF, roadmap

**Hedef dışı (v1'de yok, roadmap'e girer)**
- Vol II ve OCR (taranmış sayfalar)
- Tabloların yapılandırılmış çıkarılması (parça listeleri) → v2
- Canlı deploy (Streamlit Cloud + Render + Supabase) → v3
- Kullanıcı girişi, çoklu kullanıcı, PDF upload arayüzü

**Anti-hedefler (çalışsa bile başarısızlık sayılır)**
- LLM'in manuelde olmayan bilgiyi uydurması, kaynak göstermemesi
- Manuel PDF'inin GitHub'a yüklenmesi (Hyundai telifi)
- API key'in repoya commit'lenmesi

## 4. Kısıtlar

- Kullanıcının CPU'su güçlü değil → LLM localde çalışmaz (Ollama yok). LLM API üzerinden.
- Embedding modeli küçük olduğu için localde CPU'da çalışabilir.
- Her şey ücretsiz olmalı.
- Manuel iki sütunlu Korece/İngilizce; PDF okuyucu iki dili aynı satırda birleştiriyor.

## 5. Değerlendirilen Yaklaşımlar

**PDF okuma**
- **A) Vol I, sadece metin, Hangul temizliği, section metadata — SEÇİLDİ.** En hızlı uçtan uca
  sonuç; tablolar düz metin olarak girer (kabul edilen kalite kaybı).
- B) A + pdfplumber ile tablo çıkarma — v2'ye ertelendi.
- C) İki cilt + OCR — fazla yavaş/karmaşık, v1 için reddedildi.

**LLM**
- Ollama (local) — CPU yetersiz, reddedildi.
- **Groq ücretsiz API — SEÇİLDİ (Claude'un önerisi, kesinleşme LLM aşamasında).** Hızlı,
  OpenAI uyumlu API, deploy'da değişiklik gerektirmez.
- Gemini — alternatif; Google'a özgü SDK.

**Vector DB**
- Ayrı vector DB (Chroma, Qdrant) — ikinci bir servis demek.
- **Postgres + pgvector — SEÇİLDİ.** Zaten Postgres var; tek DB, SQLAlchemy ile hem metadata
  hem vektör.

## 6. Mimari

```
            ┌──────────────┐   HTTP    ┌──────────────┐   SQL    ┌─────────────────────┐
 Kullanıcı →│  Streamlit   │ ───────→  │   FastAPI    │ ──────→  │ Postgres + pgvector │
            │   (ui)       │ ←───────  │   (api)      │ ←──────  │      (db)           │
            └──────────────┘           └──────┬───────┘          └─────────▲───────────┘
                                              │ HTTPS                      │
                                              ▼                            │
                                         Groq LLM API          ┌───────────┴──────────┐
                                                               │ ingest script (CLI)  │
                                                               │ PDF→temizle→chunk→   │
                                                               │ embed→DB'ye yaz      │
                                                               └──────────────────────┘
```

Docker Compose'da 3 servis: `db` (`pgvector/pgvector:pg16` imajı), `api`, `ui`.
Ingest, `api` container'ı içinde tek seferlik komutla çalışır.

## 7. Bileşenler

### 7.1 Ingestion (tek seferlik script)
1. **Okuma:** pdfplumber ile sayfa sayfa metin.
2. **Temizleme:** Hangul karakterlerini (Unicode `가-힣`, `ᄀ-ᇿ`,
   `㄰-㆏`) regex ile sil; fazla boşlukları sadeleştir; boş kalan satırları at.
3. **Metadata:** Sayfa başlığından section kodu (ör. `G09500`, `A42000` → regex
   `[A-Z]\d{5}`) ve section başlığı çıkarılır. Bulunamazsa önceki sayfanınki kullanılır.
4. **Chunk:** Sayfa metni ~800 karakter / ~150 karakter overlap ile bölünür (paragraf ve
   cümle sınırlarına saygı göstererek). Chunk bir sayfayı aşmaz → kaynak sayfa net kalır.
5. **Embedding:** `sentence-transformers`, model `BAAI/bge-small-en-v1.5` (384 boyut,
   CPU'da hızlı, İngilizce'de güçlü).
6. **Kayıt:** Toplu (batch) insert. Aynı dosya tekrar ingest edilirse önce eski kayıtlar
   silinir (idempotent).

### 7.2 Veritabanı şeması
- `documents`: id, filename, title, page_count, created_at
- `chunks`: id, document_id (FK), page_number, section_code, section_title, content,
  embedding `vector(384)`
- Arama: cosine distance (`<=>`) ile top-k. v1'de index opsiyonel (chunk sayısı
  birkaç bin, sıralı tarama yeterli); HNSW index öğrenme adımı olarak eklenebilir.

### 7.3 Retrieval + LLM
- Soru aynı modelle embed edilir → top-k=5 chunk.
- Prompt: "Sadece verilen bağlamı kullan; cevap bağlamda yoksa 'manuelde bulamadım' de;
  kullandığın section ve sayfaları belirt."
- LLM katmanı tek bir arayüzün arkasında (`generate(prompt) -> str`); sağlayıcı `.env`'deki
  `LLM_PROVIDER` ile seçilir. Böylece Groq ↔ Gemini değişimi tek satır.

### 7.4 API (FastAPI)
- `GET /health` → servis + DB durumu
- `POST /ask` → body `{question: str, top_k?: int}` → `{answer: str, sources: [{section_code,
  section_title, page_number, snippet}]}`
- Pydantic modelleri ile request/response doğrulama.

### 7.5 UI (Streamlit)
```
┌───────────────────────────────────────────────┐
│ ⚓ MarinePDF — HiMSEN H21/32 Assistant          │
├───────────────────────────────────────────────┤
│ 🧑 What is the tightening procedure for ...    │
│ 🤖 According to the manual, ...                │
│    ▸ Sources: G09500 Hydraulic Screw           │
│      Tightenings (p.101), ...                  │
├───────────────────────────────────────────────┤
│ [ Ask a question about the engine...     ] ⏎  │
└───────────────────────────────────────────────┘
```
- `st.chat_message` / `st.chat_input` ile sohbet; kaynaklar açılır-kapanır (`st.expander`).
- UI sadece API'yi çağırır, DB'ye veya LLM'e doğrudan erişmez.

### 7.6 Konfigürasyon
- `.env` (commit'lenmez) + `.env.example` (commit'lenir): `DATABASE_URL`, `GROQ_API_KEY`,
  `LLM_PROVIDER`, `EMBEDDING_MODEL`, `API_URL`.
- `pydantic-settings` ile okunur.
- `.gitignore`: `data/`, `.env`, `__pycache__/`, `.venv/`.

### 7.7 Test
- `pytest` ile saf fonksiyonlar: Hangul temizleme, section kodu çıkarma, chunk'lama.
- API için `/health` ve `/ask` (LLM mock'lanarak) testleri.

## 8. Aşamalar (öğrenme sırası)

| # | Aşama | Bitti sayılır, eğer… |
|---|-------|----------------------|
| 0 | Repo iskeleti: git, venv, `.gitignore`, klasörler, README taslağı | İlk commit atıldı, `data/` git'te görünmüyor |
| 1 | PDF okuma + temizleme + metadata | Bir sayfanın temiz İngilizce metni ve section kodu yazdırılıyor; testler geçiyor |
| 2 | Chunk'lama | Tüm Vol I chunk'lanıyor, sayı/örnek kontrol edildi; testler geçiyor |
| 3 | Docker'da Postgres + pgvector, SQLAlchemy modelleri | Tablolar oluşuyor |
| 4 | Embedding + DB'ye yazma (ingest script) | Tüm chunk'lar vektörüyle DB'de |
| 5 | Arama (retrieval) | Bir soru için mantıklı top-5 chunk dönüyor |
| 6 | LLM entegrasyonu (Groq) | Soru → kaynaklı cevap terminalde |
| 7 | FastAPI | `/ask` Swagger'dan (`/docs`) çalışıyor |
| 8 | Streamlit | Chat arayüzünden soru-cevap |
| 9 | Docker Compose (3 servis) | `docker compose up` ile her şey ayağa kalkıyor |
| 10 | README cilası: diyagram, GIF, roadmap | Repo public'e hazır |

## 9. Builder'a bırakılanlar
- Klasör/dosya isimleri ve modül yapısı (kullanıcı oluşturur; Claude review'da yorum yapar)
- Chunk boyutu ince ayarı (800/150 başlangıç değeri, aşama 5'te kalite görülünce ayarlanır)
- Groq'ta hangi Llama modeli (aşama 6'da güncel ücretsiz modellere bakılır)

## 10. Claude'un verdiği kararlar (kullanıcı kontrol etsin)
- Ingest'in API endpoint değil CLI script olması (daha basit; upload v1 hedef dışı)
- Embedding modeli `bge-small-en-v1.5`
- Chunk'ların sayfa sınırını aşmaması
- Testler için `pytest`, config için `pydantic-settings`
- Aşama sırası (önce local Python, Docker'da sadece DB; tam Compose en sonda)
