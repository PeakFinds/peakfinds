#!/usr/bin/env python3
# generate_article.py
import os, sys, json, datetime, hashlib, textwrap, random, requests
from PIL import Image, ImageDraw, ImageFont

CONFIG_PATH = "config.json"
TEMPLATES_DIR = "templates"
IMAGES_DIR = "images"
OUTPUT_DIR = "docs"

# --- Utilities
def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("Missing config.json. Copy config.example.json -> config.json and edit.")
        sys.exit(1)
    return json.load(open(CONFIG_PATH))

def slugify(s):
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")[:100]

def safe_filename(s):
    return "".join(c for c in s if c.isalnum() or c in "-_ ").rstrip()

# --- Niche-specific helper: produce a keyword/title
KEYWORD_BUCKET = [
    "best budget monitor stand",
    "laptop stand for posture",
    "ergonomic keyboard for students",
    "desk chair for back pain under $150",
    "compact standing desk for dorm",
    "best desk lamp for studying",
    "ergonomic mouse for small hands",
    "desk organization ideas for small desks",
]

def pick_topic():
    return random.choice(KEYWORD_BUCKET)

# --- Text generation via HuggingFace Inference API (optional)
def hf_generate(prompt, hf_key, max_tokens=350):
    if not hf_key:
        return None
    url = "https://api-inference.huggingface.co/models/gpt2"
    headers = {"Authorization": f"Bearer {hf_key}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens, "temperature": 0.7}}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]
        return str(data)
    except Exception as e:
        print("HF generation failed:", e)
        return None

# --- Fallback template generator
def fallback_generate(title, keyword):
    intro = f"{title}\n\nStudying or working long hours? Setting up an ergonomic workspace doesn't have to be expensive. In this guide we cover practical, budget-friendly picks and posture tips for students and remote workers."
    sections = []
    for i in range(3):
        s = ("Tip %d: " % (i+1)) + random.choice([
            f"Choose an adjustable stand that raises your screen to eye level to prevent neck strain.",
            f"Use a separate keyboard and mouse to keep wrists neutral and reduce shoulder tension.",
            f"Opt for a chair with lumbar support or add a lumbar cushion for under $30.",
            f"Keep your feet flat and knees at 90° — add a cheap footrest if needed.",
            f"Use a desk lamp with adjustable brightness and color temperature for less eye strain."
        ])
        sections.append(s)
    conclusion = "Small changes to furniture and posture can make studying more comfortable and help prevent long-term issues."
    return "\n\n".join([intro] + sections + [conclusion])

# --- Image generator (simple header image using Pillow)
def make_header_image(title, outpath):
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    W, H = 1200, 630
    img = Image.new("RGB", (W,H), color=(245,245,250))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()
    lines = textwrap.wrap(title, width=28)
    y = 120
    for line in lines:
        w,h = draw.textsize(line, font=font)
        draw.text(((W-w)/2, y), line, fill=(20,20,60), font=font)
        y += h + 8
    footer = "ErgoStudentGear"
    try:
        font2 = ImageFont.truetype("DejaVuSans.ttf", 18)
    except:
        font2 = ImageFont.load_default()
    w,h = draw.textsize(footer, font=font2)
    draw.text(((W-w)/2, H-80), footer, fill=(100,100,120), font=font2)
    img.save(outpath, quality=85)

# --- Main generator
def generate_one(cfg):
    keyword = pick_topic()
    title = " ".join([w.capitalize() for w in keyword.split()][:8])
    prompt = f"Write a friendly, informative 550-900 word article for students and remote workers about '{keyword}'. Include 3 short product recommendation blurbs (each ~50 words). Use an upbeat, helpful tone and add a short 3-bullet quick tips list."
    hf_key = cfg.get("hf_api_key","").strip()
    text = hf_generate(prompt, hf_key) if hf_key else None
    if not text:
        text = fallback_generate(title, keyword)

    date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    slug = slugify(title + "-" + date)
    md_filename = f"{date}-{slug}.md"
    image_name = f"{slug}.jpg"
    image_path = os.path.join(IMAGES_DIR, image_name)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    make_header_image(title, image_path)

    tag = cfg.get("amazon_affiliate_tag","")
    af_link = f"https://www.amazon.com/s?k={keyword.replace(' ','+')}"+ (f"&tag={tag}" if tag else "")
    md = f"""---
title: "{title}"
date: {date}
author: "{cfg.get('author_name','ErgoBot')}"
categories: ["{cfg.get('default_category','Ergonomics')}"]
image: /{IMAGES_DIR}/{image_name}
---

{ text.strip() }

---

**Recommended:** [Find recommended ergonomic gear on Amazon]({af_link})
"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_md_path = os.path.join(OUTPUT_DIR, md_filename)
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print("Generated:", out_md_path)
    return out_md_path, image_path

if __name__ == "__main__":
    cfg = load_config()
    n = int(cfg.get("posts_per_run",1))
    results = []
    for i in range(n):
        md_path, img_path = generate_one(cfg)
        results.append((md_path, img_path))
    print("Done. Generated", len(results), "posts.")
