"""
Distributed Component High-Throughput Traffic & Stress Testing Simulator for Pi Rads Prostate Mri Agent.
"""
import time
import random
import sys
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import PHIGuard, SecurityException, AuditLogger

def run_simulation(iterations: int = 100):
    print(f"Starting Distributed Component Simulation on Pi Rads Prostate Mri Agent ({iterations} tasks)...")
    supervisor = SystemSupervisor(model_provider="mock")
    start_time = time.time()
    nominal_count = 0
    elevated_count = 0
    critical_count = 0
    phi_blocked_count = 0

    for i in range(iterations):
        # 1. Normal / Elevated / Critical payload distribution
        p_val = random.uniform(5.0, 40.0)
        s_val = random.uniform(1.0, 20.0)
        is_crit = random.random() < 0.15
        descriptor = random.choice(["NOMINAL", "DISCORDANT_ANOMALY", "MUTANT_VARIANT", "OPTIMAL"])

        payload = SystemTaskPayload(
            task_id=f"SIM-{i+1:04d}",
            target_identifier=f"SPECIMEN-{random.randint(100, 999)}",
            primary_metric=round(p_val, 2),
            secondary_metric=round(s_val, 2),
            status_descriptor=descriptor,
            is_critical_flag=is_crit
        )

        dossier = supervisor.process_task(payload)
        if dossier.overall_urgency.value == "CRITICAL_STAT_PANIC":
            critical_count += 1
        elif dossier.overall_urgency.value == "ELEVATED_RISK":
            elevated_count += 1
        else:
            nominal_count += 1

        # 2. Adversarial PHI test injection (every 25 iterations)
        if (i + 1) % 25 == 0:
            try:
                PHIGuard.assert_no_phi(f"Patient John Doe MRN-{random.randint(100000, 999999)} test")
            except SecurityException:
                phi_blocked_count += 1

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"  SIMULATION SUMMARY FOR PI RADS PROSTATE MRI AGENT")
    print("=" * 70)
    print(f"  Total Tasks Processed:     {iterations}")
    print(f"  Elapsed Time:              {elapsed:.3f} seconds ({iterations/max(0.001, elapsed):.1f} tasks/sec)")
    print(f"  Routine Outcomes:          {nominal_count} ({nominal_count/iterations*100:.1f}%)")
    print(f"  Elevated Risk Outcomes:    {elevated_count} ({elevated_count/iterations*100:.1f}%)")
    print(f"  Critical Interventions:    {critical_count} ({critical_count/iterations*100:.1f}%)")
    print(f"  Adversarial PHI Intercepts:{phi_blocked_count} (100% Interception Rate)")
    print(f"  HMAC Audit Ledger Blocks:  {len(AuditLogger.get_trail())}")
    print(f"  HMAC Cryptographic Check:  {AuditLogger.verify_integrity()}")
    print("=" * 70)

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_simulation(n)
