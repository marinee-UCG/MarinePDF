# MarinePDF RAG Asistanı — Uygulama Planı

> **Uygulama şekli:** Kodu ve klasörleri **kullanıcı** yazar/oluşturur. Claude süpervizör:
> her task'a başlarken kavramı anlatır, kullanıcı yazar, Claude review eder. Adımlar `- [ ]`
> checkbox'lı; her task bir commit ile biter.

**Goal:** HiMSEN H21/32 jeneratör manueline (Vol I) İngilizce soru sorulup, kaynak (section +
sayfa) gösteren cevap alınabilen bir RAG uygulaması.

**Architecture:** Tek seferlik ingest script'i PDF'i okur, Korece'yi temizler, chunk'lar,
embed eder ve Postgres+pgvector'e yazar. FastAPI `/ask` soruyu embed edip en yakın chunk'ları
bulur, Groq LLM'e kaynaklı cevap ürettirir. Streamlit sadece API'yi çağıran bir chat arayüzü.

**Tech Stack:** Python 3.11, PyMuPDF, sentence-transformers (`BAAI/bge-small-en-v1.5`),
PostgreSQL 16 + pgvector, SQLAlchemy 2.x, pydantic-settings, FastAPI, Groq SDK, Streamlit,
pytest, Docker Compose.

**Spec:** `2026-11-18-marinepdf-rag-design.md` (repoda `docs/design.md`)

## Global Constraints

- Python **3.11** (Docker imajı `python:3.11-slim`). Local.de 3.14 de var ama torch uyumsuzluğu
  çıkabilir → venv'i 3.11 ile kur.
- `data/` ve `.env` **asla** commit'lenmez. `.env.example` commit'lenir.
- Embedding boyutu **384**. Model `BAAI/bge-small-en-v1.5`, `normalize_embeddings=True`.
- Sorgu embed edilirken prefix: `"Represent this sentence for searching relevant passages: "`
  (bge modelleri bunu bekler; chunk'lara prefix **eklenmez**).
- Chunk: `chunk_size=800`, `overlap=150` karakter; chunk sayfa sınırını aşmaz.
- Temizlikten sonra 50 karakterden kısa sayfalar atlanır.
- Retrieval: cosine distance, varsayılan `top_k=5`.
- PDF okuma: **PyMuPDF** (pdfplumber bu PDF'te sayfa başı ~1 sn; v2'de tablo için saklı).
- Tüm kod, commit mesajları, README İngilizce.

## Review Focus

1. **Manuelde olmayan soru** ("What is the capital of France?") → "I could not find this in
   the manual." gibi bir cevap, uydurma değil. → Task 6 testleri.
2. **Ingest'in iki kez çalıştırılması** → chunk'lar çiftlenmez. → Task 4 doğrulama adımı.
3. **Boş / sadece boşluk soru** → API 422 döner, UI'da hata mesajı. → Task 7 testi.
4. **Groq API key yok / Groq erişilemez** → API 503 + anlaşılır mesaj; UI çökmez. → Task 6-7.
5. **Section kodu olmayan sayfa** (kapak, s.1) → `section_code=None`, sonraki sayfalar önceki
   section'ı miras alır, çökme yok. → Task 1 testi.

---

## Dosya Yapısı

```
MarinePDF/
├── .gitignore  .env.example  requirements.txt  README.md  docker-compose.yml
├── data/                       # gitignored, PDF'ler burada
├── docs/design.md
├── backend/
│   ├── __init__.py
│   ├── config.py               # Settings
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── pdf_reader.py       # Page, clean_text, extract_section, read_pages
│   │   ├── chunker.py          # TextChunk, chunk_page, chunk_pages
│   │   ├── embedder.py         # Embedder
│   │   └── ingest.py           # CLI: python -m backend.ingestion.ingest data/x.pdf
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # engine, SessionLocal, init_db
│   │   └── models.py           # Document, Chunk
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py        # SearchHit, search
│   │   ├── prompt.py           # build_prompt
│   │   ├── llm.py              # LLMClient, GroqClient, get_llm, LLMError
│   │   └── service.py          # Answer, answer_question
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app
│   │   └── schemas.py          # AskRequest, AskResponse, SourceOut
│   └── Dockerfile
├── frontend/
│   ├── app.py
│   └── Dockerfile
└── tests/
    ├── test_pdf_reader.py  test_chunker.py  test_prompt.py
    ├── test_service.py     test_api.py
```

Mevcut boş `backend/pdf.py` silinir (yerini `backend/ingestion/pdf_reader.py` alır).

---

### Task 0: Repo iskeleti

**Files:** Create: `.gitignore`, `.env.example`, `requirements.txt`, `README.md`,
`docs/design.md`, tüm `__init__.py`'ler

- [ ] **Step 1:** `git init`; Python 3.11 ile `.venv` oluştur ve aktive et.
- [ ] **Step 2:** `.gitignore`: `data/`, `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`
- [ ] **Step 3:** `.env.example`:
  `DATABASE_URL=postgresql+psycopg://marine:marine@localhost:5432/marinepdf`,
  `GROQ_API_KEY=`, `LLM_PROVIDER=groq`, `LLM_MODEL=llama-3.3-70b-versatile`,
  `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`, `API_URL=http://localhost:8000`
  → kopyasını `.env` yap.
- [ ] **Step 4:** `requirements.txt`: `pymupdf`, `sentence-transformers`, `sqlalchemy`,
  `psycopg[binary]`, `pgvector`, `pydantic-settings`, `fastapi`, `uvicorn[standard]`, `groq`,
  `streamlit`, `requests`, `pytest`, `httpx` → `pip install -r requirements.txt`
- [ ] **Step 5:** Klasörleri ve `__init__.py`'leri oluştur; design doc'u `docs/design.md`'ye
  kopyala; README'ye 2 satırlık proje tanımı.
- [ ] **Step 6: Doğrula:** `git status` çıktısında `data/` ve `.env` **görünmüyor**.
- [ ] **Step 7: Commit:** `chore: project skeleton`

---

### Task 1: PDF okuma + temizleme + section

**Files:** Create `backend/ingestion/pdf_reader.py`, Test `tests/test_pdf_reader.py`

**Interfaces — Produces:**
- `@dataclass Page: page_number: int; text: str; section_code: str | None; section_title: str | None`
- `clean_text(raw: str) -> str`
- `extract_section(raw: str) -> tuple[str | None, str | None]`
- `read_pages(pdf_path: str | Path) -> list[Page]`

- [ ] **Step 1: Failing testler**

```python
def test_clean_text_removes_korean():
    raw = "분해 절차 Loosening Procedure"
    assert clean_text(raw) == "Loosening Procedure"

def test_clean_text_drops_empty_lines_and_collapses_spaces():
    assert clean_text("일반 사항\n  Engine   Stopping  \n\n") == "Engine Stopping"

def test_extract_section_from_header():
    raw = "All type Page\n1/2\nSection No. Rev.\nNormal Operation Engine Stopping\nO02700 1A\n..."
    assert extract_section(raw) == ("O02700", "Normal Operation Engine Stopping")

def test_extract_section_missing_returns_none():
    assert extract_section("HYUNDAI\nINSTRUCTION BOOK\nVOLUME") == (None, None)
```

- [ ] **Step 2:** `pytest tests/test_pdf_reader.py -v` → FAIL (import hatası)
- [ ] **Step 3: `clean_text`** — Hangul regex `[가-힣ᄀ-ᇿ㄰-㆏]+` ile
  sil, her satırda çoklu boşluğu teke indir + strip, boş satırları at, `"\n"` ile birleştir.
- [ ] **Step 4: `extract_section`** — Sadece **ilk 8 satıra** bak (temizlenmiş). Satır
  `^([A-Z]\d{5})\s+\w{1,3}$` ile eşleşirse kod = grup 1, başlık = **bir önceki satır**.
  (Gerçek PDF'te 382 sayfanın 381'i bu kalıpta.)
- [ ] **Step 5: `read_pages`** — `fitz.open(path)`, her sayfa `page.get_text()`. Section
  ham metinden çıkarılır; bulunamazsa önceki sayfanınki miras alınır. `clean_text` sonrası
  < 50 karakterse sayfa listeye eklenmez. `page_number` 1'den başlar.
- [ ] **Step 6:** `pytest tests/test_pdf_reader.py -v` → 4 PASS
- [ ] **Step 7: Gerçek PDF ile doğrula** (geçici bir script ya da `python -c`):
  `read_pages("data/IM_2 DIESEL GENERATOR ENGINE VOL I_Vol.1.pdf")` → ~380 sayfa; 101. sayfa
  `section_code == "G09500"`; metinde Hangul yok. Birkaç saniyede bitmeli.
- [ ] **Step 8: Commit:** `feat: pdf reader with korean cleanup and section metadata`

---

### Task 2: Chunk'lama

**Files:** Create `backend/ingestion/chunker.py`, Test `tests/test_chunker.py`

**Interfaces:** Consumes `Page`. Produces:
- `@dataclass TextChunk: page_number: int; section_code: str | None; section_title: str | None; content: str`
- `chunk_page(page: Page, chunk_size: int = 800, overlap: int = 150) -> list[TextChunk]`
- `chunk_pages(pages: list[Page], chunk_size: int = 800, overlap: int = 150) -> list[TextChunk]`

- [ ] **Step 1: Failing testler**

```python
def test_short_page_is_single_chunk():
    p = Page(5, "Short text.", "G00100", "Contents")
    assert [c.content for c in chunk_page(p)] == ["Short text."]

def test_long_page_split_with_limits_and_overlap():
    text = " ".join(f"Sentence number {i}." for i in range(200))
    chunks = chunk_page(Page(1, text, None, None), chunk_size=800, overlap=150)
    assert len(chunks) > 1
    assert all(len(c.content) <= 800 for c in chunks)
    assert chunks[0].content[-50:] in chunks[1].content   # overlap var

def test_metadata_copied_to_every_chunk():
    p = Page(42, "x. " * 1000, "M31000", "Piston")
    assert {(c.page_number, c.section_code) for c in chunk_page(p)} == {(42, "M31000")}
```

- [ ] **Step 2:** `pytest tests/test_chunker.py -v` → FAIL
- [ ] **Step 3:** Implement. Yaklaşım: metni pencere pencere kes; kesim noktasını pencerenin
  sonuna en yakın `"\n"`, yoksa `". "`, yoksa boşluğa çek; sonraki pencere `bitiş - overlap`'tan
  başlasın. Sonsuz döngüye dikkat: her adımda başlangıç ilerlemeli.
- [ ] **Step 4:** `pytest tests/test_chunker.py -v` → 3 PASS
- [ ] **Step 5: Gerçek PDF:** `chunk_pages(read_pages(...))` → toplam chunk sayısını ve 2-3
  örnek chunk'ı yazdır, gözle kontrol et (cümle ortasından kesiliyor mu?).
- [ ] **Step 6: Commit:** `feat: page-bounded text chunker with overlap`

---

### Task 3: Postgres + pgvector + SQLAlchemy modelleri

**Files:** Create `docker-compose.yml` (şimdilik sadece `db`), `backend/config.py`,
`backend/db/database.py`, `backend/db/models.py`

**Interfaces — Produces:**
- `class Settings(BaseSettings)`: `database_url: str`, `groq_api_key: str = ""`,
  `llm_provider: str = "groq"`, `llm_model: str`, `embedding_model: str`,
  `api_url: str = "http://localhost:8000"`; `get_settings() -> Settings` (`@lru_cache`)
- `engine`, `SessionLocal`, `init_db() -> None`
- `Document`: `id`, `filename (unique)`, `page_count`, `created_at`; `chunks` relationship
  (`cascade="all, delete-orphan"`)
- `Chunk`: `id`, `document_id (FK, ondelete CASCADE)`, `page_number`, `section_code`,
  `section_title`, `content (Text)`, `embedding (Vector(384))`

- [ ] **Step 1:** `docker-compose.yml` → servis `db`: imaj `pgvector/pgvector:pg16`,
  env `POSTGRES_USER=marine`, `POSTGRES_PASSWORD=marine`, `POSTGRES_DB=marinepdf`, port
  `5432:5432`, named volume `pgdata`. → `docker compose up -d db`
- [ ] **Step 2:** `config.py`, `database.py`, `models.py`. `init_db()`:
  önce `CREATE EXTENSION IF NOT EXISTS vector` (`text()` ile), sonra
  `Base.metadata.create_all(engine)`.
- [ ] **Step 3: Doğrula:** `python -c "from backend.db.database import init_db; init_db()"`;
  `docker compose exec db psql -U marine -d marinepdf -c "\d chunks"` → `embedding vector(384)`
  kolonu görünüyor.
- [ ] **Step 4: Commit:** `feat: postgres + pgvector schema with sqlalchemy`

---

### Task 4: Embedding + ingest CLI

**Files:** Create `backend/ingestion/embedder.py`, `backend/ingestion/ingest.py`

**Interfaces:** Consumes `read_pages`, `chunk_pages`, `SessionLocal`, `init_db`, modeller.
Produces:
- `class Embedder`: `__init__(model_name: str)`; `embed_documents(texts: list[str], batch_size: int = 32) -> list[list[float]]`;
  `embed_query(text: str) -> list[float]` (Global Constraints'teki prefix'i ekler)
- `ingest_pdf(pdf_path: Path, session: Session, embedder: Embedder) -> int` (yazılan chunk sayısı)
- CLI: `python -m backend.ingestion.ingest "data/IM_2 DIESEL GENERATOR ENGINE VOL I_Vol.1.pdf"`

- [ ] **Step 1: Embedder** — `SentenceTransformer(model_name)`; `encode(...,
  normalize_embeddings=True, show_progress_bar=True)`, sonuçları `.tolist()`.
- [ ] **Step 2: Hızlı kontrol:** `len(Embedder(...).embed_query("lube oil pressure")) == 384`
- [ ] **Step 3: `ingest_pdf`** — aynı `filename`'li `Document` varsa sil (cascade chunk'ları
  da siler) → yeni `Document` + tüm `Chunk`'lar → tek `commit`. `main()` argparse ile path alır,
  `init_db()` çağırır, sonunda "Ingested N chunks from X" yazdırır.
- [ ] **Step 4: Çalıştır:** CLI → bitiyor, N yazdırıyor.
- [ ] **Step 5: İdempotentlik (Review Focus #2):** CLI'yi **tekrar** çalıştır →
  `SELECT count(*) FROM chunks;` ilk çalıştırmadaki N ile aynı.
- [ ] **Step 6: Commit:** `feat: embed chunks and ingest pdf into pgvector`

---

### Task 5: Retrieval

**Files:** Create `backend/rag/retriever.py`

**Interfaces:** Produces
- `@dataclass SearchHit: content: str; page_number: int; section_code: str | None; section_title: str | None; distance: float`
- `search(session: Session, query_embedding: list[float], top_k: int = 5) -> list[SearchHit]`

- [ ] **Step 1:** Implement: `select(Chunk, Chunk.embedding.cosine_distance(q).label("distance")).order_by("distance").limit(top_k)`
- [ ] **Step 2: Kalite kontrolü** (geçici script): şu 3 soru için top-5'in section/sayfasını
  yazdır ve gözle değerlendir:
  - "How do I loosen a hydraulic screw?" → G09500 civarı beklenir
  - "Engine stopping procedure" → O02700 beklenir
  - "Turbocharger maintenance" → M80000 beklenir
  Sonuç kötüyse chunk boyutunu (Task 2) ayarla, tekrar ingest et.
- [ ] **Step 3: Commit:** `feat: cosine similarity retrieval`

---

### Task 6: Prompt + LLM + servis

**Files:** Create `backend/rag/prompt.py`, `backend/rag/llm.py`, `backend/rag/service.py`;
Test `tests/test_prompt.py`, `tests/test_service.py`

**Interfaces:** Consumes `SearchHit`, `search`, `Embedder`. Produces:
- `build_prompt(question: str, hits: list[SearchHit]) -> str`
- `class LLMError(Exception)`; `class LLMClient(Protocol): def generate(self, prompt: str) -> str`;
  `class GroqClient` (hata durumunda `LLMError` fırlatır); `get_llm(settings: Settings) -> LLMClient`
- `NOT_FOUND_MESSAGE = "I could not find this in the manual."`
- `@dataclass Answer: answer: str; sources: list[SearchHit]`
- `answer_question(question: str, session: Session, embedder: Embedder, llm: LLMClient, top_k: int = 5, max_distance: float = 0.4) -> Answer`

- [ ] **Step 1: Failing testler**

```python
# test_prompt.py
def test_prompt_contains_context_and_citation_labels():
    hits = [SearchHit("Clean seat and threads.", 101, "G09500", "Hydraulic Screw Tightenings", 0.2)]
    p = build_prompt("How to loosen?", hits)
    assert "Clean seat and threads." in p
    assert "G09500" in p and "101" in p
    assert "How to loosen?" in p

def test_prompt_instructs_grounding():
    p = build_prompt("q", [])
    assert NOT_FOUND_MESSAGE in p          # LLM'e "bulamazsan tam olarak bunu söyle" talimatı

# test_service.py — sahte embedder/llm/search kullan (monkeypatch)
def test_no_relevant_hits_returns_not_found_without_calling_llm(monkeypatch): ...
    # search tüm hit'leri distance > max_distance döndürsün → answer == NOT_FOUND_MESSAGE,
    # sources == [], FakeLLM.generate hiç çağrılmamış
def test_relevant_hits_passed_to_llm_and_returned_as_sources(monkeypatch): ...
    # FakeLLM "ANSWER" döndürsün → answer == "ANSWER", len(sources) == hit sayısı
def test_llm_error_propagates(monkeypatch): ...
    # FakeLLM LLMError fırlatsın → pytest.raises(LLMError)
```

- [ ] **Step 2:** `pytest tests/test_prompt.py tests/test_service.py -v` → FAIL
- [ ] **Step 3: `build_prompt`** — Her hit `[Section {code} – {title}, page {n}]\n{content}`
  formatında; talimatlar: sadece bağlamı kullan, bağlamda yoksa tam olarak `NOT_FOUND_MESSAGE`
  yaz, kullandığın section ve sayfaları belirt.
- [ ] **Step 4: `GroqClient`** — `groq.Groq(api_key=...)`,
  `chat.completions.create(model=settings.llm_model, messages=[...], temperature=0.1)`.
  API key boşsa veya istek hata verirse `LLMError` (Review Focus #4). `get_llm` provider
  `"groq"` değilse `ValueError`.
- [ ] **Step 5: `answer_question`** — embed_query → search → `distance <= max_distance`
  olanları filtrele → hiç kalmadıysa LLM çağırmadan `NOT_FOUND_MESSAGE` → değilse prompt +
  generate. (`0.4`: Task 5 ölçümü — ilgili sorular 0.17–0.28, alakasız sorular 0.47+.)
- [ ] **Step 6:** testler → 5 PASS
- [ ] **Step 7: Gerçek uçtan uca:** Groq'tan ücretsiz key al, `.env`'e yaz; terminalden
  "How do I loosen a hydraulic screw?" → kaynaklı cevap; "What is the capital of France?" →
  `NOT_FOUND_MESSAGE` (Review Focus #1).
- [ ] **Step 8: Commit:** `feat: grounded answer generation with groq`

---

### Task 7: FastAPI

**Files:** Create `backend/api/schemas.py`, `backend/api/main.py`; Test `tests/test_api.py`

**Interfaces:** Consumes `answer_question`, `get_llm`, `Embedder`, `SessionLocal`. Produces:
- `AskRequest(question: str = Field(min_length=3, max_length=1000), top_k: int = Field(5, ge=1, le=20))`
  + `question`'ı strip eden validator
- `SourceOut(section_code, section_title, page_number, snippet: str)` (snippet = content'in ilk 300 karakteri)
- `AskResponse(answer: str, sources: list[SourceOut])`
- `GET /health` → `{"status": "ok", "db": "ok" | "error"}`; `POST /ask` → `AskResponse`

- [ ] **Step 1: Failing testler** (`TestClient` + FastAPI `dependency_overrides` ile sahte
  embedder/llm/session; `answer_question`'ı monkeypatch'le)

```python
def test_ask_returns_answer_and_sources(client): ...   # 200, body["answer"], body["sources"][0]["page_number"]
def test_blank_question_rejected(client):
    assert client.post("/ask", json={"question": "   "}).status_code == 422
def test_llm_error_returns_503(client): ...             # answer_question LLMError fırlatsın → 503, "detail" anlaşılır
def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
```

- [ ] **Step 2:** `pytest tests/test_api.py -v` → FAIL
- [ ] **Step 3:** Implement. Embedder ve LLM uygulama açılırken **bir kez** yaratılsın
  (`lifespan`); `get_db`, `get_embedder`, `get_llm_client` dependency'leri. `LLMError` →
  `HTTPException(503, "LLM service unavailable: ...")`.
- [ ] **Step 4:** testler → 4 PASS; `pytest` (tümü) → hepsi PASS
- [ ] **Step 5: Elle:** `uvicorn backend.api.main:app --reload` → `http://localhost:8000/docs`
  üzerinden `/ask` dene.
- [ ] **Step 6: Commit:** `feat: fastapi ask and health endpoints`

---

### Task 8: Streamlit arayüzü

**Files:** Create `frontend/app.py`

**Interfaces:** Consumes HTTP `POST {API_URL}/ask` → `AskResponse` JSON. DB veya backend
modüllerini **import etmez**.

- [ ] **Step 1:** Implement: başlık "⚓ MarinePDF — HiMSEN H21/32 Assistant";
  `st.session_state.messages` ile geçmiş; `st.chat_input` → `requests.post(..., timeout=60)`;
  cevap `st.chat_message("assistant")`; kaynaklar `st.expander("Sources")` içinde
  `**{code} – {title}** (p. {page})` + snippet.
- [ ] **Step 2:** Hatalar: bağlantı hatası → `st.error("API is not reachable...")`;
  422 → "Please enter a longer question."; 503 → "LLM service is unavailable, try again."
- [ ] **Step 3: Elle:** API açıkken `streamlit run frontend/app.py` → 3 soru sor, kaynaklar
  görünüyor. API'yi kapat → çökme yok, hata mesajı var (Review Focus #4).
- [ ] **Step 4: Commit:** `feat: streamlit chat ui`

---

### Task 9: Tam Docker Compose

**Files:** Create `backend/Dockerfile`, `frontend/Dockerfile`; Modify `docker-compose.yml`

- [ ] **Step 1:** `backend/Dockerfile`: `python:3.11-slim`, requirements kur, kodu kopyala,
  `CMD uvicorn backend.api.main:app --host 0.0.0.0 --port 8000`. Torch'un CPU sürümü için
  `pip install torch --index-url https://download.pytorch.org/whl/cpu` önce çalıştırılsın
  (imajı GB'larca küçültür).
- [ ] **Step 2:** `frontend/Dockerfile`: `python:3.11-slim`, `streamlit` + `requests`,
  `CMD streamlit run frontend/app.py --server.address 0.0.0.0`.
- [ ] **Step 3:** Compose: `api` (port 8000, `env_file: .env`, `DATABASE_URL` host'u `db`
  olarak override, `depends_on: db` + db healthcheck `pg_isready`, `./data:/app/data:ro`
  volume), `ui` (port 8501, `API_URL=http://api:8000`).
- [ ] **Step 4: Doğrula:** `docker compose up --build` →
  `docker compose exec api python -m backend.ingestion.ingest "data/IM_2 DIESEL GENERATOR ENGINE VOL I_Vol.1.pdf"`
  → `http://localhost:8501`'de soru-cevap çalışıyor.
- [ ] **Step 5: Commit:** `feat: dockerize api and ui`

---

### Task 10: README cilası

**Files:** Modify `README.md`

- [ ] **Step 1:** Bölümler: problem (gemi mühendisinin manuelde bilgi araması), demo GIF,
  mimari diyagram (design doc'taki), tech stack, quick start (`.env` + `docker compose up` +
  ingest komutu), "Bring your own manual" notu (telif nedeniyle PDF repoda yok), design
  decisions (neden pgvector, neden Korece temizliği, neden bge-small), roadmap (v2 tablo
  çıkarma, v3 deploy, Vol II/OCR).
- [ ] **Step 2:** Demo GIF kaydet (ScreenToGif gibi), `docs/demo.gif`.
- [ ] **Step 3: Doğrula:** Temiz bir klasöre `git clone` → README'deki adımlarla çalışıyor.
- [ ] **Step 4: Commit + GitHub'a push.**
