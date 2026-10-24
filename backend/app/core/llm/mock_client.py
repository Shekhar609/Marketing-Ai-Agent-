"""
Offline / Mock LLM Client with Grounded Domain Synthesis
Enables deterministic local testing and agent execution without live API credits.
"""

import json
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.core.llm.base import BaseLLMClient, LLMMessage, LLMResponse

T = TypeVar("T", bound=BaseModel)


class MockLLMClient(BaseLLMClient):
    """
    Deterministic mock LLM client supplying grounded data for AIPNT.
    """

    async def generate(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        user_prompt = messages[-1].content if messages else "Objective analysis"
        mock_text = f"Autonomous analysis generated for: {user_prompt[:100]}"
        return LLMResponse(
            content=mock_text,
            model=model or "mock-model",
            input_tokens=150,
            output_tokens=220,
            latency_ms=45.0,
            estimated_cost=0.00001,
        )

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        schema: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        schema_name = schema.__name__
        
        # Grounded mock responses for specific agent schemas
        if "MarketResearch" in schema_name:
            data = {
                "market_summary": "High demand across Indian Tier-2 & Tier-3 engineering colleges and schools for NEP 2020 aligned AI labs and robotics training.",
                "trends": [
                    "Government mandates for AI curriculum integration in K-12",
                    "Rapid adoption of ABDM (Ayushman Bharat Digital Mission) health records in clinics",
                    "Shift toward regional language (Indic) interactive voice AI assistants"
                ],
                "opportunities": [
                    "Direct institutional sales of Prarambh coding & IoT kits to 250+ private schools",
                    "DigiSwasth diagnostic kiosk deployment in CSR-funded rural clinics",
                    "ATAT smart classroom deployments in semi-urban institutions"
                ],
                "threats": [
                    "Legacy hardware competitors bundling low-cost uncertified STEM kits",
                    "Longer procurement cycles in government tenders"
                ],
                "recommended_actions": [
                    "Launch 60-day targeted campaign to School Principals and Hospital Administrators",
                    "Publish whitepaper on ABDM EHR compliance ROI for diagnostic centers",
                    "Offer live interactive pilot webinars with Prarambh dual Odia/English AI"
                ]
            }
        elif "Competitive" in schema_name:
            data = {
                "competitor_summary": "Primary competition includes HealthCube (MedTech) and STEMROBO / Avishkaar (EduTech).",
                "competitors": [
                    {
                        "name": "HealthCube",
                        "market_share": "Medium",
                        "strengths": ["Strong presence in rural health NGOs"],
                        "weaknesses": ["Lacks integrated ABDM PMS and vernacular voice triage"],
                        "aipnt_moat": "DigiSwasth delivers instant ABDM sync + integrated AI diagnostic triage"
                    },
                    {
                        "name": "STEMROBO",
                        "market_share": "High",
                        "strengths": ["Extensive school partner network in North India"],
                        "weaknesses": ["Curriculum is generic, no regional Indic language AI teacher co-pilot"],
                        "aipnt_moat": "Prarambh + ATAT co-teacher smart board integration in Odia & English"
                    }
                ],
                "content_gaps": ["Technical battlecard comparison", "ABDM compliance calculator"],
                "opportunities": ["Position DigiSwasth as the only end-to-end ABDM kiosk in East India"]
            }
        elif "Persona" in schema_name or "ICP" in schema_name:
            data = {
                "icp_summary": "Tier-1/2 School Trusts & Mid-size Hospital Groups in India",
                "personas": [
                    {
                        "role": "School Principal / Academic Director",
                        "pain_points": ["Lack of qualified STEM teachers", "Pressure to meet NEP 2020 AI standards"],
                        "buying_triggers": ["New academic year curriculum refresh", "Parental demand for AI skills"],
                        "decision_criteria": ["Hands-on hardware reliability", "Teacher training support", "Cost per student"]
                    },
                    {
                        "role": "Hospital Medical Superintendent / Clinic Director",
                        "pain_points": ["Overcrowded OPD triage", "ABDM compliance fines", "Manual patient record errors"],
                        "buying_triggers": ["Digital health accreditation mandates", "Need to accelerate outpatient throughput"],
                        "decision_criteria": ["Regulatory certification", "Kiosk durability", "Ease of staff training"]
                    }
                ]
            }
        else:
            # Fallback schema reconstruction using schema fields
            data = {}
            for field_name, field_info in schema.model_fields.items():
                annotation = field_info.annotation
                if annotation in (str, Optional[str]):
                    data[field_name] = f"Grounded {field_name.replace('_', ' ').title()}"
                elif annotation in (int, Optional[int]):
                    data[field_name] = 500
                elif annotation in (float, Optional[float]):
                    data[field_name] = 500000.0
                elif annotation in (bool, Optional[bool]):
                    data[field_name] = True
                elif getattr(annotation, "__origin__", None) is list or annotation is list:
                    data[field_name] = [f"Item 1 for {field_name}", f"Item 2 for {field_name}"]
                elif getattr(annotation, "__origin__", None) is dict or annotation is dict:
                    data[field_name] = {"key": f"Value for {field_name}"}
                else:
                    data[field_name] = {}
        
        return schema.model_validate(data)
