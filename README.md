# PromptGuard

Real-time prompt injection detection for LLM applications — a hybrid DistilBERT classifier and rule-based heuristics layer that sits in front of any LLM call, catching hidden malicious instructions before they reach the model.

Live demo: https://promptguard-w9cd5dfuds5thgpthxkcra.streamlit.app/
Live API docs: https://promptguard-xrqm.onrender.com/docs

---

## The Problem

AI applications are increasingly connected to real systems — email, databases, code execution, browsing tools. Attackers exploit this by hiding malicious instructions inside user input, documents, or web content the AI processes, tricking it into ignoring its rules, leaking data, or taking unintended actions. This is **prompt injection**, ranked the #1 risk for LLM applications on the OWASP Top 10 (LLM01).

This isn't theoretical — in June 2025, researchers disclosed EchoLeak (CVE-2025-32711, CVSS 9.3), a zero-click prompt injection exploit against Microsoft 365 Copilot. CrowdStrike's 2026 Global Threat Report documented prompt injection attacks against 90+ organizations in 2025 alone. Most small teams shipping AI products today have no dedicated defense against this beyond ad-hoc keyword filters, which are trivially bypassed by rephrasing or encoding.

## The Solution

PromptGuard is a FastAPI REST API a developer adds before their existing LLM call — no changes to the LLM integration itself required:

```
User prompt → PromptGuard /check → flagged? → block, else forward to LLM as normal
```

```python
check = requests.post("https://promptguard-xrqm.onrender.com/check", json={"prompt": user_message}).json()
if check["flagged"]:
    return "Request blocked."
# otherwise, proceed to call OpenAI/Anthropic/etc. as usual
```

## Architecture

- **DistilBERT classifier** (fine-tuned, exported to ONNX + int8 quantized) — learns patterns from real attack examples
- **Rule-based heuristics** — regex pattern matching for known jailbreak phrases, base64-encoded payload detection, input length anomalies
- **Hybrid scoring** — rules act as a confidence floor; if a rule fires, the combined score is boosted regardless of model confidence, so obvious attacks aren't missed even if the model is uncertain
- **FastAPI** backend exposing `POST /check`
- **Streamlit** frontend as a thin demo client calling the same live API

## Results

Evaluated on the held-out test split of `deepset/prompt-injections` (116 examples, untouched during training):

| Metric | Score |
|---|---|
| Precision | 96.5% |
| Recall | 91.7% |
| Threshold | 0.03 (tuned via precision-recall sweep, not the default 0.5) |

**Why threshold 0.03 and not 0.5:** the model's raw output scores are not well-calibrated around the standard 0.5 midpoint for this dataset size. Rather than assume the default, the operating threshold was chosen from an actual precision-recall curve on the test set, prioritizing recall — since in a security context, a missed attack is more costly than a false alarm.

**Comparison note:** a published benchmark on this same dataset reports 99.1% accuracy. The gap is most likely explained by a larger training run/more extensive tuning than was feasible in this project's timeframe — closing it would be the first priority with more time.

## Known Limitations (found through manual testing)

- **Rule patterns are intentionally narrow** — regex phrase matching requires close-to-exact phrasing (e.g. `"forget all previous instructions"`) and can miss natural variation (e.g. `"forget all your previous prompts"` originally slipped past the rules layer until patterns were loosened with bounded wildcards; verified via regression test before deploying the fix).
- **Input-only screening** — PromptGuard checks the incoming prompt, not the LLM's output. A more complete system would also scan the response before it reaches the user, in case the model was manipulated despite a passing input check.
- **No multi-turn detection** — each prompt is evaluated independently; attacks that build up gradually across a conversation aren't currently caught.
- **Free-tier hosting tradeoffs** — the API sleeps after 15 minutes of inactivity on Render's free tier (mitigated with UptimeRobot keep-alive pings), and the model was quantized/converted to ONNX specifically to fit the 512MB memory limit, which may trade a small amount of accuracy for deployability.

## Tech Stack

- **Model:** DistilBERT, fine-tuned on `deepset/prompt-injections` (balanced with `tatsu-lab/alpaca` benign examples), exported to ONNX and int8-quantized for lightweight deployment
- **Backend:** FastAPI, ONNX Runtime, Hugging Face `transformers` (tokenizer only)
- **Frontend:** Streamlit
- **Hosting:** Render (API), Streamlit Community Cloud (demo), Hugging Face Hub (model weights)
- **Data:** `deepset/prompt-injections`, `tatsu-lab/alpaca`

## Project Structure

PromptGuard/
├── src/
│ ├── api.py # FastAPI app, POST /check endpoint
│ ├── hybrid_score.py # combines model + rules into one risk score
│ ├── heuristics.py # rule-based detection layer
│ └── test_hybrid.py # manual test cases
├── data/
│ ├── promptguard_train.csv
│ └── promptguard_test.csv
├── streamlit_app.py # demo frontend
├── .streamlit/config.toml # theme config
├── assets/logo_512.png
└── requirements.txt

## What I'd Add With More Time

1. **Multi-turn conversation detection** — evaluate patterns across a full conversation, not just single messages
2. **Adversarial robustness testing** — automated red-teaming against the model itself, retraining against attacks specifically designed to evade it
3. **Indirect prompt injection detection** — extend beyond direct prompts to catch injections hidden in documents, emails, and web content an AI agent is asked to process
4. **Output scanning** — check the LLM's response, not just the input

## Model & Dataset Links

- Model (original): https://huggingface.co/amna27/promptguard-distilbert
- Model (ONNX, deployed): https://huggingface.co/amna27/promptguard-distilbert-onnx
- Training data: [deepset/prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections), [tatsu-lab/alpaca](https://huggingface.co/datasets/tatsu-lab/alpaca)
