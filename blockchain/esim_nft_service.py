"""
AstraLink - eSIM NFT Service
============================

Handles eSIM QR code generation, NFT metadata creation, and artwork generation
for the EnhancedDynamicESIMNFT contract.
"""

import qrcode
from PIL import Image, ImageDraw, ImageFilter
import json
import aioipfs
import asyncio
from typing import Dict, Any, Tuple
import io
import base64
from web3 import Web3
import random
from pathlib import Path
import yaml
from logging_config import get_logger

logger = get_logger(__name__)

class ESIMNFTService:
    def __init__(self, ipfs_client=None):
        self.ipfs_client = ipfs_client or aioipfs.AsyncIPFS()
        self.theme_colors = {
            "cosmic": [(25, 25, 112), (138, 43, 226), (75, 0, 130)],  # Deep space blues and purples
            "quantum": [(0, 255, 255), (255, 0, 255), (0, 255, 0)],   # Bright quantum colors
            "cyber": [(0, 255, 0), (255, 0, 98), (0, 234, 255)],      # Cyberpunk neons
            "nebula": [(255, 192, 203), (147, 112, 219), (0, 191, 255)], # Nebula pastels
            "matrix": [(0, 255, 0), (0, 200, 0), (0, 150, 0)]         # Matrix greens
        }

    async def generate_activation_qr(self, esim_data: Dict[str, Any]) -> Tuple[str, bytes]:
        """Generate QR code for eSIM activation and upload to IPFS"""
        try:
            # Create QR code with eSIM activation data
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            
            # Format eSIM activation data
            activation_data = {
                "type": "eSIM",
                "carrier": esim_data["carrier"],
                "activationCode": esim_data["activation_code"],
                "tokenId": esim_data["token_id"],
                "bandwidth": esim_data["bandwidth"]
            }
            
            qr.add_data(json.dumps(activation_data))
            qr.make(fit=True)

            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Add AstraLink branding
            final_img = self._add_branding_to_qr(qr_img)
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            final_img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Upload to IPFS
            ipfs_hash = await self.ipfs_client.add(img_bytes)
            
            return ipfs_hash, img_bytes

        except Exception as e:
            logger.error(f"Failed to generate QR code: {str(e)}")
            raise

    async def generate_nft_artwork(self, token_id: int, theme: str, rarity: int) -> str:
        """Generate unique NFT artwork based on theme and rarity"""
        try:
            # Create base image
            width, height = 1024, 1024
            image = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(image)
            
            # Get theme colors
            colors = self.theme_colors.get(theme, self.theme_colors["cosmic"])
            
            # Generate artistic elements based on rarity
            self._generate_artistic_elements(image, draw, colors, rarity)
            
            # Add theme-specific effects
            image = self._apply_theme_effects(image, theme)
            
            # Convert to bytes and upload to IPFS
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            ipfs_hash = await self.ipfs_client.add(img_bytes)
            return f"ipfs://{ipfs_hash}"

        except Exception as e:
            logger.error(f"Failed to generate NFT artwork: {str(e)}")
            raise

    def _add_branding_to_qr(self, qr_img: Image.Image) -> Image.Image:
        """Add AstraLink branding to QR code"""
        # Create new image with padding for branding
        final_size = (qr_img.size[0] + 40, qr_img.size[1] + 60)
        final_img = Image.new('RGB', final_size, 'white')
        
        # Paste QR code
        final_img.paste(qr_img, (20, 20))
        
        # Add branding text
        draw = ImageDraw.Draw(final_img)
        draw.text((final_size[0]//2, final_size[1]-25), 
                 "AstraLink eSIM", 
                 fill='black',
                 anchor="mm")
        
        return final_img

    def _generate_artistic_elements(self, image: Image.Image, draw: ImageDraw.Draw, 
                                 colors: list, rarity: int) -> None:
        """Generate artistic elements based on rarity"""
        width, height = image.size
        
        # Number of elements based on rarity
        num_elements = int(rarity / 100) + 5
        
        for _ in range(num_elements):
            # Generate random shapes and patterns
            shape_type = random.choice(['circle', 'line', 'rectangle'])
            color = random.choice(colors)
            
            if shape_type == 'circle':
                center = (random.randint(0, width), random.randint(0, height))
                radius = random.randint(20, 200)
                draw.ellipse([center[0]-radius, center[1]-radius,
                            center[0]+radius, center[1]+radius],
                           fill=color, outline=None)
            elif shape_type == 'line':
                start = (random.randint(0, width), random.randint(0, height))
                end = (random.randint(0, width), random.randint(0, height))
                draw.line([start, end], fill=color, width=random.randint(2, 10))
            else:  # rectangle
                pos = (random.randint(0, width), random.randint(0, height))
                size = (random.randint(50, 200), random.randint(50, 200))
                draw.rectangle([pos[0], pos[1], pos[0]+size[0], pos[1]+size[1]],
                             fill=color, outline=None)

    def _apply_theme_effects(self, image: Image.Image, theme: str) -> Image.Image:
        """Apply theme-specific effects to the image"""
        if theme == "quantum":
            # Add quantum noise effect
            image = image.filter(ImageFilter.NOISE)
            image = image.filter(ImageFilter.BLUR)
        elif theme == "cosmic":
            # Add cosmic glow effect
            image = image.filter(ImageFilter.BLUR)
            image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
        elif theme == "cyber":
            # Add cyberpunk scanlines
            image = self._add_scanlines(image)
        elif theme == "nebula":
            # Add nebula blur effect
            image = image.filter(ImageFilter.GaussianBlur(radius=2))
        elif theme == "matrix":
            # Add matrix-style digital rain effect
            image = self._add_digital_rain(image)
            
        return image

    def _add_scanlines(self, image: Image.Image) -> Image.Image:
        """Add cyberpunk-style scanlines"""
        width, height = image.size
        draw = ImageDraw.Draw(image)
        
        for y in range(0, height, 4):
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, 50), width=1)
            
        return image

    def _add_digital_rain(self, image: Image.Image) -> Image.Image:
        """Add matrix-style digital rain effect"""
        width, height = image.size
        draw = ImageDraw.Draw(image)
        
        for x in range(0, width, 20):
            length = random.randint(50, height)
            start_y = random.randint(0, height)
            for y in range(start_y, start_y + length, 15):
                char = random.choice("01")
                draw.text((x, y), char, fill=(0, 255, 0, 150))
                
        return image