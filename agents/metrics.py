"""
Prometheus Operational Metrics Exporter for pi-rads-prostate-mri-agent.
"""
import time
from typing import Dict, Any

class SystemMetricsCollector:
    def __init__(self):
        self.system_name = "pi-rads-prostate-mri-agent"
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
        sys_lbl = self.system_name
        p_lines = [
            "# HELP system_tasks_total Total count of distributed component tasks processed",
            "# TYPE system_tasks_total counter",
            f'system_tasks_total{{system="{sys_lbl}"}} {self.tasks_total}',
            "",
            "# HELP alerts_triggered_total Total count of alerts by urgency tier",
            "# TYPE alerts_triggered_total counter",
            f'alerts_triggered_total{{system="{sys_lbl}",urgency="CRITICAL_STAT"}} {self.critical_alerts_total}',
            f'alerts_triggered_total{{system="{sys_lbl}",urgency="ELEVATED_RISK"}} {self.elevated_alerts_total}',
            f'alerts_triggered_total{{system="{sys_lbl}",urgency="ROUTINE"}} {self.routine_tasks_total}',
            "",
            "# HELP phi_outbound_blocks_total Total PHI outbound guard blocks",
            "# TYPE phi_outbound_blocks_total counter",
            f'phi_outbound_blocks_total{{system="{sys_lbl}"}} {self.phi_blocks_total}',
            "",
            "# HELP audit_chain_blocks_total Total HMAC-SHA256 audit blocks signed",
            "# TYPE audit_chain_blocks_total counter",
            f'audit_chain_blocks_total{{system="{sys_lbl}"}} {self.audit_blocks_total}',
            "",
            "# HELP task_processing_duration_avg_seconds Average task evaluation latency",
            "# TYPE task_processing_duration_avg_seconds gauge",
            f'task_processing_duration_avg_seconds{{system="{sys_lbl}"}} {avg_latency:.4f}',
            ""
        ]
        return "\n".join(p_lines)

GLOBAL_METRICS = SystemMetricsCollector()
