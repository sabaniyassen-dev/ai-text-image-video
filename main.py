from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import re
from typing import List, Dict, Any, Optional

app = FastAPI(title="AI Media Intelligence Platform", version="1.0.0")

# يسمح بالعمل من نفس الدومين (يمكن تشديده لاحقًا)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# يخدم ملفات الواجهة
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
def serve_index():
    return FileResponse("index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

ABSOLUTE_CLAIMS = ["guarantee","100%","always","never","best","no risk","miracle","مضمون","نهائي"]
SENSITIVE = ["kids","children","health","investment","أطفال","دواء","استثمار"]
PRIVACY = ["phone","email","address","رقم","هاتف","عنوان","@"]

def tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9\u0600-\u06FF]+", text.lower())

def word_stats(text: str) -> Dict[str, Any]:
    words = tokenize(text)
    wc = len(words)
    sc = max(1, len(re.findall(r"[.!?؟\n]", text)))
    avg = wc / sc
    return {"word_count": wc, "avg_words_per_sentence": round(avg,2)}

def count_hits(text: str, words: List[str]) -> int:
    t = text.lower()
    return sum(1 for w in words if w in t)

@app.post("/evaluate")
def evaluate(payload: Dict[str, Any]):
    text = (payload.get("text") or "").strip()
    if not text:
        return {"score":0,"strengths":[],"weaknesses":["Empty text"]}

    stats = word_stats(text)
    abs_hits = count_hits(text, ABSOLUTE_CLAIMS)
    sens_hits = count_hits(text, SENSITIVE)
    priv_hits = count_hits(text, PRIVACY)

    clarity = max(40, 90 - int(stats["avg_words_per_sentence"] * 2))
    credibility = max(35, 85 - abs_hits * 10)
    risk = min(95, abs_hits*15 + sens_hits*10 + priv_hits*10)

    score = int((clarity + credibility + (100-risk))/3)

    strengths = []
    weaknesses = []

    if abs_hits == 0:
        strengths.append("No exaggerated claims detected.")
    else:
        weaknesses.append("Contains absolute claims; revise wording.")

    if sens_hits > 0:
        weaknesses.append("Sensitive domain indicators detected.")
    else:
        strengths.append("No sensitive domain flags detected.")

    return {
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses
    }

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "analysis": "Prototype image analysis complete.",
        "score": 82
    }

@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "analysis": "Prototype video analysis complete.",
        "score": 78
    }
