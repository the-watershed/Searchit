"""
openai_client: Handles OpenAI API calls for image and annotation analysis using secure key storage.
"""
import json
import os
import sys
import base64
from typing import List, Optional

def _log(msg):
    """Log to console and file for debugging."""
    print(msg)
    try:
        with open("trace.log", "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except Exception:
        pass

def analyze_images(image_paths: List[str], annotations: Optional[List[str]] = None) -> str:
    """
    Analyze multiple images and annotations as a single artifact using OpenAI's vision API.
    Uses secure key storage to protect API credentials.

    Args:
        image_paths: List of file paths to images
        annotations: List of captions/annotations for each image (optional)

    Returns:
        JSON string containing structured analysis data
    """
    _log(f"[OpenAI] Starting analysis of {len(image_paths)} images")
    
    try:
        from secure_storage import get_openai_api_key
        api_key = get_openai_api_key()
    except ImportError:
        # Fallback to old method if secure_storage not available
        _log("[OpenAI] Warning: secure_storage not available, falling back to config.json")
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("openai_api_key", "").strip()
        except Exception as e:
            _log(f"[ERROR] Could not load OpenAI key: {e}")
            api_key = ""
    
    _log(f"[DEBUG] OpenAI key loaded: {api_key[:6] if api_key else 'NONE'}... (length: {len(api_key)})")
    
    if not api_key:
        _log("[ERROR] No OpenAI API key found. Please check secure storage or environment variables.")
        return "OpenAI error: No API key provided. Please set your API key in Settings or environment variable SEARCHIT_OPENAI_API_KEY."
    
    if not (api_key.startswith("sk-") or api_key.startswith("sess-")):
        _log(f"[ERROR] API key format looks invalid: {api_key[:10]}...")
        return "OpenAI error: Invalid API key format."

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    """
    Analyze multiple images and annotations as a single artifact using OpenAI's vision API.
    Returns a JSON string with fields:
      {
        "title": str, "brand": str, "maker": str, "description": str,
        "condition": str, "provenance_notes": str,
        "prices": {"low": number|null, "median": number|null, "high": number|null},
        "confidence": number (0..1),
        "evidence": [str],
        "ambiguities": [str]
      }
    Unknown fields must be "Unknown"; do not guess.
    """
    from openai import OpenAI
    api_key = ""
    log_box = getattr(analyze_images, 'log_box', None)
    def _log(msg):
        try:
            if log_box:
                log_box.append(msg)
        except Exception:
            pass

    _log(f"[DEBUG] (START) Looking for config at: {CONFIG_PATH}")
    _log(f"[DEBUG] (START) Config exists: {os.path.exists(CONFIG_PATH)}")
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                api_key = config.get("openai_api_key", "").strip()
        except Exception as e:
            _log(f"[ERROR] Could not load OpenAI key: {e}")
    _log(f"[DEBUG] OpenAI key loaded: {api_key[:6]}... (length: {len(api_key)})")
    if not api_key:
        _log("[ERROR] No OpenAI API key found. Please check config.json and Settings.")
        return "OpenAI error: No API key provided."
    if not (api_key.startswith("sk-") or api_key.startswith("sess-")):
        _log(f"[ERROR] API key format looks invalid: {api_key[:10]}...")
    client = OpenAI(api_key=api_key)

    # Prepare images with high-detail and captions
    images_content = []
    captions = []
    for idx, path in enumerate(image_paths, start=1):
        try:
            with open(path, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
            images_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}", "detail": "high"}
            })
            captions.append(f"Image {idx}: {os.path.basename(path)}")
        except Exception as e:
            _log(f"[WARN] Could not load image {path}: {e}")

    # Accept optional metadata from caller (e.g., UploadPage): captions and OCR hints
    meta = getattr(analyze_images, 'meta', None)
    meta_captions = None
    meta_ocr = None
    try:
        if isinstance(meta, dict):
            mc = meta.get('captions')
            mo = meta.get('ocr_hints')
            if isinstance(mc, list) and mc:
                meta_captions = [str(x) for x in mc]
            if isinstance(mo, list) and mo:
                meta_ocr = [str(x) for x in mo]
    except Exception:
        meta_captions = None
        meta_ocr = None

    # If caller provided captions, prefer them; else use defaults
    if meta_captions:
        try:
            # Normalize length to number of images
            if len(meta_captions) < len(image_paths):
                meta_captions += [""] * (len(image_paths) - len(meta_captions))
            captions = [f"Image {i+1}: {meta_captions[i]}" if meta_captions[i] else captions[i]
                        for i in range(len(image_paths))]
        except Exception:
            pass

    # Aggregate OCR hints and user notes
    user_notes = "\n".join([a for a in annotations if a]) if annotations else ""
    ocr_block = ""
    if meta_ocr:
        # Trim or pad to match number of images
        if len(meta_ocr) < len(image_paths):
            meta_ocr += [""] * (len(image_paths) - len(meta_ocr))
        lines = []
        for i, text in enumerate(meta_ocr, start=1):
            if text and text.strip():
                lines.append(f"[OCR {i}] {text.strip()}")
        if lines:
            ocr_block = "\n" + "\n".join(lines)

    def _call(messages, max_tokens=900):
        return client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
            max_tokens=max_tokens,
        )

    schema_hint = (
        "Return ONLY a valid JSON object with keys: title, brand, maker, description, condition, "
        "provenance_notes, prices {low, median, high}, confidence (0..1), evidence (array of strings), ambiguities (array of strings). "
        "If unknown, set the string value to 'Unknown' or the price value to null. Cite evidence using [img:N] and short notes."
    )

    system_msg = {"role": "system", "content": (
        "You are a provenance expert for antiques and collectibles. "
        "Be precise and conservative; avoid hallucinations. Only extract what is supported by visible evidence."
    )}
    user_intro = (
        "All images and notes below are of the same artifact. Analyze them as a whole and extract structured facts.\n"
        f"Per-image captions:\n{chr(10).join(captions)}\n\n"
        f"UserNotes:\n{user_notes}{ocr_block}\n\n"
        + schema_hint
    )

    # Pass 1: initial extraction with ambiguities listed
    try:
        resp1 = _call([
            system_msg,
            {"role": "user", "content": [{"type": "text", "text": user_intro}] + images_content},
        ])
        txt1 = resp1.choices[0].message.content or ""
    except Exception as e:
        return f"OpenAI error: {e}"

    def _parse_json(txt):
        try:
            return json.loads(txt), None
        except Exception as e:
            return None, str(e)

    data, err = _parse_json(txt1)
    if data is None:
        _log("[DEBUG] First pass returned non-JSON; requesting JSON-only reformat...")
        # Retry: ask for JSON-only reformat
        try:
            resp_fix = _call([
                system_msg,
                {"role": "user", "content": [{"type": "text", "text": user_intro + "\nReturn ONLY the JSON object, no prose."}] + images_content},
            ], max_tokens=700)
            txt_fix = resp_fix.choices[0].message.content or ""
            data, err = _parse_json(txt_fix)
        except Exception as e:
            return f"OpenAI error: {e}"
        if data is None:
            return txt1 or txt_fix or "OpenAI error: Could not parse JSON response."

    # Pass 2: refinement focusing on unknowns/ambiguities
    try:
        unknown_keys = [k for k, v in data.items() if isinstance(v, str) and v.strip().lower() == 'unknown']
        amb = data.get('ambiguities') or []
        if unknown_keys or amb:
            refine_prompt = (
                "Refine the previous JSON using the same images. Only fill fields that are clearly supported by visible evidence.\n"
                f"Unknown fields: {unknown_keys}. Ambiguities: {amb}.\n"
                "Return ONLY the full JSON object in the same schema."
            )
            resp2 = _call([
                system_msg,
                {"role": "user", "content": [{"type": "text", "text": refine_prompt}] + images_content},
            ], max_tokens=900)
            txt2 = resp2.choices[0].message.content or ""
            data2, err2 = _parse_json(txt2)
            if data2:
                data = data2
    except Exception as e:
        _log(f"[WARN] Refinement step skipped due to error: {e}")

    # Pretty-print JSON string as final result
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        return str(data)

# Backward compatibility: single image
def analyze_image(image_path, annotation):
    return analyze_images([image_path], [annotation])
