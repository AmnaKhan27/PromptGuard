import re
import base64

SUSPICIOUS_PHRASES = [
    r"ignore (all|any|the) (previous|prior|above) instructions",
    r"disregard (all|any|the) (previous|prior|above)",
    r"forget (all|any|your) (previous|prior|instructions)",
    r"you are now",
    r"act as (if|though)",
    r"new (instructions|task|rule)s?:",
    r"reveal your (system prompt|instructions|prompt)",
    r"show me (all )?your (prompt|instructions|system prompt)",
    r"jailbreak",
    r"DAN mode",
    r"developer mode",
    r"pretend (you are|to be)",
]

def check_suspicious_phrases(text: str):
    text_lower = text.lower()
    hits = []
    for pattern in SUSPICIOUS_PHRASES:
        if re.search(pattern, text_lower):
            hits.append(pattern)
    return hits


def check_base64(text: str):
    candidates = re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", text)
    decoded_hits = []
    for c in candidates:
        try:
            decoded = base64.b64decode(c, validate=True).decode("utf-8", errors="ignore")
            if decoded and any(ch.isalpha() for ch in decoded):
                decoded_hits.append(decoded[:80])
        except Exception:
            continue
    return decoded_hits


def check_length_anomaly(text: str, max_normal_len: int = 1500):
    return len(text) > max_normal_len


def run_heuristics(text: str) -> dict:
    phrase_hits = check_suspicious_phrases(text)
    base64_hits = check_base64(text)
    is_long = check_length_anomaly(text)

    triggered = bool(phrase_hits) or bool(base64_hits) or is_long
    reasons = []
    if phrase_hits:
        reasons.append(f"suspicious phrase pattern matched ({len(phrase_hits)} hit(s))")
    if base64_hits:
        reasons.append("base64-encoded content detected")
    if is_long:
        reasons.append("input length anomaly")

    return {
        "rule_triggered": triggered,
        "rule_reasons": reasons,
    }
