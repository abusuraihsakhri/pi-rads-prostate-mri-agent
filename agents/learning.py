"""
Autonomous Bayesian Calibration & Active Learning Feedback Engine for pi-rads-prostate-mri-agent.
"""
import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class WorkerPerformanceMetric(BaseModel):
    worker_name: str
    total_evaluations: int = 0
    concordant_decisions: int = 0
    historical_brier_score: float = 0.05
    dynamic_weight: float = 1.0

class ActiveLearningEngine:
    """Continuously refines sub-agent voting weights based on consensus feedback."""

    def __init__(self, system_name: str = "Pi Rads Prostate Mri Agent"):
        self.system_name = system_name
        self.worker_metrics: Dict[str, WorkerPerformanceMetric] = {
            "InvariantQCWorker": WorkerPerformanceMetric(worker_name="InvariantQCWorker"),
            "SafetyEscalationWorker": WorkerPerformanceMetric(worker_name="SafetyEscalationWorker"),
            "ProtocolConformanceWorker": WorkerPerformanceMetric(worker_name="ProtocolConformanceWorker"),
        }
        self.uncertainty_buffer: List[Dict[str, Any]] = []

    def record_feedback(self, worker_name: str, was_concordant: bool, confidence_score: float):
        if worker_name not in self.worker_metrics:
            self.worker_metrics[worker_name] = WorkerPerformanceMetric(worker_name=worker_name)
        m = self.worker_metrics[worker_name]
        m.total_evaluations += 1
        if was_concordant:
            m.concordant_decisions += 1
        
        # Update dynamic Bayesian reliability weight
        acc = m.concordant_decisions / max(1, m.total_evaluations)
        m.dynamic_weight = round(max(0.2, min(2.0, acc * 1.5)), 3)

        # Flag borderline cases for offline active learning review
        if 0.45 <= confidence_score <= 0.65:
            self.uncertainty_buffer.append({
                "worker": worker_name,
                "confidence": confidence_score,
                "concordant": was_concordant
            })

    def get_calibrated_weights(self) -> Dict[str, float]:
        return {k: v.dynamic_weight for k, v in self.worker_metrics.items()}

GLOBAL_LEARNING_ENGINE = ActiveLearningEngine()
