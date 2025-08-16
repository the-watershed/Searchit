"""
openai_client: Handles OpenAI API calls for image and annotation analysis.
"""
import base64
import json
import os


# Always load config.json from project root, regardless of CWD
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        OPENAI_API_KEY = config.get("openai_api_key", "")
else:
    OPENAI_API_KEY = ""



def analyze_image(image_path, annotation):
    """
    Analyze an image and annotation using OpenAI's vision API (openai>=1.0.0).
    Returns a string with maker, value, and provenance info.
    """
    from openai import OpenAI
    # Debug: print first 6 chars of key to log (never full key)
    if hasattr(analyze_image, 'log_box') and analyze_image.log_box:
        analyze_image.log_box.append(f"[DEBUG] OpenAI key loaded: {OPENAI_API_KEY[:6]}... (length: {len(OPENAI_API_KEY)})")
    client = OpenAI(api_key=OPENAI_API_KEY)
    with open(image_path, "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
    prompt = f"Analyze this item for maker, value, and provenance. Notes: {annotation}"
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": "You are a provenance expert for antiques and collectibles."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]}
            ],
            max_tokens=512
        )
        result = response.choices[0].message.content
        return result
    except Exception as e:
        return f"OpenAI error: {e}"
