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
    except ImportError:
        _log("[ERROR] OpenAI library not installed. Please install with: pip install openai")
        return "OpenAI error: Library not installed."
    except Exception as e:
        _log(f"[ERROR] Failed to initialize OpenAI client: {e}")
        return f"OpenAI error: {str(e)}"

    # Prepare image data for analysis
    image_content = []
    
    for i, image_path in enumerate(image_paths):
        if not os.path.exists(image_path):
            _log(f"[WARNING] Image not found: {image_path}")
            continue
            
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode()
                
            # Determine image format
            image_format = "jpeg"
            if image_path.lower().endswith(('.png', '.webp', '.gif')):
                image_format = image_path.split('.')[-1].lower()
                
            image_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{image_format};base64,{image_data}",
                    "detail": "high"
                }
            })
            
            # Add annotation if provided
            if annotations and i < len(annotations) and annotations[i]:
                image_content.append({
                    "type": "text",
                    "text": f"Caption for image {i+1}: {annotations[i]}"
                })
                
        except Exception as e:
            _log(f"[ERROR] Failed to process image {image_path}: {e}")
            continue

    if not image_content:
        return "OpenAI error: No valid images to analyze."

    # Build the analysis prompt
    prompt_text = """Analyze this artifact and provide structured information as JSON.

    Required JSON structure:
    {
      "title": "Brief descriptive title",
      "brand": "Brand name if visible/identifiable", 
      "maker": "Manufacturer if different from brand",
      "description": "Detailed description of the item",
      "condition": "Physical condition assessment",
      "provenance_notes": "Historical context, origin, or authenticity notes",
      "prices": {
        "low": estimated_low_value_number_or_null,
        "median": estimated_median_value_number_or_null, 
        "high": estimated_high_value_number_or_null
      },
      "confidence": confidence_score_0_to_1,
      "evidence": ["list", "of", "supporting", "details"],
      "ambiguities": ["list", "of", "uncertain", "aspects"]
    }
    
    Guidelines:
    - Use "Unknown" for any field where information cannot be determined
    - Be conservative with price estimates 
    - Include confidence score reflecting certainty
    - Focus on observable details and factual information
    - Consider rarity, condition, and market factors for pricing
    """

    messages = [
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": prompt_text}
            ] + image_content
        }
    ]

    try:
        _log("[OpenAI] Sending request to GPT-4 Vision...")
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=2000,
            temperature=0.1
        )
        
        result = response.choices[0].message.content
        _log(f"[OpenAI] Received response: {len(result)} characters")
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                # Validate JSON
                parsed = json.loads(json_str)
                _log("[OpenAI] Successfully extracted and validated JSON")
                return json_str
            else:
                _log("[OpenAI] No JSON found in response, returning raw text")
                return result
                
        except json.JSONDecodeError as e:
            _log(f"[OpenAI] JSON parsing failed: {e}, returning raw response")
            return result
            
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        _log(f"[ERROR] {error_msg}")
        return error_msg


# Legacy function for backward compatibility
def analyze_images_old(image_paths, annotations=None):
    """Backward compatibility wrapper."""
    return analyze_images(image_paths, annotations)
