"use strict";

// Deterministic PI-RADS v2.1 combination rules; scoring assumes a qualified
// reader has already assigned valid sequence-level assessment scores.
// No image interpretation, diagnosis, or treatment recommendation is performed.
function scoreLesion(input) {
    const zone = input.zone;
    const t2w = Number(input.t2w);
    const dwi = Number(input.dwi);
    if (!["peripheral", "transition"].includes(zone)) {
        throw new Error("Select peripheral or transition zone.");
    }
    if (!Number.isInteger(t2w) || t2w < 1 || t2w > 5 ||
        !Number.isInteger(dwi) || dwi < 1 || dwi > 5) {
        throw new Error("T2W and DWI scores must be integers from 1 to 5.");
    }
    const rawSize = input.size_mm;
    const size = rawSize === "" || rawSize == null ? null : Number(rawSize);
    if (size !== null && (!Number.isFinite(size) || size <= 0)) {
        throw new Error("Lesion size must be a finite positive number in mm.");
    }
    const dce = input.dce_positive === true;
    const notes = [];
    let score;
    let dceUpgrade = false;
    if (zone === "peripheral") {
        score = dwi;
        if (dwi === 3 && dce) {
            score = 4;
            dceUpgrade = true;
            notes.push("Positive DCE upgraded DWI 3 to PI-RADS 4.");
        }
    } else {
        score = t2w;
        if (t2w === 2 && dwi >= 4) {
            score = 3;
            notes.push("DWI ≥4 upgraded T2W 2 to PI-RADS 3.");
        } else if (t2w === 3 && dwi === 5) {
            score = 4;
            notes.push("DWI 5 upgraded T2W 3 to PI-RADS 4.");
        }
    }
    if (score >= 3) {
        notes.push("PI-RADS categorization alone does not determine biopsy management.");
    }
    return {
        lesion_id: String(input.lesion_id || ""),
        zone: zone,
        t2w_score: t2w,
        dwi_score: dwi,
        dce_positive: dce,
        pirads_score: score,
        primary_sequence: zone === "peripheral" ? "DWI" : "T2W",
        secondary_sequence: zone === "peripheral" ? "DCE" : "DWI",
        dce_upgrade_applied: dceUpgrade,
        size_mm: size,
        location: String(input.location || ""),
        biopsy_recommended: score >= 4,
        clinical_significance: ({
            1: "Very low", 2: "Low", 3: "Intermediate",
            4: "High", 5: "Very high"
        })[score],
        notes: notes
    };
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { scoreLesion };
}

if (typeof document !== "undefined") {
    const form = document.getElementById("lesion-form");
    const list = document.getElementById("results");
    const summary = document.getElementById("summary");
    const message = document.getElementById("message");
    const entries = [];

    function render() {
        list.replaceChildren();
        if (entries.length === 0) {
            summary.textContent = "No lesions assessed";
            list.textContent = "Enter sequence-level scores to assess a lesion.";
            return;
        }
        const max = Math.max(...entries.map(x => x.pirads_score));
        summary.textContent = entries.length + " lesion(s) · Highest PI-RADS " + max;
        entries.forEach(function (item) {
            const article = document.createElement("article");
            article.className = "result";
            const header = document.createElement("h3");
            header.textContent = item.lesion_id + " — PI-RADS " + item.pirads_score +
                " (" + item.clinical_significance + ")";
            article.append(header);
            const detail = document.createElement("p");
            detail.textContent = (item.zone === "peripheral" ? "Peripheral zone" : "Transition zone") +
                " · T2W " + item.t2w_score + " · DWI " + item.dwi_score +
                " · DCE " + (item.dce_positive ? "positive" : "negative") +
                (item.size_mm == null ? "" : " · " + item.size_mm + " mm") +
                (item.location ? " · " + item.location : "");
            article.append(detail);
            const explanation = document.createElement("p");
            explanation.className = "result-notes";
            explanation.textContent = item.notes.join(" ");
            article.append(explanation);
            list.append(article);
        });
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        message.textContent = "";
        try {
            const input = {
                lesion_id: "Lesion " + (entries.length + 1),
                zone: document.getElementById("zone").value,
                t2w: document.getElementById("t2w").value,
                dwi: document.getElementById("dwi").value,
                dce_positive: document.getElementById("dce").checked,
                size_mm: document.getElementById("size").value,
                location: document.getElementById("location").value.trim()
            };
            const result = scoreLesion(input);
            entries.push(result);
            render();
            message.textContent = result.lesion_id + " assessed. Review the result below.";
        } catch (error) {
            message.textContent = error.message;
        }
    });

    document.getElementById("reset").addEventListener("click", function () {
        entries.length = 0;
        form.reset();
        message.textContent = "";
        render();
    });

    document.getElementById("export").addEventListener("click", function () {
        message.textContent = "";
        if (!entries.length) {
            message.textContent = "Add at least one lesion before exporting.";
            return;
        }
        const data = {
            reference: "ACR PI-RADS v2.1",
            disclaimer: "Educational scoring aid, not a clinical diagnosis or management directive.",
            lesions: entries,
            max_pirads_score: Math.max(...entries.map(x => x.pirads_score))
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "pi-rads-assessment.json";
        document.body.append(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
    });
    render();
}
