"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { scoreLesion } = require("./app.js");

const lesion = (zone, t2w, dwi, dce_positive = false) => ({
    zone, t2w, dwi, dce_positive, lesion_id: "L1"
});

test("all 25 TZ score combinations match PI-RADS v2.1", () => {
    for (let t2w = 1; t2w <= 5; t2w++) {
        for (let dwi = 1; dwi <= 5; dwi++) {
            let expected = t2w;
            if (t2w === 2 && dwi >= 4) expected = 3;
            if (t2w === 3 && dwi === 5) expected = 4;
            assert.equal(scoreLesion(lesion("transition", t2w, dwi)).pirads_score, expected);
        }
    }
});
test("peripheral DWI 3 upgrades only with positive DCE", () => {
    assert.equal(scoreLesion(lesion("peripheral", 1, 3, false)).pirads_score, 3);
    assert.equal(scoreLesion(lesion("peripheral", 1, 3, true)).pirads_score, 4);
    assert.equal(scoreLesion(lesion("peripheral", 1, 4, true)).pirads_score, 4);
});
test("rejects unsupported anatomy and invalid input", () => {
    assert.throws(() => scoreLesion(lesion("central", 3, 5)), /Select peripheral/);
    assert.throws(() => scoreLesion(lesion("transition", 0, 5)), /scores/);
    assert.throws(() => scoreLesion({ ...lesion("transition", 3, 5), size_mm: "-2" }), /size/);
    assert.throws(() => scoreLesion({ ...lesion("transition", 3, 5), size_mm: "Infinity" }), /size/);
});
test("PI-RADS 3 is not an automatic biopsy directive", () => {
    assert.equal(scoreLesion(lesion("transition", 2, 5)).biopsy_recommended, false);
});
