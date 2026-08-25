"""
CLI for PI-RADS Prostate MRI Agent: ACR PI-RADS v2.1 scoring tool.
"""
import argparse
import json
import sys
from pi_rads_prostate_mri_agent.models import ProstateZone, ProstateLesion
from pi_rads_prostate_mri_agent.engine import score_lesion, assess_patient


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pi-rads-prostate-mri-agent",
        description="PI-RADS v2.1 prostate MRI scoring tool.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # score command - score a single lesion
    p_score = subparsers.add_parser("score", help="Score a single prostate lesion")
    p_score.add_argument("--zone", required=True, choices=["peripheral", "transition", "anterior_fibromuscular", "central"],
                         help="Prostate zone")
    p_score.add_argument("--t2w", type=int, required=True, help="T2W score (1-5)")
    p_score.add_argument("--dwi", type=int, required=True, help="DWI score (1-5)")
    p_score.add_argument("--dce-positive", action="store_true", help="DCE is positive")
    p_score.add_argument("--size", type=float, default=None, help="Lesion size in mm")
    p_score.add_argument("--location", default="", help="Lesion location (e.g., 'left base')")
    p_score.add_argument("--json", action="store_true", help="Output as JSON")

    # assess command - assess multiple lesions
    p_assess = subparsers.add_parser("assess", help="Assess multiple lesions for a patient")
    p_assess.add_argument("-l", "--lesion", action="append", dest="lesions", required=True,
                          help="Lesion spec: ZONE:T2W:DWI[:DCE][:SIZE_MM] (e.g., peripheral:3:4:dce:12). Repeatable.")
    p_assess.add_argument("--json", action="store_true", help="Output as JSON")

    # info command
    p_info = subparsers.add_parser("info", help="Show PI-RADS score information")
    p_info.add_argument("score", nargs="?", type=int, default=None, help="Score (1-5)")

    args = parser.parse_args(argv)

    if args.command == "score":
        zone = ProstateZone(args.zone)
        lesion = ProstateLesion(
            lesion_id="lesion_1",
            zone=zone,
            t2w_score=args.t2w,
            dwi_score=args.dwi,
            dce_positive=args.dce_positive,
            size_mm=args.size,
            location=args.location,
        )
        result = score_lesion(lesion)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print("=" * 60)
            print(f"  PI-RADS v2.1 Assessment")
            print("=" * 60)
            print(f"  Lesion:      {result.lesion_id}")
            print(f"  Zone:        {result.zone.value}")
            print(f"  T2W Score:   {result.t2w_score}")
            print(f"  DWI Score:   {result.dwi_score}")
            print(f"  DCE:         {'Positive' if result.dce_positive else 'Negative'}")
            print(f"  PI-RADS:     {result.pirads_score}")
            print(f"  Primary:     {result.primary_sequence}")
            print(f"  Secondary:   {result.secondary_sequence}")
            if result.dce_upgrade_applied:
                print(f"  * DCE upgrade applied")
            if result.size_mm:
                print(f"  Size:        {result.size_mm}mm")
            print(f"  Biopsy:      {'Recommended' if result.biopsy_recommended else 'Not recommended'}")
            print(f"  Significance: {result.clinical_significance}")
            if result.notes:
                for note in result.notes:
                    print(f"  Note: {note}")
            print("=" * 60)
        return 0

    elif args.command == "assess":
        lesions = []
        for i, spec in enumerate(args.lesions):
            parts = spec.split(":")
            if len(parts) < 3:
                print(f"Error: Invalid lesion spec '{spec}'. Use ZONE:T2W:DWI[:DCE][:SIZE]", file=sys.stderr)
                return 1
            zone = ProstateZone(parts[0])
            t2w = int(parts[1])
            dwi = int(parts[2])
            dce = False
            size = None
            if len(parts) > 3:
                if parts[3].lower() in ("dce", "positive", "true", "1"):
                    dce = True
                else:
                    try:
                        size = float(parts[3])
                    except ValueError:
                        pass
            if len(parts) > 4:
                try:
                    size = float(parts[4])
                except ValueError:
                    pass
            lesions.append(ProstateLesion(
                lesion_id=f"lesion_{i+1}",
                zone=zone,
                t2w_score=t2w,
                dwi_score=dwi,
                dce_positive=dce,
                size_mm=size,
            ))

        assessment = assess_patient(lesions)
        if args.json:
            print(json.dumps(assessment.to_dict(), indent=2))
        else:
            print("=" * 60)
            print(f"  PI-RADS v2.1 Patient Assessment")
            print("=" * 60)
            print(f"  Max PI-RADS Score: {assessment.max_pirads_score}")
            print(f"  Actionable Lesion: {'Yes' if assessment.has_actionable_lesion else 'No'}")
            print()
            for lr in assessment.lesions:
                print(f"  {lr.lesion_id}: Zone={lr.zone.value}, T2W={lr.t2w_score}, "
                      f"DWI={lr.dwi_score}, DCE={'+' if lr.dce_positive else '-'} "
                      f"-> PI-RADS {lr.pirads_score}")
                if lr.biopsy_recommended:
                    print(f"    -> Biopsy recommended")
            print("=" * 60)
        return 0

    elif args.command == "info":
        descriptions = {
            1: "Very low - clinically significant cancer is highly unlikely",
            2: "Low - clinically significant cancer is unlikely",
            3: "Intermediate - clinically significant cancer is equivocal",
            4: "High - clinically significant cancer is likely",
            5: "Very high - clinically significant cancer is highly likely",
        }
        if args.score:
            if args.score not in descriptions:
                print(f"Invalid score: {args.score}. Must be 1-5.", file=sys.stderr)
                return 1
            print(f"PI-RADS {args.score}: {descriptions[args.score]}")
        else:
            print("PI-RADS v2.1 Score Definitions:")
            print()
            for score, desc in descriptions.items():
                print(f"  PI-RADS {score}: {desc}")
            print()
            print("Zone-based scoring rules:")
            print("  Peripheral Zone: DWI primary, DCE secondary")
            print("    - DCE positivity upgrades score 3 to 4")
            print("  Transition Zone: T2W primary, DWI secondary")
            print("    - DWI score 4-5 upgrades T2W score 3 to 4")
            print()
            print("Biopsy recommendation: PI-RADS >= 3")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
