import os, datetime, json, requests

# --- Config ---
MODEL = "gpt-4o-mini"  # low-cost, good quality; change if you prefer
TOPICS = [
    "AI technology trends", "productivity hacks", "budgeting and saving money",
    "fitness and recovery tips", "learning faster", "side hustles",
    "simple cooking and meal prep", "career growth tips", "sleep and focus",
    "digital minimalism", "travel on a budget"
]
# ---------------

def get_api_key():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return key or None

def generate_article(topic, api_key):
    # Use Chat Completions via HTTP for maximal compatibility
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = (
        f"Write a ~600-word blog post about {topic}. "
        "Use a clear H1 title, short intro, 3–5 skimmable sections with H2s, "
        "practical tips, and a brief conclusion. Keep it original and friendly."
    )
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 900,
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def fallback_article(topic):
    # Fallback content if API key is missing or API call fails
    return f"""# {topic}: Quick Guide

**Heads up:** This post used a fallback generator (no API credit or key issue).

## Why it matters
A fast primer on {topic} with practical steps you can use today.

## What to do first
- Keep it simple
- Track your actions
- Iterate weekly

## 3 quick tips
1) Start small.  
2) Remove friction.  
3) Celebrate tiny wins.

## Wrap-up
Short and sweet so you can take action now.
"""

def main():
    today = datetime.date.today().strftime("%Y-%m-%d")
    api_key = get_api_key()

    # Rotate topics so posts vary
    idx = datetime.date.today().toordinal() % len(TOPICS)
    topic = TOPICS[idx]

    try:
        if not api_key:
            content = fallback_article(topic)
            title_line = content.splitlines()[0].lstrip("# ").strip()
        else:
            content = generate_article(topic, api_key)
            # Try to extract a title from the first line; if none, synthesize
            first = content.splitlines()[0].strip()
            title_line = first.lstrip("# ").strip() if first.startswith("#") else f"{topic} — {today}"
    except Exception as e:
        # If API errors, fall back so the workflow still succeeds
        content = fallback_article(topic) + f"\n\n> Note: API error: {e}"
        title_line = f"{topic} — {today} (fallback)"

    # Ensure _posts exists
    os.makedirs("_posts", exist_ok=True)

    # Minimal Jekyll front matter
    fm = f"---\ntitle: \"{title_line}\"\ndate: {today}\n---\n\n"
    filename = f"_posts/{today}-auto-post.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(fm + content)

    print(f"✅ Saved: {filename}")

if __name__ == "__main__":
    main()
