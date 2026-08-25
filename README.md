# PI-RADS Prostate MRI Agent

> **ACR PI-RADS v2.1** multiparametric prostate MRI scoring tool.

## Overview

Implements PI-RADS v2.1 (Prostate Imaging Reporting and Data System) for scoring prostate lesions on multiparametric MRI (mpMRI). Evaluates peripheral zone (PZ) and transition zone (TZ) lesions using zone-specific primary/secondary sequences and DCE upgrade rules.

## PI-RADS Scores

| Score | Interpretation |
|-------|---------------|
| **1** | Very low - clinically significant cancer highly unlikely |
| **2** | Low - clinically significant cancer unlikely |
| **3** | Intermediate - clinically significant cancer equivocal |
| **4** | High - clinically significant cancer likely |
| **5** | Very high - clinically significant cancer highly likely |

## Zone-Based Scoring Rules

### Peripheral Zone (PZ)
- **Primary**: DWI (Diffusion-Weighted Imaging)
- **Secondary**: DCE (Dynamic Contrast-Enhanced)
- DCE positivity upgrades PI-RADS 3 to 4

### Transition Zone (TZ)
- **Primary**: T2W (T2-Weighted)
- **Secondary**: DWI
- DWI score 4-5 upgrades T2W score 3 to 4

## Biopsy Recommendation

PI-RADS >= 3: Biopsy recommended

## CLI Usage

```bash
# Score a single PZ lesion
python cli.py score --zone peripheral --t2w 3 --dwi 4 --dce-positive

# Score a TZ lesion
python cli.py score --zone transition --t2w 3 --dwi 5 --size 15

# Assess multiple lesions
python cli.py assess -l peripheral:3:4:dce:12 -l transition:2:2:0:8

# JSON output
python cli.py score --zone peripheral --t2w 4 --dwi 4 --json

# Show score definitions
python cli.py info
python cli.py info 4
```

## Python API

```python
from pi_rads_prostate_mri_agent import ProstateLesion, ProstateZone, score_lesion

lesion = ProstateLesion(
    lesion_id="L1",
    zone=ProstateZone.PERIPHERAL,
    t2w_score=3,
    dwi_score=4,
    dce_positive=True,
    size_mm=12,
)

result = score_lesion(lesion)
print(f"PI-RADS: {result.pirads_score}")
print(f"Biopsy recommended: {result.biopsy_recommended}")
```

## Testing

```bash
python -m pytest tests/ -v
```

## License

MIT License. See [LICENSE](LICENSE).
