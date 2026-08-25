"""
Prometheus Operational Metrics Exporter for pi-rads-prostate-mri-agent.
"""
import time
from typing import Dict, Any

class SystemMetricsCollector:
    def __init__(self):
        self.tasks_total = 0
        self.critical_alerts_total = 0
        self.elevated_alerts_total = 0
        self.routine_tasks_total = 0
        self.phi_blocks_total = 0
        self.audit_blocks_total = 0
        self.processing_latency_sum = 0.0

    def record_task(self, urgency: str, duration_sec: float):
        self.tasks_total += 1
        self.processing_latency_sum += duration_sec
        self.audit_blocks_total += 1
        u_upper = str(urgency).upper()
        if "CRITICAL" in u_upper:
            self.critical_alerts_total += 1
        elif "ELEVATED" in u_upper:
            self.elevated_alerts_total += 1
        else:
            self.routine_tasks_total += 1

    def record_phi_block(self):
        self.phi_blocks_total += 1

    def export_prometheus_text(self) -> str:
        avg_latency = self.processing_latency_sum / max(1, self.tasks_total)
        return (
            f"# HELP system_tasks_total Total count of distributed component tasks processed\n"
            f"# TYPE system_tasks_total counter\n"
            f"system_tasks_total {system=\"pi-rads-prostate-mri-agent\"} {self.tasks_total}\n\n"
            f"# HELP alerts_triggered_total Total count of alerts by urgency tier\n"
            f"# TYPE alerts_triggered_total counter\n"
            f"alerts_triggered_total {system=\"pi-rads-prostate-mri-agent\",urgency=\"CRITICAL_STAT\"} {self.critical_alerts_total}\n"
            f"alerts_triggered_total {system=\"pi-rads-prostate-mri-agent\",urgency=\"ELEVATED_RISK\"} {self.elevated_alerts_total}\n"
            f"alerts_triggered_total {system=\"pi-rads-prostate-mri-agent\",urgency=\"ROUTINE\"} {self.routine_tasks_total}\n\n"
            f"# HELP phi_outbound_blocks_total Total PHI outbound guard blocks\n"
            f"# TYPE phi_outbound_blocks_total counter\n"
            f"phi_outbound_blocks_total {system=\"pi-rads-prostate-mri-agent\"} {self.phi_blocks_total}\n\n"
            f"# HELP audit_chain_blocks_total Total HMAC-SHA256 audit blocks signed\n"
            f"# TYPE audit_chain_blocks_total counter\n"
            f"audit_chain_blocks_total {system=\"pi-rads-prostate-mri-agent\"} {self.audit_blocks_total}\n\n"
            f"# HELP task_processing_duration_avg_seconds Average task evaluation latency\n"
            f"# TYPE task_processing_duration_avg_seconds gauge\n"
            f"task_processing_duration_avg_seconds {system=\"pi-rads-prostate-mri-agent\"} {avg_latency:.4f}\n"
        )

GLOBAL_METRICS = SystemMetricsCollector()
