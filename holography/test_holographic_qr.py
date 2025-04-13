"""
Test script for generating holographic QR codes with AI
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from holography.ai_image_generator import AIHolographicGenerator
from holography.nft_visualization import NFTVisualizationManager
import json
import os

async def test_holographic_generation():
    # Sample eSIM data
    esim_data = {
        "esim_id": "1234567890",
        "carrier": "AstraLink",
        "activation_date": "2025-04-12",
        "bandwidth": 1000,
        "plan_details": "Quantum Unlimited 5G+",
        "status": "active"
    }

    # Test each theme
    themes = ["cosmic", "quantum", "cyber", "nebula", "matrix"]
    
    # Initialize the visualization manager with test API key
    viz_manager = NFTVisualizationManager("test_api_key_12345")
    
    print("Testing holographic QR generation for each theme...")
    
    for theme in themes:
        print(f"\nGenerating {theme} theme...")
        try:
            result = await viz_manager.generate_nft_visualization(
                token_id=1,
                theme=theme,
                metadata=esim_data
            )
            
            # Save the holographic QR code
            holographic_data = result["holographic_data"]
            output_dir = "test_output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save metadata
            metadata_path = os.path.join(output_dir, f"{theme}_metadata.json")
            with open(metadata_path, "w") as f:
                json.dump(holographic_data["metadata"], f, indent=2)
                
            print(f"✓ Generated {theme} theme successfully")
            print(f"  - Model URI: {result['model_uri']}")
            print(f"  - AR Viewer URL: {result['ar_viewer_url']}")
            print(f"  - QR Metadata saved to: {metadata_path}")
            
        except Exception as e:
            print(f"✗ Error generating {theme} theme: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_holographic_generation())