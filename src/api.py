from fastapi import FastAPI
from pydantic import BaseModel
from hybrid_score import get_risk_assessment

app = FastAPI(title="PromptGuard API", description="Prompt injection risk scoring")

class CheckRequest(BaseModel):
    prompt: str

class CheckResponse(BaseModel):
    risk_score: float
    flagged: bool
    model_score: float
    rule_triggered: bool
    reasons: list[str]

@app.get("/")
def root():
    return {"status": "PromptGuard API is running", "docs": "/docs"}

@app.post("/check", response_model=CheckResponse)
def check_prompt(request: CheckRequest):
    result = get_risk_assessment(request.prompt)
    return {
        "risk_score": result["risk_score"],
        "flagged": result["flagged"],
        "model_score": result["model_score"],
        "rule_triggered": result["rule_triggered"],
        "reasons": result["reasons"],
    }
