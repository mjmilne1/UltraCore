"""
UltraWealth - Fully Digital Automated Investment System

A comprehensive wealth management platform providing:
- Managed Discretionary Accounts (MDA)
- Australian ETF investing
- AI-powered portfolio management
- ASIC RG 179 compliance
- Multimodal AI assistant (Anya)

Author: Manus AI
Date: November 13, 2025
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Manus AI"

from .services.application_service import UltraWealthApplication

# Convenience exports
__all__ = [
    "UltraWealthApplication",
]
