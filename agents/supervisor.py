"""
Supervisor Orchestrator & Operations Intelligence for Pi Rads Prostate Mri Agent.
Domain: Radiology & Neuroimaging Systems
"""
import uuid
from typing import Dict, Any, List, Optional
from .base import AuditLogger, ActionExecutor, PHIGuard
from .models import SystemTaskPayload, AgentAlert, ConsensusDossier, UrgencyLevel, SystemIntegrityStatus
from .workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from .llm_factory import LLMFactory


class SystemSupervisor:
    """Master Distributed Component Coordinator for Pi Rads Prostate Mri Agent."""

    def __init__(self, model_provider: str = "mock"):
        self.qc_worker = InvariantQCWorker()
        self.safety_worker = SafetyEscalationWorker()
        self.conformance_worker = ProtocolConformanceWorker()
        self.llm = LLMFactory.create(model_provider, system_name="Pi Rads Prostate Mri Agent")
        self.dossier_registry: Dict[str, ConsensusDossier] = {}

    def process_task(self, payload: SystemTaskPayload, actor: str = "SystemSupervisor") -> ConsensusDossier:
        # Zero-PHI outbound validation
        PHIGuard.assert_no_phi(payload.task_id)
        PHIGuard.assert_no_phi(payload.target_identifier)
        PHIGuard.assert_no_phi(payload.status_descriptor)

        # Multi-worker evaluations
        all_alerts: List[AgentAlert] = []
        all_alerts.extend(self.qc_worker.evaluate(payload))
        all_alerts.extend(self.safety_worker.evaluate(payload))
        all_alerts.extend(self.conformance_worker.evaluate(payload))

        crit_count = sum(1 for a in all_alerts if a.urgency == UrgencyLevel.CRITICAL_STAT)
        elev_count = sum(1 for a in all_alerts if a.urgency == UrgencyLevel.ELEVATED)

        if crit_count > 0:
            overall_urgency = UrgencyLevel.CRITICAL_STAT
            integrity_status = SystemIntegrityStatus.RECALIBRATION_REQUIRED
        elif elev_count > 0:
            overall_urgency = UrgencyLevel.ELEVATED
            integrity_status = SystemIntegrityStatus.DISCORDANT
        else:
            overall_urgency = UrgencyLevel.ROUTINE
            integrity_status = SystemIntegrityStatus.VALIDATED

        audit_entry = AuditLogger.log(
            actor=actor,
            actor_tier="supervisor",
            event_type="TASK_EVALUATION_COMPLETED",
            details={
                "task_id": payload.task_id,
                "target_identifier": payload.target_identifier,
                "overall_urgency": overall_urgency.value,
                "total_alerts": len(all_alerts),
            }
        )

        dossier = ConsensusDossier(
            dossier_id=f"DOSSIER-{uuid.uuid4().hex[:8].upper()}",
            task_id=payload.task_id,
            target_identifier=payload.target_identifier,
            overall_urgency=overall_urgency,
            integrity_status=integrity_status,
            total_alerts=len(all_alerts),
            critical_alerts_count=crit_count,
            alerts=all_alerts,
            consensus_summary=f"Multi-agent consensus completed with status [{overall_urgency.value}]. Total alerts: {len(all_alerts)}.",
            audit_hash=audit_entry["current_hash"],
        )

        self.dossier_registry[dossier.dossier_id] = dossier
        return dossier

    def query_supervisory_chat(self, query: str) -> str:
        PHIGuard.assert_no_phi(query)
        prompt = f"Supervisor inquiry for Pi Rads Prostate Mri Agent under ACR RADS / Fleischner Society / ASPECTS Guidelines: {query}"
        return self.llm.invoke(prompt)
