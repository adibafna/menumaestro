# MenuMaestro 🍽️

**Local-first menu translation & cultural adaptation — powered by Gemma 3 via Ollama.**

> Built for the [Hacktoberfest Open-Source AI Challenge: Week 2 — Side Hustle](https://dev.to/challenges/hf26)

---

## What it does

MenuMaestro takes a restaurant's dish names (typed or photographed) and turns them into **culturally adapted, appetite-inspiring translations** — not the robotic word-for-word output you get from generic translators.

For each dish you get:
- **Adapted name** in the target language (sounds natural to a native speaker)
- **Appetising 1–2 sentence description** with ingredient context
- **Dietary flags** — Vegan · Vegetarian · Gluten-Free · Halal · Kosher · Nut-Free · Dairy-Free
- **Cultural note** — one sentence for dishes that confuse foreign guests
- A suggested **restaurant tagline** in the target language

Supports 12 target languages out of the box. Drop in a photo of a handwritten menu and Gemma's vision model OCRs it first.

---

## Why open-weight + local?

| Concern | How MenuMaestro handles it |
|---|---|
| **Privacy** | Your seasonal specials never hit a cloud server |
| **Cost** | Zero API fees after setup — Gemma 3 runs on consumer hardware |
| **Vendor lock-in** | Swap any Ollama-compatible model; the prompt is yours |
| **Niche accuracy** | Gemma 3 instruction-tuned for food cultural context; can be fine-tuned on your cuisine |

A small Indian restaurant owner paying \$0/month in AI costs vs. \$30+/month for a GPT-4o API — that's the difference between a viable side hustle and one that eats its own margin.

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running (`ollama serve`)
- The `gemma3:4b` model pulled: `ollama pull gemma3:4b`

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/adibafna/menumaestro
cd menumaestro

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull the model (first time only, ~3 GB)
ollama pull gemma3:4b

# 4. Launch
python app.py
# Open http://localhost:7860
```

---

## Usage

1. (Optional) Enter your restaurant name and cuisine type for better context.
2. Choose the target language.
3. **Either** paste dish names (one per line) **or** upload a photo of your menu — or both.
4. Click **✨ Translate Menu**.
5. Copy the output. Export the JSON for integration with your POS or website.

### Sample menus

Try the included samples in `demo_menus/`:
- `indian_sample.txt` — North Indian classics
- `thai_sample.txt` — Thai street food

---

## Architecture

```
┌──────────────┐     image (optional)      ┌────────────────────┐
│  Gradio UI   │──────────────────────────▶│  Gemma 3 Vision    │
│  (browser)   │                           │  (OCR step)        │
└──────┬───────┘                           └────────┬───────────┘
       │ dish names                                  │ extracted text
       │◀────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  Gemma 3 Text  (Ollama, local, no internet needed)  │
│  System prompt: cultural adapter + JSON schema      │
└────────────────────────┬────────────────────────────┘
                         │ structured JSON
                         ▼
                  Rendered Markdown
                  + Raw JSON export
```

All inference happens on your machine via Ollama. No data leaves your network.

---

## Model swap

MenuMaestro is model-agnostic. To use a different Ollama model:

```python
# app.py — top of file
VISION_MODEL = "llava:13b"   # any vision-capable Ollama model
TEXT_MODEL   = "mistral:7b"  # any text Ollama model
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Links

- 📦 **GitHub:** [github.com/adibafna/menumaestro](https://github.com/adibafna/menumaestro)
- 🏷️ Part of [Hacktoberfest Open-Source AI Challenge: Week 2 — Side Hustle](https://dev.to/challenges/hf26)
