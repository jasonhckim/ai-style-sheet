# updating from hyfve_ai_agent
**AI-powered solutions for Hyfve’s operations and automation.**

## Objective
Take a PDF, Extract product data, generate AI-based titles/descriptions, and upload to google sheets.
Split into 3 GCP-based services.

1. **PDF Parser** (Cloud Function)
2. **AI Description Generator** (Cloud Run)
3. **Google Sheet Writer** (Cloud Function)


## 🏠 GCP Setup
### 1. Use Existing GCP Project
- Project: `hyfve-style-description` (✅ already created)

### 2. Enable Required APIs
Make sure these are enabled in the API library:
- Cloud Functions
- Cloud Run
- Cloud Build
- Pub/Sub
- Google Drive API
- Google Sheets API
- Secret Manager (optional)

### 3. Service Account Setup
Use or create a service account with the following roles:
- Cloud Functions Invoker
- Cloud Run Invoker
- Pub/Sub Publisher & Subscriber
- Drive API + Sheets API permissions
- Stackdriver Resource Metadata Writer

Generate a key (JSON) and store it locally or in Secret Manager.

---

## 🛠️ Step-by-Step Service Setup

### ✅ 1. PDF Parser (Cloud Function)
**Goal:**
- Trigger: New PDF in Drive folder
- Output: Publish to Pub/Sub topic `pdf-processed`

**Responsibilities:**
- Use PyMuPDF to extract style number and image
- Upload image to Drive (get public link)
- Push extracted info to Pub/Sub

**Deploy:**
```bash
cd functions/pdf_parser
pip install -r requirements.txt -t .
gcloud functions deploy parse_pdf \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --env-vars-file ../../.env.yaml \
  --entry-point main \
  --project hyfve-style-description
```

### ✅ 2. AI Description Generator (Cloud Run)
**Goal:**
- Trigger: Pub/Sub message from `pdf-processed`
- Output: Publishes enriched record to `descriptions-generated`

**Responsibilities:**
- Use OpenAI to generate title, description, hashtags
- Attach to original record
- Publish to `descriptions-generated`

**Deploy:**
```bash
cd functions/description_generator
gcloud run deploy ai-generator \
  --source . \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=... \
  --no-allow-unauthenticated \
  --project hyfve-style-description
```

### ✅ 3. Google Sheet Writer (Cloud Function)
**Goal:**
- Trigger: Pub/Sub topic `descriptions-generated`
- Output: Google Sheet

**Responsibilities:**
- Copy Google Sheet template
- Paste data to Sheet1
- Paste cleaned data to Designer tab

**Deploy:**
```bash
cd functions/sheet_writer
pip install -r requirements.txt -t .
gcloud functions deploy write_to_sheet \
  --runtime python310 \
  --trigger-topic descriptions-generated \
  --env-vars-file ../../.env.yaml \
  --entry-point main \
  --project hyfve-style-description
```

---

## 💼 Project Structure Example
```
ai-style-sheet/gcp
├── description_generator/
│   └── main.py
├── pdf_parser/
│   └── main.py
├── sheet_writer/
│   └── main.py
├── shared/
│   ├── auth.py
│   ├── common.py
│   ├── config.yaml
│   └── drive_utils.py
├── .env.yaml
└── requirements.txt
```

---

## 🔹 Pub/Sub Topics
| Topic Name               | Publisher      | Subscriber       |
|--------------------------|----------------|------------------|
| `pdf-processed`          | pdf_parser     | ai_generator     |
| `descriptions-generated` | ai_generator   | sheet_writer     |

---

## 📜 Environment Variables
Create `.env.yaml`:
```yaml
GOOGLE_APPLICATION_CREDENTIALS: "service-account.json"
PDF_FOLDER_ID: "..."
TEMPLATE_SHEET_ID: "1MgmD0ncx7GmtmEaxQmhs8m_bi-1TBGeX8q4cixcFiF4"
OPENAI_API_KEY: "sk-..."
```

---

## 🤝 Final Note
Once this works:
- Add Cloud Scheduler to trigger PDF polling daily
- Add logging to each stage (`google-cloud-logging`)
- Use Firestore or GCS for caching if needed
