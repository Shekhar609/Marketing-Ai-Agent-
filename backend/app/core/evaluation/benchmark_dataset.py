"""
Golden Benchmark Evaluation Dataset
Corresponds to Master Specification Section 39:
Pre-built evaluation test cases for RAG accuracy, marketing campaign strategies,
and autonomous decision reliability.
"""

from typing import Any, Dict, List
from pydantic import BaseModel


class GoldenTestCase(BaseModel):
    id: str
    category: str  # RAG, AGENT, PERSONA, CAMPAIGN
    prompt: str
    expected_contexts: List[str]
    reference_output: str
    required_keywords: List[str]
    passing_threshold: float = 0.70


GOLDEN_BENCHMARK_SUITE: List[GoldenTestCase] = [
    GoldenTestCase(
        id="BENCH_RAG_001",
        category="RAG",
        prompt="What is AIPNT DigiSwasth and its ABDM integration?",
        expected_contexts=[
            "AIPNT DigiSwasth is an AI-powered OPD and IPD hospital management system built with native ABDM M1, M2, and M3 compliance.",
            "It automates patient registration, electronic health record synchronization, and multi-lingual voice triage across 12 Indian regional languages.",
        ],
        reference_output="AIPNT DigiSwasth is an AI hospital triage and EHR platform that provides ABDM M1/M2/M3 compliance and multilingual voice triage.",
        required_keywords=["DigiSwasth", "ABDM", "triage", "compliance"],
        passing_threshold=0.75,
    ),
    GoldenTestCase(
        id="BENCH_CAMPAIGN_002",
        category="CAMPAIGN",
        prompt="Design a 30-day B2B marketing campaign for hospital CIOs in tier-1 Indian metros.",
        expected_contexts=[
            "Hospital CIOs prioritize compliance, patient wait times, and rapid EHR adoption.",
        ],
        reference_output=(
            "# 30-Day Campaign Strategy for Hospital CIOs\n"
            "• Target Audience: Hospital CIOs & Medical Directors in Tier-1 Indian Metros.\n"
            "• Channels: 60% LinkedIn Thought Leadership, 40% Google High-Intent Search.\n"
            "• Conversion Action: Offer 14-day free pilot trial with instant ABDM compliance.\n"
            "• Financial Budget: Allocated $25,000 budget targeting CPL under $50 and 3.5x ROI."
        ),
        required_keywords=["LinkedIn", "CIO", "Search", "conversion", "budget"],
        passing_threshold=0.70,
    ),
    GoldenTestCase(
        id="BENCH_PERSONA_003",
        category="PERSONA",
        prompt="Generate buyer persona for Chief Revenue Officer of a fast-growing B2B SaaS company.",
        expected_contexts=[
            "CROs evaluate CAC payback periods, net revenue retention, and sales pipeline velocity.",
        ],
        reference_output=(
            "# Buyer Persona: Chief Revenue Officer (CRO)\n"
            "• Target Role: CRO at High-Growth B2B SaaS Company.\n"
            "• Primary Pain Point: Disjointed marketing and sales operations leading to pipeline leakage.\n"
            "• Strategic Goal: Unified revenue attribution, CAC reduction, and Net Revenue Retention.\n"
            "• Decision Metric: Pipeline velocity, ROI justification, and seamless CRM integration."
        ),
        required_keywords=["CRO", "pipeline", "attribution", "CAC", "retention"],
        passing_threshold=0.70,
    ),
]
