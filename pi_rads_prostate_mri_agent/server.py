"""FastAPI interface for PI-RADS v2.1 scoring and legacy case audit utilities."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, FiniteFloat
from .models import ClinicalCasePayload, ProstateLesion, ProstateZone
from .engine import score_lesion, assess_patient
from .agents import ProstateMRICoordinator

coordinator = ProstateMRICoordinator()


class ScoringRequest(BaseModel):
    zone: Literal["peripheral", "transition"]
    t2w_score: int = Field(ge=1, le=5, strict=True)
    dwi_score: int = Field(ge=1, le=5, strict=True)
    dce_positive: bool = False
    size_mm: Optional[FiniteFloat] = Field(default=None, gt=0)
    location: str = Field(default="", max_length=100)
    lesion_id: str = Field(default="lesion_1", max_length=50)

    def to_lesion(self) -> ProstateLesion:
        return ProstateLesion(
            lesion_id=self.lesion_id,
            zone=ProstateZone(self.zone),
            t2w_score=self.t2w_score,
            dwi_score=self.dwi_score,
            dce_positive=self.dce_positive,
            size_mm=self.size_mm,
            location=self.location,
        )


class AssessmentRequest(BaseModel):
    lesions: List[ScoringRequest] = Field(min_length=1, max_length=25)


class AuditRequest(BaseModel):
    case_id: str = "CASE-2026-001"
    patient_synthetic_id: str = "SYNTH-PT-881"
    primary_metric: float = 24.5
    secondary_metric: float = 14.0
    status_flag: str = "DISCORDANT"
    is_stat: bool = True
    clinical_notes: str = ""
    biomarkers: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    query: str


def create_app():
    try:
        from fastapi import FastAPI
    except ImportError:
        return None

    app = FastAPI(
        title="PI-RADS v2.1 prostate MRI scoring reference",
        description="Combines reader-assigned sequence scores. Not a diagnosis or biopsy decision service.",
        version="2.0.1",
    )

    @app.get("/health")
    def health():
        return {"status": "HEALTHY", "system": "pi-rads-prostate-mri-agent", "version": "2.0.1"}

    @app.post("/api/score")
    def api_score(req: ScoringRequest):
        return score_lesion(req.to_lesion()).to_dict()

    @app.post("/api/assess")
    def api_assess(req: AssessmentRequest):
        return assess_patient([lesion.to_lesion() for lesion in req.lesions]).to_dict()

    @app.post("/api/audit")
    def api_audit(req: AuditRequest):
        return coordinator.process_case(ClinicalCasePayload(**req.model_dump()))

    @app.post("/api/chat")
    def api_chat(req: ChatRequest):
        return {"response": coordinator.query_supervisory_chat(req.query)}

    return app
