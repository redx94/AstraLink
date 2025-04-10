"""
AstraLink - Carrier Integration Module
=================================

This module provides integration with mobile carrier APIs for retrieving data
plans and processing plan purchases with major carriers.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
See LICENSE file for licensing information.
"""

from typing import Dict, List
import aiohttp
import json

class CarrierIntegration:
    def __init__(self):
        self.supported_carriers = {
            "t-mobile": "https://api.t-mobile.com/esim/v1",
            "att": "https://api.att.com/esim/v1",
            "verizon": "https://api.verizon.com/esim/v1"
        }

    async def get_data_plans(self, carrier: str) -> List[Dict]:
        """Get available data plans from carrier"""
        if carrier not in self.supported_carriers:
            raise CarrierError("Unsupported carrier")

        async with aiohttp.ClientSession() as session:
            url = f"{self.supported_carriers[carrier]}/plans"
            async with session.get(url) as response:
                return await response.json()

    async def purchase_plan(self, carrier: str, plan_id: str, payment_info: Dict) -> Dict:
        """Purchase a data plan and get activation code"""
        if carrier not in self.supported_carriers:
            raise CarrierError("Unsupported carrier")

        purchase_data = {
            "planId": plan_id,
            "payment": payment_info
        }

        async with aiohttp.ClientSession() as session:
            url = f"{self.supported_carriers[carrier]}/purchase"
            async with session.post(url, json=purchase_data) as response:
                result = await response.json()
                return {
                    "activation_code": result["activationCode"],
                    "iccid": result["iccid"],
                    "plan_details": result["planDetails"]
                }
