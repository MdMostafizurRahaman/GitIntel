# SETUP & Installation Guide

## প্রিরিকুইজাইট

- Python 3.8+
- Neo4j 4.0+ (ডাউনলোড: https://neo4j.com/download/)
- Git
- 4GB RAM (কমপক্ষে)

## স্টেপ ১: ডেটাবেস সেটআপ

### Neo4j ইনস্টলেশন

#### Windows:
```bash
# Neo4j Desktop ডাউনলোড করুন
https://neo4j.com/download/

# অথবা CLI ইনস্টলেশন
choco install neo4j  # Chocolatey এর মাধ্যমে
```

#### Linux:
```bash
# Ubuntu/Debian
sudo apt-get install neo4j

# Start Neo4j
sudo systemctl start neo4j
```

#### Mac:
```bash
# Homebrew
brew install neo4j

# Start
brew services start neo4j
```

### Neo4j কনফিগারেশন

1. **ওয়েব ইন্টারফেস খুলুন**: http://localhost:7474
2. **ডিফল্ট পাসওয়ার্ড পরিবর্তন করুন**: neo4j / neo4j → নতুন পাসওয়ার্ড
3. **প্রতিযোগিতা চালু করুন** (যদি থাকে):
   ```
   SHOW TRANSACTIONS;
   TERMINATE TRANSACTION "query-id";
   ```

## স্টেপ ২: পাইথন পরিবেশ সেটআপ

### ভার্চুয়াল এনভায়রনমেন্ট তৈরি করুন

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### ডিপেন্ডেন্সি ইনস্টল করুন

```bash
cd d:\GitIntel\Dataset
pip install -r requirements.txt
```

## স্টেপ ৩: কনফিগারেশন

### Environment Variables সেট করুন

**`.env` ফাইল তৈরি করুন:**

```bash
# Windows PowerShell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="আপনার_পাসওয়ার্ড"
$env:NEO4J_DATABASE="neo4j"
$env:LOG_LEVEL="INFO"
$env:API_HOST="127.0.0.1"
$env:API_PORT="8000"

# Linux/Mac
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="আপনার_পাসওয়ার্ড"
# ... অন্যগুলো
```

অথবা `.env` ফাইল তৈরি করুন:

```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=আপনার_পাসওয়ার্ড
NEO4J_DATABASE=neo4j
LOG_LEVEL=INFO
API_HOST=127.0.0.1
API_PORT=8000
```

### Python কনফিগারেশন সম্পাদন করুন

`config/config.py` এ প্রয়োজন অনুযায়ী পরিবর্তন করুন:

```python
NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "user": os.getenv("NEO4J_USER", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", "password"),
    "database": os.getenv("NEO4J_DATABASE", "neo4j"),
}
```

## স্টেপ ৪: সিস্টেম টেস্ট করুন

### Neo4j সংযোগ যাচাই করুন

```bash
cd d:\GitIntel\Dataset
python -c "from neo4j.manager import get_neo4j_manager; neo4j = get_neo4j_manager(); print('Connected!'); neo4j.close()"
```

### CLI সিস্টেম টেস্ট করুন

```bash
python -m cli.main list-datasets
```

### API সার্ভার শুরু করুন

```bash
python -m api.server
```

অথবা uvicorn দিয়ে:

```bash
uvicorn api.server:app --reload --host 127.0.0.1 --port 8000
```

টেস্ট করুন:
```bash
curl http://127.0.0.1:8000/api/health
```

### GUI অ্যাপ চালু করুন

```bash
# অপশন ১: PyQt5 GUI (অ্যাডভান্সড, ইনস্টলেশন লাগে)
python -m gui.app

# অপশন ২: tkinter GUI (বিল্ট-ইন, কোনো ইনস্টলেশন লাগে না)
python -m gui.app_tkinter
```

**GUI বেছে নেওয়ার টিপস:**
- **tkinter**: যদি PyQt5 ইনস্টল করতে না চান
- **PyQt5**: যদি আরও অ্যাডভান্সড ফিচার চান (টেবিল, প্রোগ্রেসবার)

## স্টেপ ৫: নমুনা ডেটা দিয়ে পরীক্ষা করুন

### নমুনা ডেটা এক্সট্রাক্ট করুন

```bash
# একটি ছোট GitHub repo ক্লোন করুন
git clone https://github.com/your-sample-repo /tmp/sample_repo

# Defects4J ডেটা এক্সট্রাক্ট করুন
python -m cli.main extract \
  --dataset-type defects4j \
  --source /tmp/sample_repo \
  --output /tmp/raw_data.json
```

### ডেটা প্রসেস করুন

```bash
python -m cli.main process \
  --input /tmp/raw_data.json \
  --output /tmp/processed_data.json \
  --normalize-code \
  --clean-text \
  --remove-duplicates
```

### ডেটা লেবেল করুন

```bash
python -m cli.main label \
  --input /tmp/processed_data.json \
  --output /tmp/labeled_data.json \
  --label-type bug_severity
```

### Neo4j-এ ইমপোর্ট করুন

```bash
python -m cli.main import-to-neo4j \
  --input /tmp/labeled_data.json \
  --dataset-name "Sample Dataset" \
  --project-id "sample_001"
```

### সিস্টেম স্ট্যাটাস চেক করুন

```bash
python -m cli.main status
```

## স্টেপ ৬: দীর্ঘমেয়াদী সেটআপ

### নিয়মিত ব্যবহারের জন্য

1. **Batch Scripts তৈরি করুন** (`scripts/run_extraction.bat`):

```batch
@echo off
cd /d "d:\GitIntel\Dataset"
call venv\Scripts\activate
python -m cli.main extract ^
  --dataset-type %1 ^
  --source %2 ^
  --output %3
pause
```

2. **আপনার পাইথন পাথ কনফিগার করুন**:

```bash
# PowerShell Profile এ যোগ করুন
$PROFILE

# যোগ করুন:
$env:PYTHONPATH += ";d:\GitIntel\Dataset"
```

### দৈনিক ব্যাকআপ সেটআপ করুন

```bash
# Windows Task Scheduler
# New Task -> Run: python -m scripts.backup_neo4j
```

### লগ ফাইল মনিটর করুন

```bash
# লগ ফোল্ডার খুলুন
explorer "d:\GitIntel\Dataset\logs"
```

## সাধারণ সমস্যা সমাধান

### সমস্যা: "neo4j সংযোগ ব্যর্থ"

**সমাধান**:
1. Neo4j রান হচ্ছে কি চেক করুন: `systemctl status neo4j`
2. ইউআরআই সঠিক কি চেক করুন (default: `bolt://localhost:7687`)
3. পাসওয়ার্ড সঠিক কি চেক করুন

```bash
# Neo4j Web UI পরীক্ষা করুন
http://localhost:7474
```

### সমস্যা: "মডিউল খুঁজে পাওয়া যায় না"

**সমাধান**:
1. ভার্চুয়াল এনভায়রনমেন্ট অ্যাক্টিভেট করা আছে কি চেক করুন
2. requirements.txt ইনস্টল করেছেন কি চেক করুন:

```bash
pip install -r requirements.txt --upgrade
```

### সমস্যা: "পারমিশন ডেনাইড" (Linux/Mac)

**সমাধান**:
```bash
chmod +x d:\GitIntel\Dataset\cli\main.py
```

### সমস্যা: GUI স্টার্ট হচ্ছে না

**সমাধান**:
```bash
# PyQt5 GUI এর জন্য
pip install PyQt5 --force-reinstall
python -m gui.app

# অথবা tkinter GUI ব্যবহার করুন (কোনো ইনস্টলেশন লাগে না)
python -m gui.app_tkinter

# Headless mode এ চেষ্টা করুন
export QT_QPA_PLATFORM=offscreen
python -m gui.app
```

## নেক্সট স্টেপস

1. **আরও ডেটাসেট যোগ করুন**: নিজের extractor লিখুন
2. **কাস্টম processors তৈরি করুন**: আপনার চাহিদা অনুযায়ী
3. **API ইন্টিগ্রেশন**: ওয়েবসাইটে ইন্টিগ্রেট করুন
4. **ডাটা ভিজুয়ালাইজেশন**: Neo4j ড্যাশবোর্ড সেটআপ করুন

## সাপোর্ট

সমস্যা বা প্রশ্ন থাকলে:
- দেখুন: `docs/` ফোল্ডার
- রিডমি পড়ুন: `docs/README.md`
- আর্কিটেকচার: `docs/ARCHITECTURE.md`

---

**শুভেচ্ছা! আপনার Dataset Management System প্রস্তুত 🎉**
