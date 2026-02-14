from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import re
from typing import List, Dict, Any, Optional

app = FastAPI(title="AI Media Intelligence Platform", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # لاحقاً نضيّقها لدومينك فقط
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def serve_index():
    return FileResponse("index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

ABSOLUTE_CLAIMS = [
    "guarantee","100%","always","never","best","no risk","miracle",
    "مضمون","نهائي","بدون أي","مستحيل","أضمن","ضمان"
]
SENSITIVE = ["kids","children","child","أطفال","قاصر","health","دواء","مرض","investment","استثمار","ربح"]
PRIVACY = ["phone","email","address","رقم","هاتف","عنوان","@","واتساب","whatsapp"]

def tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9\u0600-\u06FF]+", text.lower())

def word_stats(text: str) -> Dict[str, Any]:
    words = tokenize(text)
    wc = len(words)
    sc = max(1, len(re.findall(r"[.!?؟\n]", text)))
    avg_wps = wc / sc
    return {"word_count": wc, "sentence_count": sc, "avg_words_per_sentence": round(avg_wps, 2)}

def count_hits(text: str, words: List[str]) -> int:
    t = text.lower()
    return sum(1 for w in words if w.lower() in t)

def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))

def rubric_for_score(score: int) -> Dict[str, str]:
    if score >= 85:
        return {"level":"Excellent", "description":"Ready to publish with minor refinements."}
    if score >= 70:
        return {"level":"Very Good", "description":"Strong, but improve proof/CTA clarity."}
    if score >= 55:
        return {"level":"Good", "description":"Usable draft; needs revision for clarity/risks."}
    if score >= 40:
        return {"level":"Fair", "description":"High revision needed before publishing."}
    return {"level":"Poor", "description":"Not publish-ready; rewrite recommended."}

@app.post("/evaluate")
def evaluate(payload: Dict[str, Any]):
    text = (payload.get("text") or payload.get("content") or "").strip()
    msg_type = payload.get("message_type") or "general"
    channel = payload.get("channel") or "social"
    audience = payload.get("audience") or "general"

    if not text:
        return {
            "score": 0,
            "strengths": [],
            "weaknesses": ["Empty input text"],
            "detailed_analysis": [],
            "paragraph": "No content was provided for analysis.",
            "stats": {"word_count": 0, "sentence_count": 0, "avg_words_per_sentence": 0},
            "rubric": rubric_for_score(0)
        }

    stats = word_stats(text)
    abs_hits = count_hits(text, ABSOLUTE_CLAIMS)
    sens_hits = count_hits(text, SENSITIVE)
    priv_hits = count_hits(text, PRIVACY)

    clarity = clamp(90 - int(stats["avg_words_per_sentence"] * 2), 40, 95)
    credibility = clamp(85 - abs_hits * 10, 35, 95)
    compliance_risk = clamp(20 + abs_hits * 15 + sens_hits * 10 + priv_hits * 10, 0, 95)
    score = int((clarity + credibility + (100 - compliance_risk)) / 3)

    strengths = []
    weaknesses = []

    if stats["word_count"] >= 25:
        strengths.append("Message length is sufficient for clarity.")
    else:
        weaknesses.append("Text is too short; add context and a clear CTA.")

    if abs_hits == 0:
        strengths.append("No obvious absolute/guaranteed claims detected.")
    else:
        weaknesses.append("Contains absolute/guaranteed-style claims; reduce legal/ethical risk.")

    if priv_hits == 0:
        strengths.append("No clear personal-data collection cues detected.")
    else:
        weaknesses.append("Potential personal data collection; add consent + privacy notice.")

    if sens_hits == 0:
        strengths.append("No strong indicators of sensitive regulated domains detected.")
    else:
        weaknesses.append("Sensitive domain cues detected; requires stricter wording and review.")

    points = [
        f"1) Clarity score: {clarity}/100 based on sentence length and readability.",
        f"2) Credibility score: {credibility}/100 influenced by absolute claims (hits: {abs_hits}).",
        f"3) Compliance risk: {compliance_risk}/100 (higher = riskier). Factors: absolutes={abs_hits}, sensitive={sens_hits}, privacy={priv_hits}.",
        "4) Value proposition: state the benefit clearly (what the audience gains).",
        "5) CTA: make it specific (action + where + timeframe).",
        "6) Evidence: add 1–2 proof points (data, testimonial, official source).",
        "7) Tone: avoid exaggerated promises; use qualified wording (may/can/typically).",
        f"8) Audience fit: tailor complexity to '{audience}'.",
        f"9) Channel fit ({channel}): optimize format (short hooks for social; structured for web).",
        f"10) Message type ({msg_type}): if ad/PR/crisis, follow approvals workflow.",
        "11) Ethics: avoid manipulation; keep transparent intent.",
        "12) Privacy-by-design: state purpose/consent if collecting contacts.",
        "13) Inclusivity: avoid stereotyping; use inclusive language.",
        "14) Compliance caution: for health/finance/children, avoid directives without approval.",
        "15) Improvement plan: refine headline + add proof point + strengthen CTA + final human review."
    ]

    paragraph = (
        f"This content shows a {'strong' if score>=70 else 'mixed'} communication profile. "
        f"Stats: {stats['word_count']} words, avg {stats['avg_words_per_sentence']} words/sentence. "
        f"Main risk drivers: absolute claim signals ({abs_hits}) and sensitive/privacy cues ({sens_hits}/{priv_hits}). "
        f"To improve: add a verified proof point, use qualified wording, and strengthen the CTA for the target audience."
    )

    return {
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "detailed_analysis": points,
        "paragraph": paragraph,
        "stats": stats,
        "rubric": rubric_for_score(score)
    }

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    # Prototype details (يمكن تطويره لاحقاً لقراءة أبعاد الصورة فعلياً)
    return {
        "filename": file.filename,
        "score": 82,
        "summary": "Image is generally suitable for publishing (prototype checks).",
        "checks": {
            "aspect_ratio_hint": "Prefer 1:1 or 4:5 for Instagram; 16:9 for YouTube thumbnails.",
            "contrast_hint": "Verify text contrast on dark areas.",
            "branding_hint": "Add logo/attribution in a safe margin.",
            "readability_hint": "Keep max 2–3 font sizes; avoid dense text blocks."
        },
        "recommendations": [
            "Ensure safe margins for different crops (mobile vs desktop).",
            "Use one visual focal point; avoid clutter.",
            "If using text overlay, test readability on small screens."
        ]
    }

@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    # Prototype details (لا نقوم بقراءة الفيديو فعلياً على Render المجاني)
    return {
        "filename": file.filename,
        "score": 78,
        "technical_assumptions": {
            "note": "Prototype evaluation (no deep decoding on free tier).",
            "recommended_specs": "1080p, 25–30fps, captions on, strong hook in first 3–5 seconds."
        },
        "strengths": [
            "Structure can be optimized for short-form platforms.",
            "Score assumes acceptable pacing and basic clarity."
        ],
        "weaknesses": [
            "If file is large, upload may fail on free hosting due to timeout/limits.",
            "CTA may be missing; ensure end-card with next step."
        ],
        "detailed_analysis": [
            "1) Hook: state benefit/problem in first 3–5 seconds.",
            "2) Captions: add burned-in subtitles for silent viewing.",
            "3) CTA: end-card with link/QR/contact.",
            "4) Proof: add reference/disclaimer for factual claims.",
            "5) Privacy: blur faces/plates if no consent."
        ],
        "summary": "Video prototype analysis complete. For reliable results, use short clip uploads on free hosting."
    }
