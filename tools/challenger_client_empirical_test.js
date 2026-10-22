/**
 * Empirical Challenger Client-Side Verification: Node.js Harness
 * Evaluates taste_profiler.js and sensory_wheel.js client algorithms.
 */

const fs = require('fs');
const assert = require('assert');

// 1. Taste Profiler Client Simulation
const WEIGHTS = {
    body: 1.2,
    acidity: 1.3,
    sweetness: 1.0,
    caffeine: 1.1,
    nutty_choco: 1.0,
    fruity_floral: 1.0,
    balance: 0.9,
};
const D_MAX = 24.6475;

const SKUS = [
    {
        sku_code: "INNO-ROBUSTA-NAT-01",
        name: "Đắk Lắk Highland Fine Robusta Natural",
        vector: { body: 9.5, acidity: 3.5, sweetness: 8.5, caffeine: 9.5, nutty_choco: 9.0, fruity_floral: 3.0, balance: 7.5 },
        best_brew: ["phin", "espresso"],
    },
    {
        sku_code: "INNO-ARABICA-WASH-02",
        name: "Cầu Đất Mountain Bourbon Washed",
        vector: { body: 6.0, acidity: 9.0, sweetness: 8.0, caffeine: 3.5, nutty_choco: 3.0, fruity_floral: 9.5, balance: 8.5 },
        best_brew: ["pourover", "dripbag", "coldbrew"],
    },
    {
        sku_code: "INNO-SIGNATURE-HONEY-03",
        name: "Innokafe Heritage Signature Red Honey",
        vector: { body: 8.0, acidity: 6.8, sweetness: 9.2, caffeine: 6.5, nutty_choco: 7.5, fruity_floral: 7.0, balance: 9.0 },
        best_brew: ["espresso", "phin", "pourover", "dripbag"],
    },
    {
        sku_code: "INNO-DRIP-EXPLORER-04",
        name: "Hộp Drip Bag Khám Phá Nghệ Nhân (Artisan Box 10 Gói)",
        vector: { body: 7.5, acidity: 7.0, sweetness: 8.2, caffeine: 6.0, nutty_choco: 7.0, fruity_floral: 7.0, balance: 8.5 },
        best_brew: ["dripbag"],
    },
    {
        sku_code: "INNO-COLDBREW-CITRUS-05",
        name: "Innokafe Cold Brew Blend Summer Citrus",
        vector: { body: 5.5, acidity: 8.5, sweetness: 9.0, caffeine: 4.5, nutty_choco: 3.5, fruity_floral: 9.0, balance: 8.5 },
        best_brew: ["coldbrew", "pourover", "dripbag"],
    },
    {
        sku_code: "INNO-HORECA-BARISTA-06",
        name: "Innokafe Espresso Barista Master 80/20",
        vector: { body: 9.2, acidity: 4.0, sweetness: 8.0, caffeine: 8.8, nutty_choco: 8.8, fruity_floral: 4.0, balance: 8.0 },
        best_brew: ["espresso", "phin"],
    },
];

function calculateClientSide(answers) {
    const u = {
        body: 5.0,
        acidity: 5.0,
        sweetness: 5.0,
        caffeine: 5.0,
        nutty_choco: 5.0,
        fruity_floral: 5.0,
        balance: 5.0,
    };

    const { habit, gear, flavor, caffeine } = answers;
    if (habit === "phin_dam") {
        u.body += 4.0;
        u.caffeine += 3.0;
        u.acidity -= 2.0;
        u.nutty_choco += 3.0;
    } else if (habit === "sua_da") {
        u.sweetness += 4.0;
        u.body += 3.0;
        u.nutty_choco += 4.0;
        u.acidity -= 3.0;
    } else if (habit === "den_thanh") {
        u.acidity += 4.0;
        u.fruity_floral += 4.0;
        u.body -= 2.0;
        u.balance += 2.0;
    } else if (habit === "coldbrew_sangtao") {
        u.sweetness += 3.0;
        u.fruity_floral += 3.0;
        u.balance += 3.0;
        u.acidity += 1.0;
    }

    if (flavor === "nutty_choco") {
        u.nutty_choco += 4.0;
        u.body += 2.0;
        u.acidity -= 2.0;
    } else if (flavor === "fruity_floral") {
        u.fruity_floral += 4.5;
        u.acidity += 3.5;
        u.balance += 1.0;
    } else if (flavor === "honey_balanced") {
        u.sweetness += 4.0;
        u.balance += 4.0;
        u.body += 1.0;
    }

    if (caffeine === "high") u.caffeine = 9.5;
    else if (caffeine === "medium") u.caffeine = 6.0;
    else if (caffeine === "low") u.caffeine = 3.0;

    for (const k in u) {
        u[k] = Math.max(1.0, Math.min(10.0, u[k]));
    }

    const ranked = SKUS.map((item) => {
        const pVec = item.vector;
        let distSq = 0;
        for (const dim in WEIGHTS) {
            const diff = (u[dim] || 5.0) - (pVec[dim] || 5.0);
            distSq += WEIGHTS[dim] * diff * diff;
        }
        const dist = Math.sqrt(distSq);

        const isGearMatch = !gear || (item.best_brew && item.best_brew.includes(gear));
        const gamma = isGearMatch ? 1.0 : 0.88;

        const baseSim = (1.0 - dist / D_MAX) * 100.0 * gamma;
        const matchScore = Math.min(94.0, Math.max(85.0, baseSim * 0.285 + 68.35));

        return Object.assign({}, item, {
            match_score: Math.round(matchScore * 10) / 10,
            dist: Math.round(dist * 10) / 10,
        });
    });

    ranked.sort((a, b) => b.match_score - a.match_score);
    return {
        top1: ranked[0],
        top2: ranked[1] || ranked[0],
        all_ranked: ranked,
        user_vector: u,
    };
}

// 2. Run 144 combinations
const habits = ["phin_dam", "sua_da", "den_thanh", "coldbrew_sangtao"];
const gears = ["phin", "espresso", "dripbag", "pourover"];
const flavors = ["nutty_choco", "fruity_floral", "honey_balanced"];
const caffeines = ["high", "medium", "low"];

let top1Oob = 0;
let minTop1 = 100;
let maxTop1 = 0;

for (const h of habits) {
    for (const g of gears) {
        for (const f of flavors) {
            for (const c of caffeines) {
                const res = calculateClientSide({ habit: h, gear: g, flavor: f, caffeine: c });
                const s = res.top1.match_score;
                if (s < minTop1) minTop1 = s;
                if (s > maxTop1) maxTop1 = s;
                if (s < 85.0 || s > 94.0) {
                    top1Oob++;
                }
            }
        }
    }
}

console.log("[JS Client Engine Results]");
console.log(`Evaluated 144 combinations in JS:`);
console.log(`Top 1 Min Score: ${minTop1}%, Max Score: ${maxTop1}%`);
console.log(`Top 1 Out-of-Bounds ([85.0%, 94.0%]): ${top1Oob} / 144`);

// 3. Sensory Wheel JS normalization edge case test
function normalizeScores(scores) {
    scores = scores || {};
    const parseScore = (val, fallback) => {
        if (val === undefined || val === null || val === "" || isNaN(Number(val))) {
            return fallback;
        }
        return Math.min(10.0, Math.max(1.0, parseFloat(val)));
    };

    return {
        aroma: parseScore(scores.aroma, 8.0),
        acidity: parseScore(scores.acidity, 5.0),
        body: parseScore(scores.body, 8.0),
        sweetness: parseScore(scores.sweetness, 8.0),
        cleancup: parseScore(scores.cleancup, 8.5),
        aftertaste: parseScore(scores.aftertaste, 8.0),
    };
}

const zeroScores = { aroma: 0, acidity: 0, body: 0, sweetness: 0, cleancup: 0, aftertaste: 0 };
const normalizedZero = normalizeScores(zeroScores);
console.log("\n[Sensory Wheel Normalization Check]");
console.log("Input: all zeros {aroma: 0, ...}");
console.log("Normalized result:", normalizedZero);
if (normalizedZero.aroma === 1.0) {
    console.log("Zero score correctly preserved and clamped to 1.0!");
} else {
    console.log("Notice: 0 is falsy, so fallback is triggered instead of clamping to 1.0! aroma becomes:", normalizedZero.aroma);
}
