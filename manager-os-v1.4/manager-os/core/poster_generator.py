"""
MANAGER OS — Poster Generation Engine
FILE: core/poster_generator.py
CREATED: 2026-06-06 | Claude Sonnet 4.6
PURPOSE: Generates beautiful invitation posters.
         Uses DALL-E for background image (if keys exist),
         then draws stylized invitation text overlays using Pillow.
         Includes a 100% reliable local gradient generator fallback.
"""

import os
import requests
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from loguru import logger
from openai import OpenAI

def get_font(font_name: str = "arial.ttf", size: int = 24) -> ImageFont.ImageFont:
    """Safe font loading wrapper."""
    try:
        # Standard paths for fonts on Windows
        paths = [
            f"C:\\Windows\\Fonts\\{font_name}",
            font_name
        ]
        for p in paths:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()

def draw_gradient_background(width: int, height: int) -> Image.Image:
    """Generate a premium dark neon gradient background locally."""
    base = Image.new("RGBA", (width, height), (10, 5, 20, 255)) # Deep dark purple
    draw = ImageDraw.Draw(base)
    
    # Draw linear gradient from top-left to bottom-right
    for y in range(height):
        # Blend colors from deep purple to dark blue/magenta
        r = int(10 + (30 * y / height))
        g = int(5 + (10 * y / height))
        b = int(20 + (50 * y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        
    # Draw some stylized glowing neon circles in the background
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ol_draw = ImageDraw.Draw(overlay)
    
    # Cyan glow circle
    ol_draw.ellipse([(-100, -100), (300, 300)], fill=(0, 212, 255, 30))
    # Magenta glow circle
    ol_draw.ellipse([(width - 300, height - 300), (width + 100, height + 100)], fill=(255, 0, 127, 25), outline=None)
    
    # Blur the glow overlay for a soft neon effect
    overlay = overlay.filter(ImageFilter.GaussianBlur(50))
    
    # Combine base and overlay
    final_bg = Image.alpha_composite(base, overlay)
    return final_bg

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list:
    """Wrap text to fit within a maximum pixel width."""
    words = text.split(' ')
    lines = []
    current_line = []
    
    # Simple bounding box measurement wrapper
    def get_width(t):
        if hasattr(font, 'getbbox'):
            return font.getbbox(t)[2]
        return len(t) * 10  # Fallback
        
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if get_width(test_line) > max_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(' '.join(current_line))
    return lines

async def generate_invite_poster(
    title: str,
    details: str,
    theme: str = "party",
    output_path: str = "./logs/invite_poster.png",
    config: Optional[dict] = None
) -> str:
    """Generate invite poster, returns absolute path of the poster."""
    logger.info(f"Generating invite poster. Title: '{title}', Theme: '{theme}'")
    
    # Standard poster dimensions
    width, height = 600, 800
    background = None
    
    # Attempt AI Background Generation if OpenAI API Key exists
    openai_key = config.get("api_keys", {}).get("openai") if config else None
    if openai_key:
        try:
            logger.info("Triggering OpenAI DALL-E for background image...")
            client = OpenAI(api_key=openai_key)
            prompt = (
                f"Sleek abstract dark neon {theme} gradient background, glowing ambient light, "
                "no text, no letters, high-resolution graphic design background"
            )
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response.data[0].url
            img_data = requests.get(image_url).content
            
            # Load and resize to target size
            ai_img = Image.open(BytesIO(img_data)).convert("RGBA")
            background = ai_img.resize((width, height), Image.Resampling.LANCZOS)
            logger.info("AI background generation successful.")
        except Exception as e:
            logger.warning(f"AI background generation failed: {e}. Falling back to local gradient.")
            
    if background is None:
        background = draw_gradient_background(width, height)
        
    # Create Draw Context
    draw = ImageDraw.Draw(background)
    
    # Load fonts
    title_font = get_font("impact.ttf", 48)
    header_font = get_font("arial.ttf", 20)
    details_font = get_font("arial.ttf", 26)
    footer_font = get_font("arial.ttf", 16)
    
    # Draw double glowing neon border
    # Outer cyan border
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(0, 212, 255, 200), width=3)
    # Inner magenta border
    draw.rectangle([(15, 15), (width - 15, height - 15)], outline=(255, 0, 127, 180), width=1)
    
    # Calculate title dimensions and draw with drop-shadow
    title_text = title.upper()
    title_lines = wrap_text(title_text, title_font, width - 80)
    
    y_cursor = 80
    
    # Header / Invitation Callout
    callout = "YOU ARE CORDIALLY INVITED TO"
    c_w = draw.textlength(callout, font=header_font)
    draw.text(((width - c_w)//2, y_cursor), callout, fill=(0, 212, 255, 230), font=header_font)
    y_cursor += 50
    
    # Draw Title Lines
    for line in title_lines:
        t_w = draw.textlength(line, font=title_font)
        x_pos = (width - t_w) // 2
        # Title Shadow
        draw.text((x_pos + 3, y_cursor + 3), line, fill=(0, 0, 0, 180), font=title_font)
        # Title Main Text (Glowing white/neon magenta)
        draw.text((x_pos, y_cursor), line, fill=(255, 255, 255, 255), font=title_font)
        y_cursor += 60
        
    y_cursor += 30
    
    # Draw Details Divider Line
    draw.line([(100, y_cursor), (width - 100, y_cursor)], fill=(255, 0, 127, 150), width=2)
    y_cursor += 50
    
    # Format and Draw Details (e.g. Date, Venue, Time)
    detail_lines = [line.strip() for line in details.split('\n') if line.strip()]
    for d_line in detail_lines:
        # Check if line contains a label like "Date:" or "Venue:" to make it stand out
        parts = d_line.split(':', 1)
        if len(parts) == 2:
            label, val = parts[0] + ":", parts[1]
            # Draw label in cyan, value in white
            lbl_w = draw.textlength(label, font=details_font)
            val_w = draw.textlength(val, font=details_font)
            total_w = lbl_w + val_w
            x_start = (width - total_w) // 2
            
            draw.text((x_start, y_cursor), label, fill=(0, 212, 255, 255), font=details_font)
            draw.text((x_start + lbl_w, y_cursor), val, fill=(255, 255, 255, 255), font=details_font)
        else:
            d_w = draw.textlength(d_line, font=details_font)
            draw.text(((width - d_w)//2, y_cursor), d_line, fill=(255, 255, 255, 255), font=details_font)
            
        y_cursor += 45
        
    # Draw Footer
    y_cursor = height - 80
    footer_text = "MANAGER OS — EXECUTED ON BEHALF OF ANANT"
    f_w = draw.textlength(footer_text, font=footer_font)
    draw.text(((width - f_w)//2, y_cursor), footer_text, fill=(255, 255, 255, 100), font=footer_font)
    
    # Save Image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    background.save(output_path, "PNG")
    abs_path = os.path.abspath(output_path)
    logger.info(f"Poster successfully saved at: {abs_path}")
    return abs_path
