"""
AstraLink - Holographic Visualization Package
========================================

This package provides holographic visualization capabilities including
QR code generation and 3D model rendering for the AstraLink platform.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
"""

from .ai_image_generator import AIHolographicGenerator
from .nft_visualization import NFTVisualizationManager
from .holographic_qr import HolographicQRGenerator

__all__ = ['AIHolographicGenerator', 'NFTVisualizationManager', 'HolographicQRGenerator']