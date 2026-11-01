# Digital Image Forensics Tool

A college mini-project for analyzing digital images for forensic indicators.

## Features
- React + Vite frontend
- FastAPI Python backend
- Image upload
- EXIF metadata extraction
- SHA-256 and MD5 hashing
- Error Level Analysis (ELA)
- Copy-move forgery analysis using ORB feature matching
- Basic noise/residual analysis
- Forensic result summary
- PDF report generation

> Important: The application reports indicators of possible manipulation. It does not prove that an image is fake.

## Requirements
- Windows 10/11
- Python 3.10+
- Node.js 18+
- VS Code

## 1. Start Backend

Open PowerShell in the `backend` folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend:
http://127.0.0.1:8000

API documentation:
http://127.0.0.1:8000/docs

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Then activate again.

## 2. Start Frontend

Open another PowerShell in the `frontend` folder:

```powershell
npm install
npm run dev
```

Open the URL shown by Vite, normally:
http://localhost:5173

## 3. Test
Upload a JPG/JPEG/PNG image and click Analyze.

## Project structure

digital-image-forensics/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── services/
│   │   ├── metadata.py
│   │   ├── hashing.py
│   │   ├── ela.py
│   │   ├── copy_move.py
│   │   └── report.py
│   ├── uploads/
│   └── results/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
└── README.md
