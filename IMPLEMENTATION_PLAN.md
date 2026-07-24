# Budget-Darpan — Complete Implementation Plan

> **Hackathon**: CodeFest 2026 | **Team**: Die Vordenker
> **Theme**: Local government budget transparency for Nepal
> **Duration**: 60 hours

> **Current implementation note (24 July 2026):** `README.md` is the authoritative build status and `AGENTS.md` is the local engineering contract. The later sections of this document preserve early product exploration; their illustrative municipalities and figures are not official data and must not be seeded or presented as facts. The implemented Phase 3A slice uses review-gated page chunks, hybrid Chroma/BM25-style retrieval, a direct typed provider layer, and the exact Ollama tag `qwen2.5:3b` rather than LangChain.

---

## 1. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.x + Django REST Framework |
| Database | SQLite |
| Frontend | React 18 + Vite + Tailwind CSS |
| Mobile | React Native (Expo) — future scope after the web demo is stable |
| Vector DB | ChromaDB (persistent, local); optional Pinecone deployment adapter later |
| Embeddings | Ollama `nomic-embed-text-v2-moe` (multilingual, ~100 languages) |
| Chat LLM | Ollama `qwen2.5:3b` with a deterministic evidence-safe fallback |
| RAG Framework | Direct typed vector-provider abstraction; no LangChain dependency |
| OCR | Tesseract 5 (`nep+eng` language pack) |
| Deployment | Render (Django backend + React static) |
| LLM Server | Ollama (localhost:11434) |

---

## 2. Directory Structure

```
budget-darpan/
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── budgets/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── filters.py
│   ├── chat/
│   │   ├── __init__.py
│   │   ├── engine.py          # Weight scoring + intent resolution
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── anomaly/
│   │   ├── __init__.py
│   │   ├── detector.py        # Rule-based anomaly engine
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── pipeline.py        # LangChain + ChromaDB + Ollama
│   │   ├── ingester.py        # Document ingestion
│   │   ├── retriever.py       # Query → embed → search → respond
│   │   ├── urls.py
│   │   └── views.py
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── pipeline.py        # Tesseract wrapper
│   │   └── management/commands/
│   │       ├── __init__.py
│   │       └── ocr_pdfs.py
│   ├── management/commands/
│   │   ├── __init__.py
│   │   ├── seed_data.py       # Seed 6 LGs + sectors + budget rows
│   │   └── ingest_docs.py     # OCR → chunk → embed → ChromaDB
│   ├── requirements.txt
│   ├── Dockerfile
│   └── render.yaml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   ├── SearchFilter.jsx
│   │   │   ├── BudgetTable.jsx
│   │   │   ├── SectorChart.jsx
│   │   │   ├── ChatWidget.jsx
│   │   │   ├── AnomalyBadge.jsx
│   │   │   └── MapView.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── LGDashboard.jsx
│   │   │   └── AnomalyReport.jsx
│   │   ├── i18n/
│   │   │   ├── en.json
│   │   │   └── np.json
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── chroma_db/                  # Created at runtime by ingestion
├── docs/                       # Budget PDFs/Markdown for RAG
├── README.md
└── AGENTS.md
```

---

## 3. Database Schema (SQLite via Django ORM)

```python
# budgets/models.py

class Province(models.Model):
    code = models.CharField(max_length=2, unique=True)
    name_en = models.CharField(max_length=100)
    name_np = models.CharField(max_length=100)

class District(models.Model):
    code = models.CharField(max_length=4, unique=True)
    name_en = models.CharField(max_length=100)
    name_np = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='districts')

class LocalGovernment(models.Model):
    LG_TYPES = [
        ('metro', 'महानगरपालिका'),
        ('sub_metro', 'उप-महानगरपालिका'),
        ('muni', 'नगरपालिका'),
        ('rural', 'गाउँपालिका'),
    ]
    code = models.CharField(max_length=10, unique=True)
    name_en = models.CharField(max_length=100)
    name_np = models.CharField(max_length=100)
    lg_type = models.CharField(max_length=10, choices=LG_TYPES)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='local_govs')
    total_budget = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

class FiscalYear(models.Model):
    year_np = models.CharField(max_length=9, unique=True)  # "२०८१/८२"
    year_en = models.CharField(max_length=9, unique=True)  # "2024/25"

class Sector(models.Model):
    code = models.CharField(max_length=6, unique=True)  # COFOG: 701-710
    name_en = models.CharField(max_length=100)
    name_np = models.CharField(max_length=100)

class BudgetAllocation(models.Model):
    BUDGET_TYPES = [
        ('recurrent', 'चालू'),
        ('capital', 'पुँजीगत'),
        ('financing', 'वित्तिय'),
    ]
    local_gov = models.ForeignKey(LocalGovernment, on_delete=models.CASCADE, related_name='budgets')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPES)
    allocated = models.DecimalField(max_digits=18, decimal_places=2)
    spent = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('local_gov', 'fiscal_year', 'sector', 'budget_type')
```

---

## 4. Seed Data: 6 Local Governments

| # | LG | Code | Type | Province | District | FY 2081/82 | FY 2082/83 | FY 2083/84 |
|---|-----|------|------|----------|----------|-----------|-----------|-----------|
| 1 | Kathmandu | 80401 | metro | Bagmati | Kathmandu | 25.63B | 25.80B | 25.88B |
| 2 | Pokhara | 80402 | metro | Gandaki | Kaski | 7.51B | 8.35B | 8.50B |
| 3 | Lalitpur | 80403 | metro | Bagmati | Lalitpur | 6.00B | 6.20B | 6.50B |
| 4 | Bhaktapur | 80404 | muni | Bagmati | Bhaktapur | 2.40B | 2.47B | 2.60B |
| 5 | Hetauda | 80405 | sub_metro | Bagmati | Makwanpur | 2.52B | 2.60B | 2.85B |
| 6 | Butwal | 80406 | sub_metro | Lumbini | Rupandehi | 1.50B | 1.60B | 1.70B |

Each LG has sector breakdowns for 5 sectors × 3 FYs × 2 budget types = 30 rows per LG = **180 total seed rows**.

**Sectors:**

| Code | English | नेपाली |
|------|---------|--------|
| 701 | Infrastructure Development | पूर्वाधार विकास |
| 702 | Social Development | सामाजिक विकास |
| 703 | Economic Development | आर्थिक विकास |
| 704 | Good Governance | सुशासन |
| 705 | Office Operations & Admin | कार्यालय सञ्चालन तथा प्रशासन |

> `ponytail: 5 broad sectors, not full COFOG. Expand if queries justify it.`

---

## 5. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/provinces/` | List provinces |
| GET | `/api/districts/?province=X` | List districts |
| GET | `/api/local-govs/?district=X&type=Y` | List LGs (filterable) |
| GET | `/api/sectors/` | List sectors (bilingual) |
| GET | `/api/fiscal-years/` | List fiscal years |
| GET | `/api/budgets/` | Budget data, filters: `lg`, `sector`, `fy`, `budget_type` |
| GET | `/api/budgets/summary/` | Aggregated: `?lg=X&fy=Y` → sector-wise totals |
| POST | `/api/chat/` | `{"query": "..."}` → `{intent, entities, response, source}` |
| GET | `/api/anomalies/` | Anomaly flags, filters: `lg`, `fy`, `severity` |
| POST | `/api/rag/query/` | `{"query": "..."}` → RAG response from budget docs |
| POST | `/api/rag/ingest/` | Trigger document re-ingestion |

---

## 6. Weighted Chat Engine — `chat/engine.py`

**Entity types and weights:**

```python
WEIGHTS = {
    'ANOMALY': 12,     # fraud, धांधली, irregular, suspicious, anomaly, असामान्य
    'LG': 10,          # kathmandu, pokhara, lalitpur, bhaktapur, hetauda, butwal
    'SECTOR': 8,       # education/शिक्षा, health/स्वास्थ्य, infrastructure/पूर्वाधार
    'COMPARE': 7,      # vs, compare, difference, तुलना
    'FY': 6,           # 2081, 2082, २०८१, २०८२
    'METRIC': 5,       # budget, spent, allocated, बजेट, खर्च, विनियोजन
    'BUDGET_TYPE': 4,  # recurrent/capital/चालू/पुँजीगत
}
```

**Algorithm:**

```
1. Normalize query (lowercase, strip punctuation)
2. Tokenize by whitespace
3. Match tokens against entity dictionaries (English + Nepali)
4. Score each matched entity type → sum weights
5. Bonus: LG+SECTOR pair → ×1.5 multiplier
6. Highest scoring combination → intent

Intents:
  - GET_BUDGET:      LG+SECTOR+FY present → fetch from DB
  - COMPARE:         COMPARE entity present → multi-LG or multi-sector query
  - ANOMALY_CHECK:   ANOMALY entity present → run detector
  - RAG_FALLBACK:    score < threshold (default: 12) → fall to RAG
```

**Sample queries and intents:**

| Query | Entities | Score | Intent | Response |
|-------|----------|-------|--------|----------|
| "kathmandu education budget 2082" | LG(10)+SECTOR(8)+FY(6) | 24 | GET_BUDGET | Kathmandu education: NPR 3.29B allocated, 53.8% spent |
| "pokhara ma infrastructure ma kati kharcha vayo?" | LG(10)+SECTOR(8)+METRIC(5) | 23 | GET_BUDGET | पोखरामा पूर्वाधारमा NPR X विनियोजित, Y% खर्च |
| "compare education budget of kathmandu and lalitpur" | COMPARE(7)+SECTOR(8)+LG(10)+LG(10) | 35 | COMPARE | Side-by-side comparison table |
| "any fraud in hetauda budget?" | ANOMALY(12)+LG(10) | 22 | ANOMALY_CHECK | Hetauda: admin bloat flag (27.84%), capital underspend |
| "what did budget speech say about education?" | SECTOR(8) | 8 | RAG_FALLBACK | Searches ChromaDB → "According to budget speech 2083/84..." |

---

## 7. Anomaly Detection — `anomaly/detector.py`

**Rules (applied per LG per FY per sector):**

| # | Rule | Condition | Severity | Flag Message |
|---|------|-----------|----------|-------------|
| 1 | Overspend | spent/allocated > 1.15 | 🟡 yellow, 🔴 red (>1.30) | "{sector} overspent by {X}%" |
| 2 | Severe underspend | spent/allocated < 0.40 | 🟡 yellow, 🔴 red (<0.20) | "{sector} severely underspent ({X}%)" |
| 3 | Admin bloat | admin sector % > 25% total | 🟡 yellow, 🔴 red (>35%) | "Admin costs {X}% of budget" |
| 4 | Capital starvation | capital budget % < 20% total | 🟡 yellow, 🔴 red (<10%) | "Capital spending only {X}% of budget" |
| 5 | YoY sector spike | \|sector_change\| > 40% | 🟡 yellow, 🔴 red (>60%) | "{sector} allocation changed {X}% YoY" |

**Output:**

```json
{
  "lg": "hetauda",
  "fy": "2081/82",
  "flags": [
    {"rule": "admin_bloat", "severity": "yellow", "message": "Admin costs 27.84% of total budget"},
    {"rule": "capital_starvation", "severity": "red", "message": "Capital spending only 10.78% of budget"}
  ],
  "score": 72
}
```

> `ponytail: hardcoded thresholds; tune if false positives emerge.`

---

## 8. OCR Pipeline — `ocr/pipeline.py`

**Prerequisites:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-nep
pip install pytesseract pdf2image pymupdf
```

**Flow:**

```
1. python manage.py ocr_pdfs
2. For each PDF in docs/:
   a. Convert PDF pages to images (pdf2image)
   b. Run Tesseract with --lang nep+eng
   c. Extract text + store in DocumentChunk model
3. python manage.py ingest_docs
   a. Read DocumentChunk rows
   b. Split into 500-char chunks (RecursiveCharacterTextSplitter)
   c. Prefix each chunk with "search_document: "
   d. Embed via Ollama nomic-embed-text-v2-moe
   e. Store in ChromaDB (persistent at chroma_db/)
```

**Input documents (pre-seeded):**
- Budget Speech FY 2083/84 (Nepali) — from bibstha/nepal-budget-2083-2084
- Budget Speech FY 2083/84 (English translation)
- Kathmandu Metro sectoral budget reports (from kathmandu.gov.np)
- MoFAGA budget summary table (scraped HTML)

> `ponytail: skip full OCR if pre-parsed text from bibstha/nepal-budget-2083-2084 covers demo needs.`

---

## 9. RAG Pipeline — `rag/pipeline.py`

**Dependencies:**
```bash
pip install langchain langchain-community langchain-chroma chromadb ollama
```

**Implementation:**

```python
# rag/pipeline.py
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

OLLAMA_BASE = "http://localhost:11434"
CHROMA_DIR = "chroma_db"
COLLECTION = "budget_docs"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text-v2-moe",
    base_url=OLLAMA_BASE
)

llm = ChatOllama(
    model="qwen2.5",          # Better Nepali support than llama3.2
    base_url=OLLAMA_BASE,
    temperature=0,
    num_predict=512
)

vectorstore = Chroma(
    collection_name=COLLECTION,
    embedding_function=embeddings,
    persist_directory=CHROMA_DIR
)

prompt_template = """You are a budget assistant for Nepal local government.
Answer using ONLY the context below. If unsure, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer (in the same language as the question):"""

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    chain_type_kwargs={"prompt": PromptTemplate.from_template(prompt_template)}
)

def answer_query(query: str) -> dict:
    result = qa.invoke(query)
    return {"response": result["result"], "source": "RAG"}
```

**Ingestion:**

```python
# rag/ingester.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

def ingest_documents():
    loader = DirectoryLoader("docs/", glob="**/*.md", loader_cls=TextLoader)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    for chunk in chunks:
        chunk.page_content = "search_document: " + chunk.page_content
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION
    )
    return len(chunks)
```

---

## 10. Chat Flow — End-to-End

```
User types in ChatWidget:
"kathmandu education budget 2082 ma kati kharcha vayo?"

1. POST /api/chat/ {query: "..."}
2. engine.py:
   - Tokenize: ["kathmandu", "education", "budget", "2082", "ma", "kati", "kharcha", "vayo"]
   - Match: LG(kathmandu=10), SECTOR(education=8), METRIC(budget=5, kharcha=5), FY(2082=6)
   - Score: LG+SECTOR+FY = 10+8+6 = 24 (×1.5 bonus = 36)
   - Intent: GET_BUDGET
3. Query DB:
   - BudgetAllocation.objects.filter(
       local_gov__name_en__iexact="kathmandu",
       sector__name_en__iexact="education",
       fiscal_year__year_en="2081/82"
     ).aggregate(Sum('allocated'), Sum('spent'))
4. Format response:
   "Kathmandu Metropolitan City allocated NPR 3,294,777,000 to education
    in FY 2081/82, of which 53.8% (NPR 1,773,442,000) has been spent."
5. Return to frontend → ChatWidget displays

If query was "what is the education policy for 2083?":
  - Score: SECTOR(education=8) = 8
  - Score < threshold(12) → RAG_FALLBACK
  - rag/pipeline.py answer_query("education policy 2083")
  - Embed query → ChromaDB search → top 3 chunks → LLM generate
  - Return RAG response
```

---

## 11. Frontend Components

| Component | File | Purpose |
|-----------|------|---------|
| `SearchFilter` | `components/SearchFilter.jsx` | Province → District → LG dropdown cascade, sector filter, FY select |
| `BudgetTable` | `components/BudgetTable.jsx` | Sortable table: Sector, Allocated, Spent, %Spent, AnomalyBadge |
| `SectorChart` | `components/SectorChart.jsx` | Bar chart (allocated vs spent per sector), pie chart (allocation distribution) |
| `ChatWidget` | `components/ChatWidget.jsx` | Toggleable sidebar, message list, input, typing indicator |
| `AnomalyBadge` | `components/AnomalyBadge.jsx` | 🟡/🔴 pill with tooltip |
| `MapView` | `components/MapView.jsx` | Province-level choropleth (leaflet or plain SVG) |

**Pages:**

| Page | Route | Content |
|------|-------|---------|
| Home | `/` | Search bar, summary stats, province map, sector pie chart |
| LGDashboard | `/lg/:code` | Full budget table, sector charts, anomaly flags, chat |
| AnomalyReport | `/anomalies` | List of all flags across LGs, filterable by severity |

**i18n (react-i18next):**

```json
// en.json
{
  "search.placeholder": "Search budgets, sectors, LGs...",
  "budget.allocated": "Allocated",
  "budget.spent": "Spent",
  "sector.education": "Education",
  "anomaly.flag": "Flag"
}

// np.json
{
  "search.placeholder": "बजेट, क्षेत्र, स्थानीय तह खोज्नुहोस्...",
  "budget.allocated": "विनियोजित",
  "budget.spent": "खर्च",
  "sector.education": "शिक्षा",
  "anomaly.flag": "चिन्ह"
}
```

---

## 12. Ollama Setup (Production Server)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull nomic-embed-text-v2-moe   # 475MB, multilingual embeddings
ollama pull qwen2.5                   # 4GB, Nepali-friendly chat

# Or lighter alternative
ollama pull nomic-embed-text          # 274MB, English embeddings
ollama pull llama3.2                  # 2GB, fast English chat

# Start Ollama service
ollama serve
```

Django connects via `http://localhost:11434`.

> `ponytail: nomic-embed-text-v1.5 (274MB) instead of v2-moe (475MB) if RAM is tight.`
>
> **Render limitation**: Render free tier cannot run Ollama. Options:
> 1. Run Ollama on a cheap VPS (Hetzner ~€4/mo) → Django connects via private network
> 2. Local demo only (judges see localhost)
> 3. Use `OllamaEmbeddings` with `base_url` pointing to externally hosted Ollama

---

## 13. Deployment (Render)

**render.yaml:**

```yaml
services:
  - type: web
    name: budget-darpan-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn config.wsgi
    disk:
      name: data
      mountPath: /var/data
      sizeGB: 1
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings
      - key: CHROMA_DB_DIR
        value: /var/data/chroma_db

  - type: web
    name: budget-darpan-frontend
    env: static
    buildCommand: npm install && npm run build
    staticPublishPath: ./dist
    envVars:
      - key: VITE_API_URL
        value: https://budget-darpan-backend.onrender.com
```

---

## 14. 60-Hour Build Schedule

| Slot | Hours | What | Deliverable |
|------|-------|------|-------------|
| **Day 1 AM** | 6 | Backend setup | Django project, models, migrations, admin, seed_data command |
| **Day 1 PM** | 6 | API + Data | DRF viewsets, budget endpoints, scrape news for 6 LGs' data, seed DB |
| **Day 2 AM** | 4 | Chat Engine | `chat/engine.py` — entity matcher, weight scorer, intent resolver |
| **Day 2 AM** | 4 | Anomaly | `anomaly/detector.py` — rules engine, `/api/anomalies/` |
| **Day 2 PM** | 6 | Frontend Part 1 | Vite+React, pages (Home, LGDashboard), SearchFilter, BudgetTable |
| **Day 2 PM** | 4 | Frontend Part 2 | SectorChart, i18n toggle, Nepali/English translations |
| **Day 3 AM** | 4 | Chat Widget | ChatWidget component, POST /api/chat/ integration, typing indicator |
| **Day 3 AM** | 4 | OCR + RAG | Tesseract setup, ingest budget speech PDF, ChromaDB, LangChain chain |
| **Day 3 PM** | 6 | Integration | ChatWidget → falls back to RAG, anomaly flags on dashboard, polish |
| **Day 3 PM** | 8 | Deploy + Demo Prep | Render deploy, seed real data, demo script, presentation |

---

## 15. Demo Script (For Judges)

**Flow:**

1. **Homepage** → Search "education" → shows all LGs' education budget side-by-side
2. **Toggle to Nepali** → UI flips to Devanagari
3. **Click Kathmandu** → LGDashboard: table + bar chart of 5 sectors, allocated vs spent
4. **Chat**: `kathmandu education budget 2082 ma kati kharcha vayo?` → Nepali response with amount
5. **Anomalies tab** → Red flags: Hetauda admin bloat (27.84%), Bhaktapur capital underspend
6. **RAG**: `what did the budget speech say about education allocation?` → Response from ChromaDB-retrieved speech chunk with citation
7. **Compare**: `compare health spending in kathmandu vs pokhara` → Side-by-side chart

---

## 16. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ollama too slow on hackathon laptop | Chat/RAG slow | Use `llama3.2:2b` (smallest), set `num_predict=256` |
| Nepali OCR quality poor | RAG has garbage text | Use pre-parsed text from bibstha repo instead |
| ChromaDB too slow | Search lag | Set k=2, use nomic-embed-text-v1.5 (smaller) |
| Not enough time for mobile | Phase 3 incomplete | Responsive web is sufficient demo; skip React Native |
| Budget data inaccurate | Wrong demo numbers | Source from verified news articles + MoFAGA, label as "unofficial reconstruction" |

---

## 17. Quick Start (for teammates)

```bash
# 1. Clone repo
git clone <repo-url> && cd budget-darpan

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data          # Seeds 6 LGs, sectors, FYs, 180 budget rows
python manage.py runserver

# 3. Start Ollama (separate terminal)
ollama pull nomic-embed-text-v2-moe
ollama pull qwen2.5
ollama serve

# 4. Ingest docs for RAG
python manage.py ocr_pdfs           # OCR budget PDFs → DB
python manage.py ingest_docs        # Chunk → embed → ChromaDB

# 5. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev                         # Opens localhost:5173 → proxies API to :8000
```

---

## 18. Data Sources Reference

| Source | URL | What |
|--------|-----|------|
| MoFAGA Local Budget Portal | https://mofaga.gov.np/lgbudget-details | Budget submission for all 753 LGs |
| MoFAGA Budget Summary | https://www.mofaga.gov.np/index.php/lgbudget | Province-wise budget stats |
| FCGO Daily Budgetary Analysis | https://old.fcgo.gov.np/daily-budgetary-analysis | Daily revenue/spending |
| bibstha/nepal-budget-2083-2084 | https://github.com/bibstha/nepal-budget-2083-2084 | Pre-parsed budget speech (Nepali+English, Markdown) |
| World Bank Nepal Fiscal Dashboard | https://www.worldbank.org/en/data/interactive/2026/02/10/nepal-fiscal-dashboard | Historical expenditure by function |
| MoF Red Book | https://mof.gov.np/category/redbook/ | Expenditure estimates |
| FCGO Chart of Accounts | https://www.fcgo.gov.np/storage/uploads/publications/20210908152258_Unofficial%20Translation%20of%20Chart%20of%20Account.pdf | Official sector classification (COFOG) |
| Nepal Rastra Bank Fiscal Data | https://www.nrb.org.np/database-on-nepalese-economy/fiscal-sector/ | Revenue/expenditure trends |
| 19pritom/Nepal-77-Districts-Local-Levels | https://github.com/19pritom/Nepal-77-Districts-Local-Levels | 753 LGs in JSON (seeding) |
| yanwo1994/nepal-geo-data | https://github.com/yanwo1994/nepal-geo-data | GeoJSON for maps |
| Kathmandu Metro Budget | https://new.kathmandu.gov.np/en/notices/sectoral-budget-and-expenditure-208283 | Sectoral budget reports |
| Pokhara Metro Budget | https://www.pokharamun.gov.np/budget-program | Budget speech PDFs |
| Lalitpur Metro Budget | https://lalitpurmun.gov.np/budget-program | Budget books |
| Bhaktapur Muni Budget | https://www.ratopati.com/story/496702 | News article with sector breakdown |
| Hetauda Sub-Metro Budget | https://hetaudamun.gov.np/ne/content/... | Monthly income/expense |
| Butwal Sub-Metro Budget | https://butwalmun.gov.np/budget-income-expenses | Budget allocation |
