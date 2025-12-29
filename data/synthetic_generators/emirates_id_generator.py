"""
EmiratesIDGenerator: Generate realistic Emirates ID card images
Production-grade, OCR-ready quality for M1
"""

from PIL import Image, ImageDraw, ImageFont
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path


class EmiratesIDGenerator:
    """Generate realistic UAE Emirates ID card images."""
    
    # ID card dimensions (standard credit card size: 85.6 x 53.98 mm)
    # At 300 DPI: approximately 1017x645 pixels
    WIDTH = 1017
    HEIGHT = 645
    
    def __init__(self):
        """Initialize EmiratesIDGenerator."""
        self.colors = {
            "background": (0, 51, 102),      # Dark blue
            "text": (255, 255, 255),         # White
            "accent": (255, 184, 28),        # Gold
            "border": (200, 200, 200)        # Light gray
        }
    
    def generate_id_card(
        self,
        full_name: str,
        emirates_id: str,
        date_of_birth: str,
        nationality: str = "UAE National",
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Generate realistic Emirates ID card image.
        
        Args:
            full_name: Full name of person
            emirates_id: Emirates ID number (XXX-YYYY-ZZZZZZZZ-C)
            date_of_birth: Date of birth (YYYY-MM-DD)
            nationality: Person's nationality
            output_path: Path to save image
            
        Returns:
            Dict: ID card data and image path
        """
        try:
            # Create image
            img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.colors["background"])
            draw = ImageDraw.Draw(img)
            
            # Try to load font, fallback to default if not available
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
                name_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
                label_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
                text_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
            except:
                # Fallback to default font
                title_font = ImageFont.load_default()
                name_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # Draw border
            border_width = 3
            draw.rectangle(
                [(0, 0), (self.WIDTH - 1, self.HEIGHT - 1)],
                outline=self.colors["accent"],
                width=border_width
            )
            
            # Top stripe with UAE flag colors (red, green, white, black)
            stripe_height = 80
            draw.rectangle(
                [(0, 0), (self.WIDTH, stripe_height)],
                fill=self.colors["accent"]
            )
            
            # Title
            draw.text(
                (50, 10),
                "UNITED ARAB EMIRATES",
                fill=self.colors["background"],
                font=title_font
            )
            draw.text(
                (50, 35),
                "IDENTITY CARD",
                fill=self.colors["background"],
                font=title_font
            )
            
            # Separater line
            draw.line(
                [(50, stripe_height + 10), (self.WIDTH - 50, stripe_height + 10)],
                fill=self.colors["accent"],
                width=2
            )
            
            # Name section
            y_pos = stripe_height + 30
            draw.text(
                (50, y_pos),
                f"Name: {full_name}",
                fill=self.colors["text"],
                font=name_font
            )
            
            # ID Number
            y_pos += 50
            draw.text(
                (50, y_pos),
                f"ID No: {emirates_id}",
                fill=self.colors["text"],
                font=text_font
            )
            
            # Date of Birth
            y_pos += 35
            draw.text(
                (50, y_pos),
                f"DOB: {date_of_birth}",
                fill=self.colors["text"],
                font=text_font
            )
            
            # Nationality
            y_pos += 35
            draw.text(
                (50, y_pos),
                f"Nationality: {nationality}",
                fill=self.colors["text"],
                font=text_font
            )
            
            # Issue and Expiry dates
            today = datetime.now()
            issue_date = (today - timedelta(days=365*3)).strftime("%Y-%m-%d")  # 3 years ago
            expiry_date = (today + timedelta(days=365*3)).strftime("%Y-%m-%d")  # 3 years ahead
            
            y_pos += 35
            draw.text(
                (50, y_pos),
                f"Issued: {issue_date}",
                fill=self.colors["text"],
                font=text_font
            )
            
            y_pos += 35
            draw.text(
                (50, y_pos),
                f"Expires: {expiry_date}",
                fill=self.colors["text"],
                font=text_font
            )
            
            # Save image
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                img.save(output_path, "PNG", quality=95)
            
            id_data = {
                "full_name": full_name,
                "emirates_id": emirates_id,
                "date_of_birth": date_of_birth,
                "nationality": nationality,
                "issue_date": issue_date,
                "expiry_date": expiry_date,
                "image_path": output_path,
                "image_size_kb": None
            }
            
            # Get file size
            if output_path:
                file_size = Path(output_path).stat().st_size
                id_data["image_size_kb"] = round(file_size / 1024, 2)
            
            return id_data
        
        except Exception as e:
            raise Exception(f"Error generating ID card: {str(e)}")


# Quick test
if __name__ == "__main__":
    gen = EmiratesIDGenerator()
    
    print("=" * 60)
    print("EMIRATES ID GENERATION TEST")
    print("=" * 60)
    
    id_data = gen.generate_id_card(
        full_name="Ahmed Al Mazrouei",
        emirates_id="784-1990-123456-7",
        date_of_birth="1990-05-15",
        nationality="UAE National"
    )
    
    print(f"\nID Card Generated:")
    print(f"  Name: {id_data['full_name']}")
    print(f"  ID: {id_data['emirates_id']}")
    print(f"  DOB: {id_data['date_of_birth']}")
    print(f"  Status: Ready for OCR testing")
