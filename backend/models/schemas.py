from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class AuditRequest(BaseModel):
    url: str


class ChatRequest(BaseModel):
    message: str
    auditId: str
    auditContext: Optional[Dict[str, Any]] = None
    canvasImage: Optional[str] = None


class ListingData(BaseModel):
    title: str
    bullet_points: List[str]
    description: str
    images: List[str]
    price: str
    rating: float
    review_count: int
    reviews_summary: str
    asin: str
    category: str
    brand: str


class TitleAnalysis(BaseModel):
    score: int
    issues: List[str]
    roast: str
    fix: str


class BulletsAnalysis(BaseModel):
    score: int
    issues: List[str]
    roast: str
    fix: str


class DescriptionAnalysis(BaseModel):
    score: int
    issues: List[str]
    roast: str
    fix: str


class PricingAnalysis(BaseModel):
    score: int
    issues: List[str]
    fix: str


class TrustSignals(BaseModel):
    score: int
    missing: List[str]
    suggestions: List[str]


class CopyAnalysis(BaseModel):
    title_analysis: TitleAnalysis
    bullets_analysis: BulletsAnalysis
    description_analysis: DescriptionAnalysis
    pricing_analysis: PricingAnalysis
    trust_signals: TrustSignals


class DimensionScores(BaseModel):
    title: int
    bullets: int
    trust: int
    images: int
    description: int
    price: int


class ConversionScore(BaseModel):
    overall_score: int
    improvement_potential: str
    dimension_scores: DimensionScores
    top_5_fixes: List[str]


class ImageItem(BaseModel):
    url: str
    score: int
    issues: List[str]
    suggestions: List[str]


class ImageAnalysis(BaseModel):
    images: List[ImageItem]
    overall_image_score: int
    missing_image_types: List[str]
    priority_fix: str


class ImprovedCopy(BaseModel):
    improved_title: str
    improved_bullets: List[str]
    improved_description: str
    ad_hooks: List[str]


class RoastScript(BaseModel):
    hook: str
    roast: str
    pivot: str
    cta: str
    full_script: str


class AuditResult(BaseModel):
    auditId: str
    listing: Dict[str, Any]
    copy_analysis: Dict[str, Any]
    score: Dict[str, Any]
    image_analysis: Dict[str, Any]
    improved_copy: Dict[str, Any]
    roast_script: Dict[str, Any]
    used_mock_data: bool = False
