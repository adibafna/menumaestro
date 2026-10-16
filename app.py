"""
MenuMaestro — Local-first menu translation & cultural adaptation
Powered by Gemma 3 (vision) via Ollama
"""

import gradio as gr
import ollama
import base64
import json
import re
from pathlib import Path

# ── Model config ────────────────────────────────────────────────────────────
VISION_MODEL   = "gemma3:4b"   # multimodal; handles image + text
TEXT_MODEL     = "gemma3:4b"   # fallback for text-only input

TARGET_LANGUAGES = [
    "English (Tourist-Friendly)",
    "Spanish",
    "French",
    "German",
    "Japanese",
    "Mandarin Chinese",
    "Arabic",
    "Hindi",
    "Portuguese",
    "Italian",
    "Korean",
    "Russian",
]

DIETARY_FLAGS = ["Vegan", "Vegetarian", "Gluten-Free", "Nut-Free", "Halal", "Kosher", "Dairy-Free"]

SYSTEM_PROMPT = """You are MenuMaestro, an expert menu translator and cultural adapter for restaurant owners.

Your job:
1. Read the menu items (from text OR a photo of a menu).
2. For EACH dish:
   - Provide a culturally adapted name in the target language (not a literal word-for-word translation, but something a native speaker would naturally say).
   - Write an appetising 1–2 sentence description that explains ingredients and cooking style in a way the target audience understands.
   - List which dietary flags apply: {flags}
   - Add a "Cultural Note" (one sentence) if the dish has cultural significance or a common misconception foreign guests have about it.
3. Output ONLY valid JSON in this exact schema (no markdown fences, no commentary):

{{
  "dishes": [
    {{
      "original": "Original dish name",
      "translated_name": "Name in target language",
      "description": "Appetising description",
      "dietary_flags": ["flag1", "flag2"],
      "cultural_note": "One sentence or empty string"
    }}
  ],
  "restaurant_tagline": "A short, catchy tagline for the restaurant in the target language (1 sentence)"
}}
""".format(flags=", ".join(DIETARY_FLAGS))


# ── Helpers ──────────────────────────────────────────────────────────────────

def encode_image(image_path: str) -> str:
    """Base64-encode an image file for the Ollama vision API."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def parse_response(raw: str) -> dict:
    """Extract JSON from model output, tolerating fenced code blocks."""
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find the first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Model did not return valid JSON. Raw output:\n" + raw)


def build_prompt(menu_text: str, target_lang: str, restaurant_name: str, cuisine_type: str) -> str:
    context_parts = []
    if restaurant_name:
        context_parts.append(f"Restaurant name: {restaurant_name}")
    if cuisine_type:
        context_parts.append(f"Cuisine type: {cuisine_type}")
    context = "\n".join(context_parts)

    return f"""{context}

Target language: {target_lang}

Menu items to translate and adapt:
{menu_text}

Remember: output ONLY the JSON object, nothing else."""


def format_output(data: dict) -> str:
    """Convert parsed JSON into a readable Markdown table for display."""
    lines = []

    tagline = data.get("restaurant_tagline", "")
    if tagline:
        lines.append(f"**✨ Suggested tagline:** _{tagline}_\n")

    lines.append("---\n")

    for i, dish in enumerate(data.get("dishes", []), 1):
        lines.append(f"### {i}. {dish.get('original', '?')} → **{dish.get('translated_name', '?')}**")
        lines.append(f"> {dish.get('description', '')}")

        flags = dish.get("dietary_flags", [])
        if flags:
            flag_str = " ".join(f"`{f}`" for f in flags)
            lines.append(f"\n**Dietary:** {flag_str}")

        note = dish.get("cultural_note", "")
        if note:
            lines.append(f"\n💡 *{note}*")

        lines.append("")  # blank line between dishes

    return "\n".join(lines)


# ── Core translation function ────────────────────────────────────────────────

def translate_menu(
    menu_text: str,
    image_path,
    restaurant_name: str,
    cuisine_type: str,
    target_lang: str,
    progress=gr.Progress(track_tqdm=True),
):
    if not menu_text.strip() and image_path is None:
        return "⚠️ Please enter menu text **or** upload a menu photo.", "{}"

    progress(0, desc="Connecting to local Gemma model…")

    try:
        # ── Vision path: photo of menu ───────────────────────────────────
        if image_path is not None:
            progress(0.2, desc="Reading menu photo with Gemma vision…")
            img_b64 = encode_image(image_path)

            ocr_prompt = (
                "This is a photo of a restaurant menu. "
                "Extract every dish name you can see, one per line, preserving the original language. "
                "Output ONLY the dish names, nothing else."
            )

            ocr_response = ollama.chat(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": ocr_prompt,
                        "images": [img_b64],
                    }
                ],
            )
            extracted_items = ocr_response["message"]["content"].strip()

            # Merge with any manually typed items
            combined_text = (menu_text.strip() + "\n" + extracted_items).strip()
        else:
            combined_text = menu_text.strip()

        progress(0.5, desc=f"Translating to {target_lang}…")

        prompt = build_prompt(combined_text, target_lang, restaurant_name, cuisine_type)

        response = ollama.chat(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )

        raw_output = response["message"]["content"]
        progress(0.85, desc="Parsing response…")

        parsed = parse_response(raw_output)
        formatted = format_output(parsed)

        progress(1.0, desc="Done!")
        return formatted, json.dumps(parsed, ensure_ascii=False, indent=2)

    except Exception as exc:
        err = f"❌ **Error:** {exc}\n\n*Is Ollama running? Try: `ollama serve` in a terminal.*"
        return err, "{}"


# ── Gradio UI ────────────────────────────────────────────────────────────────

DESCRIPTION = """
# 🍽️ MenuMaestro
**Local-first menu translation & cultural adaptation — powered by Gemma 3 via Ollama.**

Everything runs on your machine. Your menu never leaves your laptop.
Paste dish names, or drop in a photo of your handwritten menu, and get back:
- Culturally adapted names (not robotic literal translations)
- Appetising descriptions your guests will actually understand
- Dietary flags (Vegan · Gluten-Free · Halal · …)
- A suggested restaurant tagline in the target language

---
"""

with gr.Blocks(title="MenuMaestro") as demo:
    gr.Markdown(DESCRIPTION)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Your Menu")

            restaurant_name = gr.Textbox(
                label="Restaurant name (optional)",
                placeholder="e.g. Spice Garden",
            )
            cuisine_type = gr.Textbox(
                label="Cuisine type (optional)",
                placeholder="e.g. North Indian, Cantonese, Oaxacan…",
            )
            target_lang = gr.Dropdown(
                choices=TARGET_LANGUAGES,
                value="English (Tourist-Friendly)",
                label="Translate to",
            )
            menu_text = gr.Textbox(
                label="Dish names (one per line)",
                placeholder="Dum Aloo\nLaal Maas\nMakki ki Roti\nSarson ka Saag",
                lines=8,
            )
            image_input = gr.Image(
                label="Or upload a photo of your menu (optional)",
                type="filepath",
            )
            translate_btn = gr.Button("✨ Translate Menu", variant="primary")

        with gr.Column(scale=2):
            gr.Markdown("### 🌐 Translated Menu")
            output_md = gr.Markdown(value="*Your translated menu will appear here…*")

            with gr.Accordion("📄 Raw JSON (for developers / export)", open=False):
                output_json = gr.Code(language="json", label="JSON Output")

    translate_btn.click(
        fn=translate_menu,
        inputs=[menu_text, image_input, restaurant_name, cuisine_type, target_lang],
        outputs=[output_md, output_json],
    )

    gr.Markdown("""
---
**🔒 Privacy:** Nothing leaves your machine. MenuMaestro runs Gemma 3 locally via Ollama.  
**📦 Open source:** Apache-2.0 · [GitHub](https://github.com/yourusername/menumaestro)
""")


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, theme=gr.themes.Soft())
