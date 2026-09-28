# How to Start — Project Hub V2

## Prerequisites

- **Python 3.x** installed
- **Node.js & npm** installed

---

## 1. Backend (Flask API)

Open a terminal and run:

```bash
cd backend
```

### First-time setup (only once)

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file in the `backend/` folder (if it doesn't already exist) with:

```
FLASK_SECRET_KEY=change-this-to-a-random-secret-key-in-production
JWT_SECRET_KEY=change-this-jwt-secret-key-in-production
GROQ_API_KEY=your-groq-api-key-here
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
```

### Run the backend

```bash
# Make sure venv is activated, then:
python app.py
```

The backend API will be running at **http://localhost:5000**

---

## 2. Frontend (React + Vite)

Open a **separate** terminal and run:

```bash
cd frontend
```

### First-time setup (only once)

```bash
npm install
```

### Run the frontend

```bash
npm run dev
```

The frontend will be running at **http://localhost:5173**

---

## Quick Start (both together)

Open **two terminals** side by side:

| Terminal 1 (Backend)               | Terminal 2 (Frontend)  |
| ---------------------------------- | ---------------------- |
| `cd backend`                       | `cd frontend`          |
| `.\venv\Scripts\activate`          | `npm install`          |
| `python app.py`                    | `npm run dev`          |

Then open **http://localhost:5173** in your browser.

---

## Tech Stack

| Layer    | Technology                     |
| -------- | ------------------------------ |
| Frontend | React 19, Vite, React Router   |
| Backend  | Flask, Flask-JWT-Extended       |
| AI       | Groq API (gpt-oss-1-2.0 model) |
| Data     | JSON file-based storage         |
