import io
import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CAPTCHA_CHARS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'

def generate_captcha_text(length=5):
    """Generate a randomized alphanumeric CAPTCHA text omitting ambiguous chars."""
    return ''.join(random.choices(CAPTCHA_CHARS, k=length))

def _get_font(size=32):
    """Attempt to load standard system fonts or fallback to default."""
    font_candidates = [
        'C:/Windows/Fonts/segoeuib.ttf',
        'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/calibrib.ttf',
        'C:/Windows/Fonts/calibri.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    ]
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def generate_captcha_image(text, width=180, height=54):
    """
    Generate a high-contrast, modern dark-themed CAPTCHA image.
    
    Args:
        text: The string to render in the CAPTCHA.
        width: Image width in pixels.
        height: Image height in pixels.
        
    Returns:
        io.BytesIO: PNG image byte stream.
    """
    # Create dark slate background
    image = Image.new('RGB', (width, height), color=(15, 23, 42)) # Slate 900
    draw = ImageDraw.Draw(image)

    # Add gradient / noise lines in background
    for y in range(height):
        # Subtle horizontal gradient
        r = int(15 + (y / height) * 15)
        g = int(23 + (y / height) * 18)
        b = int(42 + (y / height) * 20)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Background random dots / noise
    for _ in range(60):
        dot_x = random.randint(0, width - 1)
        dot_y = random.randint(0, height - 1)
        dot_color = (
            random.randint(40, 90),
            random.randint(60, 120),
            random.randint(90, 160)
        )
        draw.point((dot_x, dot_y), fill=dot_color)

    # Background random curved lines
    for _ in range(3):
        x1 = random.randint(0, width // 3)
        y1 = random.randint(0, height)
        x2 = random.randint(width // 3, 2 * width // 3)
        y2 = random.randint(0, height)
        x3 = random.randint(2 * width // 3, width)
        y3 = random.randint(0, height)
        line_color = (
            random.randint(50, 100),
            random.randint(90, 160),
            random.randint(120, 200)
        )
        draw.line([(x1, y1), (x2, y2), (x3, y3)], fill=line_color, width=1)

    # Vibrant text colors for high readability against dark background
    palette = [
        (56, 189, 248),   # Sky blue
        (52, 211, 153),   # Emerald green
        (251, 191, 36),   # Amber/Gold
        (244, 114, 182),  # Pink
        (167, 139, 250),  # Purple
        (94, 234, 212),   # Teal
        (248, 113, 113),  # Coral
    ]

    font = _get_font(size=random.randint(28, 34))

    # Render each character with slight rotation and offset onto individual char surfaces
    char_spacing = (width - 30) // len(text)
    
    for i, char in enumerate(text):
        char_color = random.choice(palette)
        
        # Create a small RGBA image for rotating the single character
        char_img = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        
        # Position char roughly in center
        char_draw.text((10, 4), char, font=font, fill=char_color)
        
        # Random rotation between -20 and 20 degrees
        angle = random.uniform(-20, 20)
        rotated_char = char_img.rotate(angle, resample=Image.BICUBIC, expand=1)
        
        # Calculate placement
        pos_x = 12 + i * char_spacing + random.randint(-2, 3)
        pos_y = (height - rotated_char.height) // 2 + random.randint(-3, 3)
        
        # Paste onto main image with alpha mask
        image.paste(rotated_char, (pos_x, pos_y), rotated_char)

    # Foreground interference line across characters
    fx1 = random.randint(5, 25)
    fy1 = random.randint(10, height - 10)
    fx2 = width - random.randint(5, 25)
    fy2 = random.randint(10, height - 10)
    draw.line([(fx1, fy1), (fx2, fy2)], fill=(148, 163, 184), width=1)

    # Save to in-memory bytes
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return buf
