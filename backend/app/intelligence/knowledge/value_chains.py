"""Generic, industry-agnostic knowledge structures.

These are *reference data* used for retrieval and matching — NOT hard-coded
per-industry recommendation tables. A value chain and a catalogue of AI
capability patterns are the same for every industry; the system dynamically
maps a given organisation's processes onto them.

The actual (industry-specific) knowledge lives in the vector store, seeded from
``data/knowledge/*`` and any uploaded documents, and is retrieved at analysis
time.
"""
from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------------
# Generic value chain (Porter, 1985) — primary + support activities.
# --------------------------------------------------------------------------
VALUE_CHAIN_AREAS: list[dict[str, Any]] = [
    {
        "name": "Inbound Logistics",
        "category": "primary",
        "description": "Receiving, storing and distributing raw materials, parts or inputs needed to create the product/service.",
        "key_activities": [
            "receiving", "warehousing", "inventory control", "inventory management", "stock control",
            "transport scheduling", "supplier returns", "unloading", "materials handling", "inbound",
            "storage", "stock replenishment", "parts receiving",
        ],
    },
    {
        "name": "Operations",
        "category": "primary",
        "description": "Transforming inputs into the final product or service: production, processing, service delivery, quality control.",
        "key_activities": [
            "production", "processing", "assembly", "quality control", "service delivery", "workflow execution",
            "manufacturing", "maintenance", "equipment monitoring", "machine operation", "fabrication",
            "claims processing", "claims adjudication", "case processing", "assessment", "grading",
            "evaluation", "repair", "clinical operations", "order processing",
        ],
    },
    {
        "name": "Outbound Logistics",
        "category": "primary",
        "description": "Collecting, storing and physically distributing the finished product or service to customers.",
        "key_activities": [
            "order fulfilment", "packaging", "shipping", "delivery", "distribution", "dispatch",
            "outbound logistics", "last-mile delivery", "transportation", "fulfilment",
        ],
    },
    {
        "name": "Marketing & Sales",
        "category": "primary",
        "description": "Persuading customers to buy: advertising, promotion, pricing, channel selection, selling.",
        "key_activities": [
            "advertising", "promotion", "pricing", "channel management", "lead generation", "sales",
            "marketing", "campaigns", "customer acquisition", "branding", "digital marketing",
        ],
    },
    {
        "name": "Service",
        "category": "primary",
        "description": "Maintaining and enhancing product value after sale: support, repair, training, warranty, customer success.",
        "key_activities": [
            "customer support", "after-sales service", "repair", "training", "complaint handling",
            "helpdesk", "technical support", "customer service", "warranty", "client success",
        ],
    },
    {
        "name": "Procurement",
        "category": "support",
        "description": "Acquiring the goods, services and resources the organisation needs to operate.",
        "key_activities": [
            "supplier selection", "purchasing", "contract negotiation", "vendor management", "sourcing",
            "buying", "supply chain", "supplier management", "requisitioning", "tendering",
        ],
    },
    {
        "name": "Technology & IT",
        "category": "support",
        "description": "Technology infrastructure, systems, data platforms and innovation that support every other activity.",
        "key_activities": [
            "IT infrastructure", "software development", "data management", "cybersecurity", "automation",
            "cloud platform", "system integration", "data engineering", "IT operations", "digitalisation",
        ],
    },
    {
        "name": "Human Resources",
        "category": "support",
        "description": "Recruiting, hiring, training, developing and compensating people.",
        "key_activities": [
            "recruitment", "onboarding", "training", "performance management", "payroll",
            "talent management", "hiring", "staffing", "compensation", "workforce planning",
        ],
    },
    {
        "name": "Firm Infrastructure",
        "category": "support",
        "description": "General management, finance, accounting, legal, planning and governance.",
        "key_activities": [
            "finance", "accounting", "legal", "planning", "risk management", "compliance",
            "audit", "strategy", "governance", "budgeting", "reporting",
        ],
    },
]


# --------------------------------------------------------------------------
# AI capability catalogue — generic patterns, industry-agnostic.
# Each entry describes what the capability does, what data it needs, who it
# touches and its typical complexity/value so the engine can reason about ANY
# process without a per-industry lookup table.
# --------------------------------------------------------------------------
AI_CAPABILITIES: list[dict[str, Any]] = [
    {
        "id": "predictive_analytics",
        "name": "Predictive Analytics",
        "description": "Statistical and machine-learning models that forecast future outcomes (demand, failure, risk, churn, cost) from historical data.",
        "data_requirements": ["historical structured data", "labeled outcomes", "time-series records"],
        "technology_requirements": ["ML platform", "feature store", "batch/stream pipeline"],
        "typical_roles": ["Data Scientist", "ML Engineer", "Business Analyst"],
        "typical_skills": ["machine learning", "statistics", "feature engineering"],
        "complexity": 3,
        "value_potential": 5,
        "examples": ["forecasting future demand or outcomes from historical data", "scoring the likelihood of an event such as default, defect or delay"],
        "risks": ["model drift over time", "bias in training data", "over-reliance without human oversight"],
        "governance": ["model validation & monitoring", "explainability documentation", "data provenance"],
    },
    {
        "id": "anomaly_detection",
        "name": "Anomaly Detection",
        "description": "Identifying unusual patterns, outliers, fraud, defects or failures in large streams of transactions or sensor data.",
        "data_requirements": ["transaction/event logs", "sensor or telemetry data", "historical normal behaviour"],
        "technology_requirements": ["streaming platform", "rules engine or ML models", "alerting system"],
        "typical_roles": ["Data Engineer", "Fraud/Risk Analyst", "Data Scientist"],
        "typical_skills": ["anomaly detection", "stream processing", "rule authoring"],
        "complexity": 3,
        "value_potential": 4,
        "examples": ["flagging fraudulent or irregular transactions", "detecting equipment or quality defects early"],
        "risks": ["false positives", "alert fatigue", "adversarial evasion"],
        "governance": ["alert triage workflow", "audit trail", "threshold governance"],
    },
    {
        "id": "nlp_classification",
        "name": "Text Classification & NLP",
        "description": "Classifying, routing and extracting meaning from unstructured text (emails, reviews, tickets, forms).",
        "data_requirements": ["unstructured text", "labeled categories (for supervised learning)", "domain vocabulary"],
        "technology_requirements": ["NLP library/model", "text pipeline", "integration to source system"],
        "typical_roles": ["NLP Engineer", "Data Scientist", "Domain Specialist"],
        "typical_skills": ["NLP", "text preprocessing", "model fine-tuning"],
        "complexity": 3,
        "value_potential": 4,
        "examples": ["routing or prioritising incoming text by intent or topic", "automated triage of forms, tickets or messages"],
        "risks": ["language and domain ambiguity", "biased labels", "missed nuance"],
        "governance": ["human review loop", "confidence thresholds", "label quality control"],
    },
    {
        "id": "document_understanding",
        "name": "Document Understanding",
        "description": "Extracting structured data from documents (invoices, claims, contracts, forms) via OCR + information extraction.",
        "data_requirements": ["scanned/typed documents", "template or layout samples", "ground-truth extracted fields"],
        "technology_requirements": ["OCR engine", "document parser", "validation rules"],
        "typical_roles": ["Document/Data Engineer", "Process Analyst", "Subject Matter Expert"],
        "typical_skills": ["OCR", "information extraction", "data validation"],
        "complexity": 4,
        "value_potential": 4,
        "examples": ["extracting key fields from invoices, claims or applications", "digitising paper-based intake processes"],
        "risks": ["extraction errors", "layout variability", "illegible scans"],
        "governance": ["confidence scoring", "exception handling", "data retention rules"],
    },
    {
        "id": "conversational_ai",
        "name": "Conversational AI",
        "description": "Chatbots and virtual assistants that handle routine interactions, answer questions and route requests.",
        "data_requirements": ["FAQ / knowledge base", "conversation history", "intent definitions"],
        "technology_requirements": ["chatbot platform", "NLU model", "integration to backend systems"],
        "typical_roles": ["Conversation Designer", "Software Engineer", "Support Lead"],
        "typical_skills": ["conversation design", "NLU", "API integration"],
        "complexity": 2,
        "value_potential": 4,
        "examples": ["answering common questions automatically", "handling routine requests and routing complex ones to staff"],
        "risks": ["poor answers eroding trust", "escalation gaps", "privacy of conversations"],
        "governance": ["fallback to human", "content moderation", "logging & privacy"],
    },
    {
        "id": "recommendation_systems",
        "name": "Recommendation & Personalisation",
        "description": "Suggesting relevant items, content or next-best-actions to individual users based on their behaviour and preferences.",
        "data_requirements": ["user interaction history", "item/content catalogue", "user profile data"],
        "technology_requirements": ["recommendation engine", "feature store", "real-time serving"],
        "typical_roles": ["ML Engineer", "Data Scientist", "Product Manager"],
        "typical_skills": ["recommender systems", "A/B testing", "personalisation"],
        "complexity": 3,
        "value_potential": 5,
        "examples": ["suggesting relevant products, content or actions to individual users", "personalising an experience based on behaviour"],
        "risks": ["filter bubbles", "privacy concerns", "cold-start for new users"],
        "governance": ["consent management", "algorithmic transparency", "diversity of recommendations"],
    },
    {
        "id": "computer_vision",
        "name": "Computer Vision",
        "description": "Analysing images and video to detect objects, defects, anomalies or extract visual information.",
        "data_requirements": ["image/video datasets", "annotated examples", "camera/sensor infrastructure"],
        "technology_requirements": ["vision models", "GPU inference", "edge/hardware integration"],
        "typical_roles": ["Computer Vision Engineer", "Data Scientist", "Operations Engineer"],
        "typical_skills": ["computer vision", "deep learning", "image annotation"],
        "complexity": 4,
        "value_potential": 4,
        "examples": ["visual quality inspection", "monitoring physical environments for safety or compliance"],
        "risks": ["environmental variability", "annotation cost", "edge hardware constraints"],
        "governance": ["safety sign-off", "human verification", "privacy in monitored spaces"],
    },
    {
        "id": "process_automation",
        "name": "Process Automation (RPA)",
        "description": "Automating repetitive, rule-based manual tasks across systems (data entry, reconciliation, form processing).",
        "data_requirements": ["process documentation", "structured inputs", "access to source systems"],
        "technology_requirements": ["RPA tooling", "orchestration", "API/system access"],
        "typical_roles": ["Automation Engineer", "Process Analyst", "Business Analyst"],
        "typical_skills": ["RPA", "process mapping", "scripting"],
        "complexity": 2,
        "value_potential": 4,
        "examples": ["automating repetitive manual data entry or reconciliation", "connecting systems that lack APIs"],
        "risks": ["brittle automation", "process exceptions", "governance of bot credentials"],
        "governance": ["exception handling", "access control for bots", "change management"],
    },
    {
        "id": "optimization",
        "name": "Optimisation & Scheduling",
        "description": "Mathematically optimising resource allocation, routing, scheduling and capacity planning.",
        "data_requirements": ["constraints & objectives", "resource/capacity data", "cost & time data"],
        "technology_requirements": ["optimisation solver", "simulation", "integration to operations"],
        "typical_roles": ["Operations Research Analyst", "Data Scientist", "Planner"],
        "typical_skills": ["operations research", "optimisation", "simulation"],
        "complexity": 4,
        "value_potential": 5,
        "examples": ["optimising routing, scheduling or resource allocation", "balancing capacity against demand"],
        "risks": ["model oversimplification", "operational resistance", "data quality"],
        "governance": ["constraint review", "human override", "performance tracking"],
    },
    {
        "id": "generative_content",
        "name": "Generative AI for Content",
        "description": "Drafting documents, summaries, marketing copy, code or responses using large language models.",
        "data_requirements": ["examples/templates", "brand guidelines", "source content"],
        "technology_requirements": ["LLM access", "prompt management", "review workflow"],
        "typical_roles": ["Content/Marketing Specialist", "Engineer", "Knowledge Manager"],
        "typical_skills": ["prompt engineering", "content editing", "review & quality control"],
        "complexity": 2,
        "value_potential": 4,
        "examples": ["drafting reports, summaries or responses", "accelerating content and document production"],
        "risks": ["hallucination", "quality inconsistency", "IP/copyright concerns"],
        "governance": ["human review", "output guidelines", "source attribution"],
    },
    {
        "id": "knowledge_management",
        "name": "Knowledge Management & Search",
        "description": "Semantic search and retrieval over an organisation's documents and knowledge so people can find answers quickly.",
        "data_requirements": ["document corpus", "knowledge base", "access controls"],
        "technology_requirements": ["vector database", "embedding model", "search UI"],
        "typical_roles": ["Knowledge Manager", "Data Engineer", "Information Architect"],
        "typical_skills": ["information retrieval", "embeddings", "taxonomy design"],
        "complexity": 2,
        "value_potential": 4,
        "examples": ["finding relevant knowledge across a large document base", "surfacing answers from unstructured repositories"],
        "risks": ["stale content", "permission leakage", "relevance gaps"],
        "governance": ["content freshness", "access control", "usage analytics"],
    },
    {
        "id": "personalization_engine",
        "name": "Personalisation Engine",
        "description": "Tailoring an experience, service or intervention to an individual based on their profile and history.",
        "data_requirements": ["individual profile data", "interaction history", "outcome data"],
        "technology_requirements": ["personalisation models", "real-time serving", "consent management"],
        "typical_roles": ["Data Scientist", "Product Manager", "Domain Specialist"],
        "typical_skills": ["personalisation", "A/B testing", "segmentation"],
        "complexity": 3,
        "value_potential": 4,
        "examples": ["adapting an experience or intervention to an individual", "targeting support where it is most needed"],
        "risks": ["privacy", "unfair treatment", "over-personalisation"],
        "governance": ["consent", "fairness review", "opt-out"],
    },
]


def capability_search_text(cap: dict[str, Any]) -> str:
    """Build a searchable text blob for embedding-based matching."""
    parts = [
        cap["name"],
        cap["description"],
        " ".join(cap.get("examples", [])),
        " ".join(cap.get("data_requirements", [])),
    ]
    return " ".join(parts)


def value_chain_search_text(area: dict[str, Any]) -> str:
    parts = [area["name"], area["description"], " ".join(area.get("key_activities", []))]
    return " ".join(parts)
