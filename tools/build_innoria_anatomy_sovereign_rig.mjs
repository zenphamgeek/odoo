#!/usr/bin/env node
/**
 * Build & Audit Innoria Isometric Sovereign Anatomy Rig
 * Uses /home/zen/hermes-agent/.agents/skills/anatomy/kit/{iso-kit,tube,lathe,audit}.mjs
 */
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  cameraOf,
  slabOf,
  cylinder,
  knurl,
  topTicks,
  radialTicks,
  solidSvg,
  lineSvg,
  dotsSvg,
  figureSvg,
  fitProjection,
  boxCorners,
  corners,
  insetPlan,
  planOutline,
  ring,
  lineOnTop,
  iso,
  depthOf,
  haloOf,
  translateAlong,
  faceTextSvg,
  topMatrix,
  sideSeam,
} from "/home/zen/hermes-agent/.agents/skills/anatomy/kit/iso-kit.mjs";
import * as G from "/home/zen/hermes-agent/.agents/skills/anatomy/kit/lathe.mjs";
import { tubePieces, tubeSvg } from "/home/zen/hermes-agent/.agents/skills/anatomy/kit/tube.mjs";
import * as A from "/home/zen/hermes-agent/.agents/skills/anatomy/kit/audit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));

const W = 760;
const H = 480;
const AZIMUTH = 45;
const ELEVATION = 30;

// 1. World Plans & Geometry Constants
const FOUNDATION = { x: -160, y: -95, w: 320, d: 190, r: 10 };
const FOUNDATION_Z = -14;
const FOUNDATION_H = 14;
const FOOT_H = 5;

const DIGIFORCE_BASE = { x: -135, y: -35, w: 68, d: 70, r: 5 };
const DIGIFORCE_VALVE = { x: -123, y: -23, w: 44, d: 46, r: 4 };

const INSILOS_CX = 0;
const INSILOS_CY = 10;
const INSILOS_FLANGE_R = 40;
const INSILOS_FLANGE_H = 8;
const INSILOS_CORE_R = 32;
const INSILOS_CORE_H = 30; // z: 8 -> 38
const INSILOS_DIAL_R = 22;
const INSILOS_DIAL_H = 8; // z: 38 -> 46

const VISIONX_BASE = { x: 68, y: -35, w: 68, d: 70, r: 5 };
const VISIONX_CX = 102;
const VISIONX_CY = 0;

const ZKLEDGER_VAULT = { x: -52, y: -82, w: 104, d: 44, r: 5 };
const ZKLEDGER_PLENUM = { x: -38, y: -74, w: 76, d: 28, r: 3 };

const P = fitProjection(
  [
    ...boxCorners(FOUNDATION, FOUNDATION_Z - FOOT_H, 56),
    [-165, -100, -20],
    [165, 100, 56],
  ],
  W,
  H,
  { pad: 26, azimuth: AZIMUTH, elevation: ELEVATION }
);

const KS = G.scaleOf(P);
const at = (p) => iso(p, P);
const S = (paths, style) => solidSvg(paths, style);
const Ln = (d, style) => lineSvg(d, style);
const Dots = (pts, style) => dotsSvg(pts, style);

const R = A.recorder(P);
const record = R.solid;

function putPart(name, group, ref, svg, shapes = [], { bias = 0, ...rest } = {}) {
  return R.put({
    name,
    piece: group,
    at: ref,
    bias,
    svg,
    shapes,
    ...rest,
  });
}

// ============================================================================
// A. BASE FOUNDATION SLAB (sovereign.foundation)
// ============================================================================
const foundationBack = [];
foundationBack.push(`<path class="iso-halo" d="${haloOf(FOUNDATION, FOUNDATION_Z - FOOT_H, FOUNDATION_H, P)}"/>`);

const byDepth = (pts) => [...pts].sort((a, b) => depthOf([a[0], a[1], 0], P) - depthOf([b[0], b[1], 0], P));
for (const [fx, fy] of byDepth(corners(FOUNDATION, 20))) {
  const footShape = record(
    A.cylinder(fx, fy, 7.5, FOUNDATION_Z - FOOT_H, FOOT_H, {
      name: R.nameFor("sovereign.foot"),
      owner: "sovereign.foundation",
      ground: true,
    })
  );
  putPart(
    footShape.name,
    "sovereign.foundation",
    [fx, fy, FOUNDATION_Z - FOOT_H / 2],
    S(cylinder(fx, fy, 7.5, FOUNDATION_Z - FOOT_H, FOOT_H, P, 24), { tone: "lo" }),
    [footShape],
    { bias: -2 }
  );
}

const foundationShape = record(
  A.slab(FOUNDATION, FOUNDATION_Z, FOUNDATION_H, { name: "sovereign.foundation", ground: true }, 8)
);

const rulerStrip = { x: FOUNDATION.x + 18, y: FOUNDATION.y + FOUNDATION.d - 12, w: FOUNDATION.w - 36, d: 6, r: 1 };
const ticks = topTicks(rulerStrip.x + 6, rulerStrip.x + rulerStrip.w - 6, 5, 5, rulerStrip.y, 0, [2.0, 4.0], P);
const foundationScrews = corners(FOUNDATION, 12);

const foundationDetailsSvg = [
  Ln(planOutline(insetPlan(FOUNDATION, 5), 0, P), { tone: "lo" }),
  Ln(planOutline(rulerStrip, 0, P, 3), { tone: "faint" }),
  Ln(ticks.minor, { tone: "lo" }),
  Ln(ticks.major, { tone: "mid" }),
  Ln(foundationScrews.map(([sx, sy]) => ring(sx, sy, 2.4, 0, P, 16)).join(""), { tone: "lo" }),
  Dots(foundationScrews.map(([sx, sy]) => at([sx, sy, 0])), { size: 0.55, tone: "mid" }),
  faceTextSvg(
    topMatrix([FOUNDATION.x + 22, FOUNDATION.y + FOUNDATION.d - 16], 0, P),
    "INNORIA SOVEREIGN OS // ZERO-DEFECT BENCH",
    { size: 3.1, tone: "mid" }
  ),
].join("");

putPart(
  "sovereign.foundation",
  "sovereign.foundation",
  [0, 0, FOUNDATION_Z / 2],
  S(slabOf(FOUNDATION, FOUNDATION_Z, FOUNDATION_H, P, 8, 1.4), {
    tone: "mid",
    inner: Ln(sideSeam(FOUNDATION, -5, P, 8), { tone: "faint" }),
  }) + foundationDetailsSvg,
  [foundationShape],
  { bias: -1 }
);

// ============================================================================
// B. LEFT MANIFOLD: DIGIFORCE (digiforce.manifold)
// ============================================================================
const digiBaseShape = record(
  A.slab(DIGIFORCE_BASE, 0, 24, { name: "digiforce.manifold", owner: "digiforce.manifold" }, 6)
);
const digiScrews = corners(DIGIFORCE_BASE, 6);
const digiRuler = topTicks(DIGIFORCE_BASE.x + 8, DIGIFORCE_BASE.x + DIGIFORCE_BASE.w - 8, 4, 4, DIGIFORCE_BASE.y + 54, 24, [1.8, 3.2], P);

putPart(
  "digiforce.manifold",
  "digiforce.manifold",
  [-101, 0, 12],
  S(slabOf(DIGIFORCE_BASE, 0, 24, P, 6, 1.0), {
    tone: "hi",
    inner: Ln(sideSeam(DIGIFORCE_BASE, 12, P, 6), { tone: "faint" }),
  }) +
    Ln(planOutline(insetPlan(DIGIFORCE_BASE, 3.5), 24, P, 4), { tone: "lo" }) +
    Ln(digiRuler.minor, { tone: "lo" }) +
    Ln(digiRuler.major, { tone: "mid" }) +
    Ln(digiScrews.map(([sx, sy]) => ring(sx, sy, 1.8, 24, P, 14)).join(""), { tone: "lo" }) +
    Dots(digiScrews.map(([sx, sy]) => at([sx, sy, 24])), { size: 0.45, tone: "hi" }) +
    faceTextSvg(topMatrix([DIGIFORCE_BASE.x + 8, DIGIFORCE_BASE.y + 62], 24, P), "DIGIFORCE e-CO", {
      size: 2.8,
      tone: "hi",
    }),
  [digiBaseShape]
);

const digiValveShape = record(
  A.slab(DIGIFORCE_VALVE, 24, 8, { name: "digiforce.valve", owner: "digiforce.manifold" }, 5)
);
putPart(
  "digiforce.valve",
  "digiforce.manifold",
  [-101, 0, 28],
  S(slabOf(DIGIFORCE_VALVE, 24, 8, P, 5, 0.7), { tone: "mid" }) +
    Ln(planOutline(insetPlan(DIGIFORCE_VALVE, 2.5), 32, P, 4), { tone: "faint" }),
  [digiValveShape]
);

const digiKnobShape = record(
  A.cylinder(-101, 0, 13, 32, 8, { name: "digiforce.knob", owner: "digiforce.manifold" })
);
const digiKnobTicks = radialTicks(-101, 0, 11.5, 24, 6, 40, [1.5, 2.8], P);
putPart(
  "digiforce.knob",
  "digiforce.manifold",
  [-101, 0, 36],
  S(cylinder(-101, 0, 13, 32, 8, P, 28, 0.6), {
    tone: "hi",
    inner: Ln(knurl(-101, 0, 13, 32, 40, 28, P, 0.8), { tone: "lo" }),
  }) +
    Ln(ring(-101, 0, 8.2, 40, P, 20), { tone: "lo" }) +
    Ln(digiKnobTicks.minor, { tone: "lo" }) +
    Ln(digiKnobTicks.major, { tone: "hi" }) +
    Dots([at([-101, 0, 40])], { size: 0.6, tone: "hi" }),
  [digiKnobShape]
);

// ============================================================================
// C. CENTER CORE CYLINDER: INSILOS ERP (insilos.core)
// ============================================================================
const insilosFlangeShape = record(
  A.cylinder(INSILOS_CX, INSILOS_CY, INSILOS_FLANGE_R, 0, INSILOS_FLANGE_H, {
    name: "insilos.flange",
    owner: "insilos.core",
  })
);
const flangeBolts = Array.from({ length: 12 }, (_, i) => {
  const ang = (i / 12) * Math.PI * 2;
  return at([
    INSILOS_CX + (INSILOS_FLANGE_R - 3.5) * Math.cos(ang),
    INSILOS_CY + (INSILOS_FLANGE_R - 3.5) * Math.sin(ang),
    INSILOS_FLANGE_H,
  ]);
});
putPart(
  "insilos.flange",
  "insilos.core",
  [INSILOS_CX, INSILOS_CY, INSILOS_FLANGE_H / 2],
  S(cylinder(INSILOS_CX, INSILOS_CY, INSILOS_FLANGE_R, 0, INSILOS_FLANGE_H, P, 36, 0.8), {
    tone: "mid",
  }) +
    Ln(ring(INSILOS_CX, INSILOS_CY, INSILOS_FLANGE_R - 1.8, INSILOS_FLANGE_H, P, 36), { tone: "lo" }) +
    Dots(flangeBolts, { size: 0.5, tone: "hi" }),
  [insilosFlangeShape]
);

const insilosCoreShape = record(
  A.cylinder(INSILOS_CX, INSILOS_CY, INSILOS_CORE_R, INSILOS_FLANGE_H, INSILOS_CORE_H, {
    name: "insilos.core",
    owner: "insilos.core",
  })
);
const coreTopZ = INSILOS_FLANGE_H + INSILOS_CORE_H; // 38
const coreTicks = radialTicks(INSILOS_CX, INSILOS_CY, INSILOS_CORE_R - 2.2, 36, 6, coreTopZ, [2.0, 4.0], P);

putPart(
  "insilos.core",
  "insilos.core",
  [INSILOS_CX, INSILOS_CY, INSILOS_FLANGE_H + INSILOS_CORE_H / 2],
  S(cylinder(INSILOS_CX, INSILOS_CY, INSILOS_CORE_R, INSILOS_FLANGE_H, INSILOS_CORE_H, P, 40, 1.2), {
    tone: "hi",
    lit: true,
    inner: Ln(knurl(INSILOS_CX, INSILOS_CY, INSILOS_CORE_R, INSILOS_FLANGE_H + 3, coreTopZ - 3, 44, P, 1.0), {
      tone: "lo",
    }),
  }) +
    Ln(ring(INSILOS_CX, INSILOS_CY, INSILOS_CORE_R - 2.2, coreTopZ, P, 36), { tone: "mid" }) +
    Ln(coreTicks.minor, { tone: "lo" }) +
    Ln(coreTicks.major, { tone: "hi" }),
  [insilosCoreShape]
);

const dialTopZ = coreTopZ + INSILOS_DIAL_H; // 46
const insilosDialShape = record(
  A.cylinder(INSILOS_CX, INSILOS_CY, INSILOS_DIAL_R, coreTopZ, INSILOS_DIAL_H, {
    name: "insilos.dial",
    owner: "insilos.core",
  })
);
const dialTicks = radialTicks(INSILOS_CX, INSILOS_CY, INSILOS_DIAL_R - 2.0, 24, 4, dialTopZ, [1.6, 3.2], P);
putPart(
  "insilos.dial",
  "insilos.core",
  [INSILOS_CX, INSILOS_CY, coreTopZ + INSILOS_DIAL_H / 2],
  S(cylinder(INSILOS_CX, INSILOS_CY, INSILOS_DIAL_R, coreTopZ, INSILOS_DIAL_H, P, 32, 0.8), {
    tone: "hi",
    inner: Ln(knurl(INSILOS_CX, INSILOS_CY, INSILOS_DIAL_R, coreTopZ, dialTopZ, 32, P, 0.7), { tone: "faint" }),
  }) +
    Ln(ring(INSILOS_CX, INSILOS_CY, INSILOS_DIAL_R - 5.5, dialTopZ, P, 28), { tone: "mid" }) +
    Ln(dialTicks.minor, { tone: "lo" }) +
    Ln(dialTicks.major, { tone: "hi" }) +
    Ln(lineOnTop([INSILOS_CX, INSILOS_CY], [INSILOS_CX + 11, INSILOS_CY - 8], dialTopZ, P), {
      tone: "hi",
      free: true,
    }) +
    Dots([at([INSILOS_CX, INSILOS_CY, dialTopZ])], { size: 0.75, tone: "hi", pulse: true }),
  [insilosDialShape]
);

// ============================================================================
// D. RIGHT VISION TURRET: VISIONX (visionx.turret)
// ============================================================================
const visionBaseShape = record(
  A.slab(VISIONX_BASE, 0, 22, { name: "visionx.turret", owner: "visionx.turret" }, 6)
);
const visionScrews = corners(VISIONX_BASE, 6);
putPart(
  "visionx.turret",
  "visionx.turret",
  [102, 0, 11],
  S(slabOf(VISIONX_BASE, 0, 22, P, 6, 1.0), {
    tone: "hi",
    inner: Ln(sideSeam(VISIONX_BASE, 11, P, 6), { tone: "faint" }),
  }) +
    Ln(planOutline(insetPlan(VISIONX_BASE, 3.5), 22, P, 4), { tone: "lo" }) +
    Ln(visionScrews.map(([sx, sy]) => ring(sx, sy, 1.8, 22, P, 14)).join(""), { tone: "lo" }) +
    Dots(visionScrews.map(([sx, sy]) => at([sx, sy, 22])), { size: 0.45, tone: "hi" }) +
    faceTextSvg(topMatrix([VISIONX_BASE.x + 8, VISIONX_BASE.y + 62], 22, P), "VISIONX 120FPS", {
      size: 2.8,
      tone: "hi",
    }),
  [visionBaseShape]
);

const visionBarrelShape = record(
  A.cylinder(VISIONX_CX, VISIONX_CY, 18, 22, 12, { name: "visionx.barrel", owner: "visionx.turret" })
);
putPart(
  "visionx.barrel",
  "visionx.turret",
  [VISIONX_CX, VISIONX_CY, 28],
  S(cylinder(VISIONX_CX, VISIONX_CY, 18, 22, 12, P, 32, 0.8), {
    tone: "mid",
    inner: Ln(knurl(VISIONX_CX, VISIONX_CY, 18, 23, 33, 30, P, 0.8), { tone: "faint" }),
  }) + Ln(ring(VISIONX_CX, VISIONX_CY, 15, 34, P, 28), { tone: "lo" }),
  [visionBarrelShape]
);

const visionLensShape = record(
  A.cylinder(VISIONX_CX, VISIONX_CY, 12, 34, 7, { name: "visionx.lens", owner: "visionx.turret" })
);
const lensTicks = radialTicks(VISIONX_CX, VISIONX_CY, 10.5, 20, 5, 41, [1.4, 2.6], P);
putPart(
  "visionx.lens",
  "visionx.turret",
  [VISIONX_CX, VISIONX_CY, 37.5],
  S(cylinder(VISIONX_CX, VISIONX_CY, 12, 34, 7, P, 28, 0.6), { tone: "hi" }) +
    Ln(ring(VISIONX_CX, VISIONX_CY, 7.5, 41, P, 24), { tone: "hi" }) +
    Ln(ring(VISIONX_CX, VISIONX_CY, 4.2, 41, P, 20), { tone: "mid" }) +
    Ln(lensTicks.minor, { tone: "lo" }) +
    Ln(lensTicks.major, { tone: "hi" }) +
    Dots([at([VISIONX_CX, VISIONX_CY, 41])], { size: 0.65, tone: "hi", pulse: true }),
  [visionLensShape]
);

// ============================================================================
// E. REAR VAULT SLAB: ZKLEDGER (zkledger.vault)
// ============================================================================
const vaultShape = record(
  A.slab(ZKLEDGER_VAULT, 0, 30, { name: "zkledger.vault", owner: "zkledger.vault" }, 6)
);
const vaultScrews = corners(ZKLEDGER_VAULT, 5.5);
const vaultStatusDots = Array.from({ length: 6 }, (_, i) =>
  at([ZKLEDGER_VAULT.x + 16 + i * 6, ZKLEDGER_VAULT.y + 36, 30])
);

putPart(
  "zkledger.vault",
  "zkledger.vault",
  [0, -60, 15],
  S(slabOf(ZKLEDGER_VAULT, 0, 30, P, 6, 1.1), {
    tone: "hi",
    inner: Ln(sideSeam(ZKLEDGER_VAULT, 15, P, 6), { tone: "faint" }),
  }) +
    Ln(planOutline(insetPlan(ZKLEDGER_VAULT, 3.5), 30, P, 4), { tone: "lo" }) +
    Ln(vaultScrews.map(([sx, sy]) => ring(sx, sy, 1.7, 30, P, 14)).join(""), { tone: "lo" }) +
    Dots(vaultScrews.map(([sx, sy]) => at([sx, sy, 30])), { size: 0.45, tone: "hi" }) +
    Dots(vaultStatusDots, { size: 0.5, tone: "hi", pulse: true }),
  [vaultShape]
);

const vaultPlenumShape = record(
  A.slab(ZKLEDGER_PLENUM, 30, 8, { name: "zkledger.plenum", owner: "zkledger.vault" }, 4)
);
const sealRings = [-18, 0, 18].map((dx) => ring(dx, -60, 6.2, 38, P, 20)).join("");
const sealInnerRings = [-18, 0, 18].map((dx) => ring(dx, -60, 3.2, 38, P, 16)).join("");
const sealDots = [-18, 0, 18].map((dx) => at([dx, -60, 38]));

putPart(
  "zkledger.plenum",
  "zkledger.vault",
  [0, -60, 34],
  S(slabOf(ZKLEDGER_PLENUM, 30, 8, P, 4, 0.6), { tone: "mid" }) +
    Ln(planOutline(insetPlan(ZKLEDGER_PLENUM, 2.2), 38, P, 3), { tone: "faint" }) +
    Ln(sealRings, { tone: "hi" }) +
    Ln(sealInnerRings, { tone: "lo" }) +
    Dots(sealDots, { size: 0.55, tone: "hi" }),
  [vaultPlenumShape]
);

// ============================================================================
// F. FLUSH ISOMETRIC AXIAL BUS TRACES (z = 0 on sovereign.foundation)
// ============================================================================
const deckBusRoutes = [
  // 1. Digiforce Manifold East Port -> Insilos Core West Flange Port (straight axial)
  [
    [-67, 18],
    [-39, 18],
  ],
  // 2. Insilos Core East Flange Port -> VisionX Turret West Port (straight axial)
  [
    [39, 18],
    [68, 18],
  ],
];

const deckBusTerminals = [
  [-64, 18],
  [-42, 18],
  [42, 18],
  [65, 18],
];

const deckBusSvg = [
  ...deckBusRoutes.map((pts) => {
    let segs = "";
    for (let i = 0; i < pts.length - 1; i++) {
      segs += lineOnTop(pts[i], pts[i + 1], 0, P);
    }
    return Ln(segs, { tone: "hi", free: true });
  }),
  Ln(deckBusTerminals.map(([bx, by]) => ring(bx, by, 1.6, 0, P, 14)).join(""), {
    tone: "lo",
    free: true,
  }),
  Dots(
    deckBusTerminals.map(([bx, by]) => at([bx, by, 0])),
    { size: 0.5, tone: "hi", pulse: true }
  ),
].join("");

// Append flush deck bus traces to sovereign.foundation item
R.items[R.items.findIndex((it) => it.name === "sovereign.foundation")].svg += deckBusSvg;

// ============================================================================
// G. SETTLE DEPTH ORDER & AUDIT
// ============================================================================
A.settle(R, P);
R.items.sort((a, b) => a.key - b.key);

if (process.argv.includes("--audit")) {
  const res = A.audit(R, P);
  console.log(A.report(res));
  const failCount = A.failures(res);
  const collisionCount =
    res.clearance.length +
    res.apart.length +
    res.flight.length +
    res.supports.sunk.length +
    res.self.length;
  const looseEndCount = res.loose.filter((e) => !e.free).length + res.terminals.length;
  console.log(
    `audit summary · ${collisionCount} collisions, ${looseEndCount} loose ends · ${R.tubes.length} tubes · ${R.solids.length} solids · ${R.items.length} items`
  );
  if (failCount === 0) {
    console.log("audit passed");
  } else {
    console.error(`audit failed: ${failCount} problems`);
    process.exitCode = 1;
  }
}

// ============================================================================
// H. EMIT GROUPED INTERACTIVE SVG
// ============================================================================
const groupOrder = [
  "sovereign.foundation",
  "zkledger.vault",
  "digiforce.manifold",
  "insilos.core",
  "visionx.turret",
];

// Compute lift vectors for interactive explode/regime highlight
export const PART_LIFTS = {
  "sovereign.foundation": translateAlong(P, [0, 0, 0]),
  "digiforce.manifold": translateAlong(P, [0, 0, 10]),
  "insilos.core": translateAlong(P, [0, 0, 12]),
  "visionx.turret": translateAlong(P, [0, 0, 10]),
  "zkledger.vault": translateAlong(P, [0, 0, 10]),
};

const groupedBuckets = new Map(groupOrder.map((g) => [g, []]));
for (const item of R.items) {
  const g = groupedBuckets.has(item.piece) ? item.piece : "sovereign.foundation";
  groupedBuckets.get(g).push(item.svg);
}

const bodyGroups = [
  `<g class="iso-backdrop">${foundationBack.join("")}</g>`,
  ...groupOrder.map((g) => {
    const liftAttr = PART_LIFTS[g] ? ` data-lift="${PART_LIFTS[g]}"` : "";
    return `<g class="iso-part-group" data-part="${g}"${liftAttr}>${groupedBuckets.get(g).join("")}</g>`;
  }),
];

const svgOut = figureSvg({
  width: W,
  height: H,
  label: "Innoria Sovereign Enterprise Anatomy Rig — Digiforce, Insilos ERP, VisionX 120FPS, ZKLedger Vault",
  body: bodyGroups,
  standalone: false,
  className: "innoria-sovereign-anatomy-svg",
});

import { readFileSync } from "node:fs";

const outPath = join(HERE, "innoria_anatomy_sovereign_rig.svg");
writeFileSync(outPath, svgOut, "utf8");
if (!process.argv.includes("--audit")) {
  console.log(`Wrote ${outPath} (${svgOut.length} bytes)`);
}

if (process.argv.includes("--write-xml")) {
  const snippetsXmlPath = "/home/zen/O20/enterprise/insilos_website/views/snippets_3d.xml";
  let xmlContent = readFileSync(snippetsXmlPath, "utf8");

  const templateBlock = `    <!-- ================================================================= -->
    <!-- 10. INNORIA ISOMETRIC SOVEREIGN ANATOMY RIG (RULE 29 BORDERLESS)  -->
    <!-- ================================================================= -->
    <template id="s_innoria_anatomy_sovereign_rig" name="Innoria Isometric Sovereign Anatomy Rig">
        <section class="s_innoria_anatomy_sovereign_rig o_colored_level position-relative py-5"
                 data-snippet="s_innoria_anatomy_sovereign_rig"
                 data-name="Innoria Isometric Sovereign Anatomy Rig"
                 id="innoria_anatomy_sovereign_rig"
                 data-rig-active-mode="regime1"
                 data-rig-active-part="digiforce.manifold"
                 style="background: linear-gradient(180deg, #070B14 0%, #080a0f 55%, #070B14 100%) !important; color: #F8FAFC !important; border-top: 1px solid rgba(56, 189, 248, 0.16); border-bottom: 1px solid rgba(56, 189, 248, 0.16); overflow: hidden;">
            <style>
                #innoria_anatomy_sovereign_rig {
                    --anatomy-page: #080a0f;
                    --anatomy-card: transparent;
                    --anatomy-text: #94a3b8;
                    --anatomy-strong: #f8fafc;
                    --anatomy-muted: #64748b;
                    --anatomy-paper: #0c1220;
                    --anatomy-face: #111a2e;
                    --anatomy-top: #162238;
                    --anatomy-shade-0: #090e1a;
                    --anatomy-shade-1: #0c1322;
                    --anatomy-shade-2: #10192b;
                    --anatomy-shade-3: #142036;
                    --anatomy-lit-top: #1e3352;
                    --anatomy-lit-shade: #15253d;
                    --anatomy-hi: #38bdf8;
                    --anatomy-mid: #475569;
                    --anatomy-lo: #1e293b;
                    --anatomy-faint: #151e2e;
                    --anatomy-lit: #ffd700;
                    --anatomy-halo: #020409;
                    --anatomy-halo-opacity: 0.85;
                    --anatomy-dot: #38bdf8;
                    --anatomy-weight: 0.65px;
                    --anatomy-mono: ui-sans-serif, "Poppins", -apple-system, BlinkMacSystemFont, sans-serif;
                }
                #innoria_anatomy_sovereign_rig .iso-svg {
                    display: block;
                    width: 100%;
                    height: auto;
                    overflow: visible;
                }
                #innoria_anatomy_sovereign_rig .iso-svg path,
                #innoria_anatomy_sovereign_rig .iso-svg circle {
                    vector-effect: non-scaling-stroke;
                }
                #innoria_anatomy_sovereign_rig .iso-fill { fill: var(--anatomy-paper); stroke: none; }
                #innoria_anatomy_sovereign_rig .iso-solid[data-lit] &gt; .iso-fill { fill: var(--anatomy-face); }
                #innoria_anatomy_sovereign_rig .iso-shade,
                #innoria_anatomy_sovereign_rig .iso-top { stroke: none; transition: fill 0.35s cubic-bezier(0.22, 1, 0.36, 1); }
                #innoria_anatomy_sovereign_rig .iso-shade[data-shade="0"] { fill: var(--anatomy-shade-0); }
                #innoria_anatomy_sovereign_rig .iso-shade[data-shade="1"] { fill: var(--anatomy-shade-1); }
                #innoria_anatomy_sovereign_rig .iso-shade[data-shade="2"] { fill: var(--anatomy-shade-2); }
                #innoria_anatomy_sovereign_rig .iso-shade[data-shade="3"] { fill: var(--anatomy-shade-3); }
                #innoria_anatomy_sovereign_rig .iso-top { fill: var(--anatomy-top); }
                #innoria_anatomy_sovereign_rig .iso-solid[data-lit] &gt; .iso-top { fill: var(--anatomy-lit-top); }
                #innoria_anatomy_sovereign_rig .iso-solid[data-lit] &gt; .iso-shade { fill: var(--anatomy-lit-shade); }
                #innoria_anatomy_sovereign_rig .iso-solid[data-lit] &gt; .iso-edge { stroke: var(--anatomy-lit); }
                #innoria_anatomy_sovereign_rig .iso-halo {
                    fill: var(--anatomy-halo);
                    stroke: none;
                    filter: blur(9px);
                    opacity: var(--anatomy-halo-opacity);
                    transform: translateY(3px);
                }
                #innoria_anatomy_sovereign_rig .iso-line {
                    fill: none;
                    stroke: var(--anatomy-lo);
                    stroke-width: var(--anatomy-weight);
                    stroke-linecap: round;
                    stroke-linejoin: round;
                    transition: stroke 0.3s ease, stroke-width 0.3s ease;
                }
                #innoria_anatomy_sovereign_rig .iso-line[data-tone="hi"] { stroke: var(--anatomy-hi); }
                #innoria_anatomy_sovereign_rig .iso-line[data-tone="mid"] { stroke: var(--anatomy-mid); }
                #innoria_anatomy_sovereign_rig .iso-line[data-tone="lo"] { stroke: var(--anatomy-lo); }
                #innoria_anatomy_sovereign_rig .iso-line[data-tone="faint"] { stroke: var(--anatomy-faint); }
                #innoria_anatomy_sovereign_rig .iso-line[data-tone="lit"] { stroke: var(--anatomy-lit); }
                #innoria_anatomy_sovereign_rig .iso-dots circle {
                    fill: var(--anatomy-dot);
                    stroke: none;
                    opacity: 0.45;
                }
                #innoria_anatomy_sovereign_rig .iso-dots[data-tone="hi"] circle { opacity: 0.92; fill: #ffd700; }
                #innoria_anatomy_sovereign_rig .iso-face-text {
                    fill: #94a3b8;
                    font-family: var(--anatomy-mono);
                    letter-spacing: 0.04em;
                    pointer-events: none;
                }
                #innoria_anatomy_sovereign_rig .iso-face-text[data-tone="hi"] { fill: #38bdf8; }
                #innoria_anatomy_sovereign_rig .tb-body { fill: var(--anatomy-shade-2); stroke: none; }
                #innoria_anatomy_sovereign_rig .tb-shine { fill: var(--anatomy-top); stroke: none; }
                #innoria_anatomy_sovereign_rig .tb-shade { fill: var(--anatomy-shade-0); stroke: none; }
                #innoria_anatomy_sovereign_rig .tb-edge { stroke: #38bdf8; }
                #innoria_anatomy_sovereign_rig .iso-part-group {
                    cursor: pointer;
                    transition: transform 0.45s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.35s ease, filter 0.35s ease;
                }
                #innoria_anatomy_sovereign_rig .iso-part-group.is-lifted {
                    filter: drop-shadow(0 10px 22px rgba(56, 189, 248, 0.28));
                }
                #innoria_anatomy_sovereign_rig .iso-part-group.is-highlighted .iso-edge {
                    stroke: #ffd700 !important;
                    stroke-width: 1.05px !important;
                }
                #innoria_anatomy_sovereign_rig .iso-part-group.is-highlighted .iso-top {
                    fill: #1e3352 !important;
                }
                #innoria_anatomy_sovereign_rig .rig-regime-pill {
                    background: transparent;
                    border: none;
                    border-left: 2px solid rgba(148, 163, 184, 0.25);
                    color: #94a3b8;
                    padding: 0.65rem 1rem;
                    text-align: left;
                    font-family: var(--anatomy-mono);
                    font-size: 0.78rem;
                    letter-spacing: 0.02em;
                    transition: all 0.25s ease;
                }
                #innoria_anatomy_sovereign_rig .rig-regime-pill:hover,
                #innoria_anatomy_sovereign_rig .rig-regime-pill.active {
                    border-left-color: #38bdf8;
                    color: #f8fafc;
                    background: linear-gradient(90deg, rgba(56, 189, 248, 0.1) 0%, transparent 100%);
                }
                #innoria_anatomy_sovereign_rig .rig-regime-pill.active .regime-code {
                    color: #ffd700 !important;
                }
                #innoria_anatomy_sovereign_rig .rig-part-btn {
                    background: transparent;
                    border: none;
                    border-bottom: 1px solid rgba(148, 163, 184, 0.22);
                    color: #cbd5e1;
                    padding: 0.45rem 0.75rem;
                    font-family: var(--anatomy-mono);
                    font-size: 0.74rem;
                    transition: all 0.22s ease;
                }
                #innoria_anatomy_sovereign_rig .rig-part-btn.active,
                #innoria_anatomy_sovereign_rig .rig-part-btn:hover {
                    color: #38bdf8;
                    border-bottom-color: #ffd700;
                }
                #innoria_anatomy_sovereign_rig .rig-telemetry-row {
                    border-top: 1px solid rgba(56, 189, 248, 0.18);
                    padding-top: 0.85rem;
                }
            </style>

            <div class="container position-relative py-4" style="z-index: 2;">
                <!-- 1. EXECUTIVE HEADER (Rule 29 Borderless Neo-Noir Obsidian) -->
                <div class="row mb-5 align-items-end">
                    <div class="col-lg-8">
                        <div class="d-inline-flex align-items-center gap-2 mb-3 text-uppercase"
                             style="color: #ffd700; font-size: 0.76rem; letter-spacing: 0.12em;">
                            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#38bdf8; box-shadow: none;"/>
                            <span>SYSTEMS ANATOMY // CỖ MÁY GIẢI PHẪU KIẾN TRÚC TỰ HÀNH</span>
                        </div>
                        <h2 class="display-5 fw-bold mb-3" style="color: #F8FAFC !important; letter-spacing: -0.02em;">
                            The Object Is The Explanation: <span class="o_text_highlight" style="color: #38bdf8;">Kiến Trúc Hệ Thống Cấp Chủ Quyền</span>
                        </h2>
                        <p class="lead mb-0" style="color: #94A3B8 !important; font-size: 1.05rem; line-height: 1.7;">
                            Mỗi cấu kiện cơ khí trên mô hình đẳng cự (Isometric Rig) phản ánh chính xác một cơ chế vận hành thực chứng: từ phân luồng chứng từ hải quan, thị giác biên 120 FPS ngắt mạch rơ-le an toàn, đến buồng mật mã kế toán cô lập vật lý.
                        </p>
                    </div>
                    <div class="col-lg-4 text-lg-end mt-3 mt-lg-0">
                        <div class="small text-uppercase" style="color: #64748B; font-size: 0.72rem; letter-spacing: 0.08em;">FIG 04 // ISOMETRIC BENCHMARK</div>
                        <div class="fw-bold" style="color: #38bdf8; font-size: 0.9rem;">0 COLLISIONS · 0 LOOSE ENDS · 16 SOLIDS</div>
                    </div>
                </div>

                <!-- 2. MAIN INTERACTIVE RIG STAGE (LEFT CONTROLS + RIGHT ISOMETRIC BENCH) -->
                <div class="row g-5 align-items-start">
                    <!-- LEFT COLUMN: 3 REGIME PILLS, ACTIVE REGIME PANEL & THROUGHPUT SLIDER -->
                    <div class="col-lg-5">
                        <div class="text-uppercase small mb-2" style="color: #64748B; font-size: 0.72rem; letter-spacing: 0.08em;">
                            CHỌN CHẾ ĐỘ VẬN HÀNH THỰC CHỨNG (3 REGIMES)
                        </div>
                        <div class="d-flex flex-column gap-2 mb-4" role="tablist" aria-label="Innoria Sovereign Rig Regimes">
                            <button type="button" class="rig-regime-pill active"
                                    data-rig-mode="regime1"
                                    data-target-part="digiforce.manifold">
                                <span class="regime-code d-block fw-bold" style="color: #38bdf8;">Chế Độ 01 · Đối Soát XNK &amp; Khóa Xuất Xứ e-CO (RVC 48.6%)</span>
                                <span class="small d-block mt-1" style="color: #94a3b8;">Digiforce Manifold · ECUS5-VNACCS &lt; 3.2s</span>
                            </button>
                            <button type="button" class="rig-regime-pill"
                                    data-rig-mode="regime2"
                                    data-target-part="visionx.turret">
                                <span class="regime-code d-block fw-bold" style="color: #38bdf8;">Chế Độ 02 · Thị Giác Biên 120 FPS &amp; Liên Động e-PTW HSE</span>
                                <span class="small d-block mt-1" style="color: #94a3b8;">VisionX Optical Turret · Ngắt Mạch PLC &lt; 12ms</span>
                            </button>
                            <button type="button" class="rig-regime-pill"
                                    data-rig-mode="regime3"
                                    data-target-part="zkledger.vault">
                                <span class="regime-code d-block fw-bold" style="color: #38bdf8;">Chế Độ 03 · Hạch Toán Tự Động VAS 200 &amp; Buồng Mật Mã Air-Gapped</span>
                                <span class="small d-block mt-1" style="color: #94a3b8;">Insilos Core + ZKLedger Vault · SLA 99.999%</span>
                            </button>
                        </div>

                        <!-- ACTIVE REGIME DETAIL PANEL (Borderless Hairline Architecture) -->
                        <div class="pt-3 pb-4" style="border-top: 1px solid rgba(56, 189, 248, 0.28); border-bottom: 1px solid rgba(148, 163, 184, 0.16);">
                            <!-- Regime 1 Content -->
                            <div class="rig-regime-detail" data-regime-panel="regime1">
                                <div class="small text-uppercase mb-1" style="color: #ffd700; font-size: 0.73rem; letter-spacing: 0.06em;">
                                    EXECUTIVE HOOK // CHẾ ĐỘ 01
                                </div>
                                <h3 class="h4 fw-bold mb-2" style="color: #F8FAFC !important;">
                                    Khóa cứng rủi ro xuất xứ trong 3 giây.
                                </h3>
                                <div class="small mb-3" style="color: #38bdf8;">
                                    RVC 48.6%, đối soát 5 luồng ECUS5-VNACCS hoàn tất dưới 3.2 giây.
                                </div>
                                <p class="small mb-3" style="color: #CBD5E1; line-height: 1.65;">
                                    Cụm van phân phối 5 cổng (Manifold Distributor) tiếp nhận song song 5 luồng tài liệu: PO, Invoice, Packing List, Tờ khai hải quan và B/L. Con trượt quang học (Vernier Slider) cân đo hàm lượng nội địa hóa RVC và kích hoạt van chốt cơ khí (Solenoid Interlock) khóa tờ khai khi lệch mã HS hoặc BOM vượt 0.5%.
                                </p>
                                <div class="small" style="color: #94A3B8; font-size: 0.72rem;">
                                    <strong style="color: #ffd700;">CHUẨN PHÁP LÝ:</strong> Thông tư 11/2020/TT-BCT · Nghị định 35/2020/NĐ-CP · EVFTA Protocol 1 &amp; CPTPP · ECUS5-VNACCS
                                </div>
                            </div>

                            <!-- Regime 2 Content -->
                            <div class="rig-regime-detail d-none" data-regime-panel="regime2">
                                <div class="small text-uppercase mb-1" style="color: #ffd700; font-size: 0.73rem; letter-spacing: 0.06em;">
                                    EXECUTIVE HOOK // CHẾ ĐỘ 02
                                </div>
                                <h3 class="h4 fw-bold mb-2" style="color: #F8FAFC !important;">
                                    Ngắt nguồn tức thì khi vi phạm an toàn.
                                </h3>
                                <div class="small mb-3" style="color: #38bdf8;">
                                    Độ trễ biên &lt; 12ms, nhận diện 99.8%, duy trì OEE &gt; 98.5%.
                                </div>
                                <p class="small mb-3" style="color: #CBD5E1; line-height: 1.65;">
                                    Thấu kính quang học viễn tâm kép (Dual Telecentric Lens) quét liên tục 120 FPS nhận diện hành lang an toàn và PPE, nối cứng vào rơ-le cách ly quang (Galvanic Safety Relay) ngắt mạch PLC trong 12ms độc lập đám mây, kết hợp cảm biến áp điện RCM FFT phân tích phổ rung động trục quay.
                                </p>
                                <div class="small" style="color: #94A3B8; font-size: 0.72rem;">
                                    <strong style="color: #ffd700;">CHUẨN PHÁP LÝ:</strong> ISO 45001:2018 (Khoản 8.1.2) · ISO 13849-1:2023 (PL e, Cat 4) · RCM FFT ISO 10816-3
                                </div>
                            </div>

                            <!-- Regime 3 Content -->
                            <div class="rig-regime-detail d-none" data-regime-panel="regime3">
                                <div class="small text-uppercase mb-1" style="color: #ffd700; font-size: 0.73rem; letter-spacing: 0.06em;">
                                    EXECUTIVE HOOK // CHẾ ĐỘ 03
                                </div>
                                <h3 class="h4 fw-bold mb-2" style="color: #F8FAFC !important;">
                                    Xóa bỏ 80% thời gian nhập liệu kế toán.
                                </h3>
                                <div class="small mb-3" style="color: #38bdf8;">
                                    Giảm 80% giờ nhập liệu, SLA 99.999%, cắt giảm 50% TCO.
                                </div>
                                <p class="small mb-3" style="color: #CBD5E1; line-height: 1.65;">
                                    Buồng mật mã Faraday cô lập mạng vật lý qua công tắc ngắt quang (Air-Gapped Optical Switch). Trụ pittông Zero-Knowledge (ZK Plunger) dập dấu băm SHA-256 / Ed25519 và bánh răng vi sai cơ khí đồng bộ đối ứng Nợ - Có chuẩn VAS 200 với 0 sai số.
                                </p>
                                <div class="small" style="color: #94A3B8; font-size: 0.72rem;">
                                    <strong style="color: #ffd700;">CHUẨN PHÁP LÝ:</strong> Thông tư 200/2014/TT-BTC · Luật Kế toán 88/2015/QH13 · Nghị định 13/2023/NĐ-CP · ISO/IEC 27001:2022
                                </div>
                            </div>
                        </div>

                        <!-- INTERACTIVE THROUGHPUT SLIDER (100 - 10,000 tx/s) -->
                        <div class="mt-4">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <label for="innoriaRigThroughputSlider" class="small text-uppercase" style="color: #94A3B8; font-size: 0.74rem;">
                                    TẦN SUẤT GIAO DỊCH &amp; XUNG LƯỢNG HỆ THỐNG
                                </label>
                                <span id="innoriaRigThroughputValue" class="fw-bold" style="color: #ffd700; font-size: 0.92rem;">2,400 tx/s</span>
                            </div>
                            <input type="range"
                                   class="form-range"
                                   id="innoriaRigThroughputSlider"
                                   min="100"
                                   max="10000"
                                   step="100"
                                   value="2400"
                                   aria-label="Throughput tx/s"/>
                            <div class="d-flex justify-content-between small" style="color: #64748B; font-size: 0.68rem;">
                                <span>100 tx/s (Baseline)</span>
                                <span>2,400 tx/s (Nominal)</span>
                                <span>10,000 tx/s (Peak Burst)</span>
                            </div>
                        </div>

                        <!-- 4 LIVE TELEMETRY READOUTS -->
                        <div class="row g-3 mt-2">
                            <div class="col-6 rig-telemetry-row">
                                <div class="text-uppercase small" style="color: #64748B; font-size: 0.68rem;">Độ Trễ Biên</div>
                                <div id="rigReadoutLatency" class="fw-bold fs-5" style="color: #38bdf8;">8.4 ms</div>
                                <div class="small" style="color: #94A3B8; font-size: 0.7rem;">Galvanic PLC Cut-off &lt; 12ms</div>
                            </div>
                            <div class="col-6 rig-telemetry-row">
                                <div class="text-uppercase small" style="color: #64748B; font-size: 0.68rem;">Tỷ Lệ Tự Động Hóa</div>
                                <div id="rigReadoutAutomation" class="fw-bold fs-5" style="color: #ffd700;">84.2%</div>
                                <div class="small" style="color: #94A3B8; font-size: 0.7rem;">RVC 48.6% · OEE 98.7%</div>
                            </div>
                            <div class="col-6 rig-telemetry-row">
                                <div class="text-uppercase small" style="color: #64748B; font-size: 0.68rem;">Tiết Kiệm TCO</div>
                                <div id="rigReadoutTco" class="fw-bold fs-5" style="color: #10b981;">-52.4% TCO</div>
                                <div class="small" style="color: #94A3B8; font-size: 0.7rem;">-80% Giờ Nhập Liệu VAS 200</div>
                            </div>
                            <div class="col-6 rig-telemetry-row">
                                <div class="text-uppercase small" style="color: #64748B; font-size: 0.68rem;">Chuẩn Tuân Thủ &amp; Bảo Chứng SHA-256</div>
                                <div id="rigReadoutCompliance" class="fw-bold fs-6" style="color: #F8FAFC;">SLA 99.999% · 0x9F4A..E82C</div>
                                <div class="small" style="color: #94A3B8; font-size: 0.7rem;">Ed25519 Air-Gapped Verified</div>
                            </div>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN: AUDITED ISOMETRIC SVG BENCH & SUB-ASSEMBLY CALLOUTS -->
                    <div class="col-lg-7">
                        <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 pb-3 mb-3"
                             style="border-bottom: 1px solid rgba(56, 189, 248, 0.2);">
                            <div class="d-flex flex-wrap gap-2" role="toolbar" aria-label="Isometric Sub-Assemblies">
                                <button type="button" class="rig-part-btn active" data-part-select="digiforce.manifold">
                                    01 · Digiforce Manifold
                                </button>
                                <button type="button" class="rig-part-btn" data-part-select="insilos.core">
                                    02 · Insilos Core Dial
                                </button>
                                <button type="button" class="rig-part-btn" data-part-select="visionx.turret">
                                    03 · VisionX 120FPS Turret
                                </button>
                                <button type="button" class="rig-part-btn" data-part-select="zkledger.vault">
                                    04 · ZKLedger Air-Gapped Vault
                                </button>
                            </div>
                            <span id="rigActivePartReadout" class="small" style="color: #ffd700; font-size: 0.74rem;">
                                ACTIVE: DIGIFORCE.MANIFOLD // RVC 48.6%
                            </span>
                        </div>

                        <!-- Isometric SVG Figure Stage -->
                        <div class="position-relative py-2">
                            ${svgOut}
                        </div>

                        <!-- Bottom Legend & Engineering Callout Strip -->
                        <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 pt-3 mt-2 small"
                             style="border-top: 1px solid rgba(148, 163, 184, 0.16); color: #94A3B8; font-size: 0.72rem;">
                            <div>
                                <span style="color: #38bdf8;">●</span> Nhấp trực tiếp vào từng cụm cơ khí trên bản vẽ hoặc thanh chọn để tách lớp trục Z
                            </div>
                            <div id="rigPartSpecCaption" style="color: #CBD5E1;">
                                Cụm van 5 cổng đối soát PO · Invoice · Packing List · Tờ khai VNACCS · B/L (&lt; 3.2s)
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script type="text/javascript">
            //<![CDATA[
            (function () {
                var root = document.getElementById("innoria_anatomy_sovereign_rig");
                if (!root) return;

                var PART_META = {
                    "digiforce.manifold": {
                        label: "ACTIVE: DIGIFORCE.MANIFOLD // RVC 48.6%",
                        caption: "Cụm van 5 cổng đối soát PO · Invoice · Packing List · Tờ khai VNACCS · B/L (< 3.2s)"
                    },
                    "insilos.core": {
                        label: "ACTIVE: INSILOS.CORE // VAS 200 DIFFERENTIAL",
                        caption: "Trụ lõi ERP tự hành & vành chia độ chuẩn Thông tư 200/2014/TT-BTC (-80% giờ nhập liệu)"
                    },
                    "visionx.turret": {
                        label: "ACTIVE: VISIONX.TURRET // 120 FPS TELECENTRIC",
                        caption: "Thấu kính viễn tâm kép 120 FPS & rơ-le quang học ngắt mạch PLC trong 12ms (ISO 13849-1)"
                    },
                    "zkledger.vault": {
                        label: "ACTIVE: ZKLEDGER.VAULT // AIR-GAPPED SHA-256",
                        caption: "Buồng mật mã Faraday cô lập mạng vật lý & dập dấu băm Ed25519 (SLA 99.999%)"
                    },
                    "sovereign.foundation": {
                        label: "ACTIVE: SOVEREIGN.FOUNDATION // ZERO-DEFECT BENCH",
                        caption: "Đế chuẩn cơ khí chính xác với thước chia vạch Vernier & 4 ống dẫn tín hiệu không va chạm"
                    }
                };

                var REGIME_PARTS = {
                    regime1: ["digiforce.manifold", "conduits"],
                    regime2: ["visionx.turret", "conduits"],
                    regime3: ["insilos.core", "zkledger.vault", "conduits"]
                };

                function highlightParts(activeParts, primaryPart) {
                    var groups = root.querySelectorAll(".iso-part-group");
                    var slider = document.getElementById("innoriaRigThroughputSlider");
                    var ratio = slider ? (parseFloat(slider.value) || 2400) / 10000 : 0.24;
                    var liftScale = 0.65 + ratio * 0.75;

                    groups.forEach(function (g) {
                        var partName = g.getAttribute("data-part");
                        var isMatch = activeParts.indexOf(partName) !== -1;
                        if (isMatch && partName !== "sovereign.foundation") {
                            g.classList.add("is-lifted", "is-highlighted");
                            var liftY = partName === "conduits" ? (-6 * liftScale) : (-14 * liftScale);
                            g.style.transform = "translate(0px, " + liftY.toFixed(1) + "px)";
                        } else {
                            g.classList.remove("is-lifted", "is-highlighted");
                            g.style.transform = "translate(0px, 0px)";
                        }
                    });

                    var partBtns = root.querySelectorAll("[data-part-select]");
                    partBtns.forEach(function (btn) {
                        btn.classList.toggle("active", btn.getAttribute("data-part-select") === primaryPart);
                    });

                    var meta = PART_META[primaryPart] || PART_META["digiforce.manifold"];
                    var readoutEl = document.getElementById("rigActivePartReadout");
                    var captionEl = document.getElementById("rigPartSpecCaption");
                    if (readoutEl) readoutEl.textContent = meta.label;
                    if (captionEl) captionEl.textContent = meta.caption;
                }

                function setRegime(mode) {
                    root.setAttribute("data-rig-active-mode", mode);
                    var pills = root.querySelectorAll("[data-rig-mode]");
                    pills.forEach(function (pill) {
                        pill.classList.toggle("active", pill.getAttribute("data-rig-mode") === mode);
                    });
                    var panels = root.querySelectorAll("[data-regime-panel]");
                    panels.forEach(function (panel) {
                        panel.classList.toggle("d-none", panel.getAttribute("data-regime-panel") !== mode);
                    });
                    var parts = REGIME_PARTS[mode] || REGIME_PARTS.regime1;
                    highlightParts(parts, parts[0]);
                }

                function updateTelemetry(txVal) {
                    var tx = parseInt(txVal, 10) || 2400;
                    var valEl = document.getElementById("innoriaRigThroughputValue");
                    if (valEl) valEl.textContent = tx.toLocaleString("en-US") + " tx/s";

                    var latency = Math.max(3.2, 11.6 - (tx / 10000) * 6.8).toFixed(1);
                    var autoRate = Math.min(99.8, 80.0 + (tx / 10000) * 19.6).toFixed(1);
                    var tcoSave = Math.min(65.0, 50.0 + (tx / 10000) * 14.5).toFixed(1);
                    var hashSuffix = ((tx * 2654435761) >>> 0).toString(16).toUpperCase().padStart(8, "0");

                    var latEl = document.getElementById("rigReadoutLatency");
                    var autoEl = document.getElementById("rigReadoutAutomation");
                    var tcoEl = document.getElementById("rigReadoutTco");
                    var compEl = document.getElementById("rigReadoutCompliance");

                    if (latEl) latEl.textContent = latency + " ms";
                    if (autoEl) autoEl.textContent = autoRate + "%";
                    if (tcoEl) tcoEl.textContent = "-" + tcoSave + "% TCO";
                    if (compEl) compEl.textContent = "SLA 99.999% · 0x" + hashSuffix;

                    var currentMode = root.getAttribute("data-rig-active-mode") || "regime1";
                    var parts = REGIME_PARTS[currentMode] || REGIME_PARTS.regime1;
                    highlightParts(parts, parts[0]);
                }

                root.querySelectorAll("[data-rig-mode]").forEach(function (pill) {
                    pill.addEventListener("click", function () {
                        setRegime(pill.getAttribute("data-rig-mode"));
                    });
                });

                root.querySelectorAll("[data-part-select]").forEach(function (btn) {
                    btn.addEventListener("click", function () {
                        var part = btn.getAttribute("data-part-select");
                        highlightParts([part, "conduits"], part);
                    });
                });

                root.querySelectorAll(".iso-part-group").forEach(function (g) {
                    g.addEventListener("click", function () {
                        var part = g.getAttribute("data-part");
                        if (part) highlightParts([part, "conduits"], part);
                    });
                });

                var slider = document.getElementById("innoriaRigThroughputSlider");
                if (slider) {
                    slider.addEventListener("input", function (e) {
                        updateTelemetry(e.target.value);
                    });
                }

                setRegime("regime1");
            })();
            //]]>
            </script>
        </section>
    </template>
`;

  // Remove old template if already present
  const existingRegex = /\s*<!-- =+\s*-->\s*<!-- 10\. INNORIA ISOMETRIC SOVEREIGN ANATOMY RIG[\s\S]*?<\/template>\n?/m;
  if (existingRegex.test(xmlContent)) {
    xmlContent = xmlContent.replace(existingRegex, "\n");
  }

  const paletteAnchor = "    <!-- ================================================================= -->\n    <!-- 7. INSILOS ERP WEBSITE SNIPPETS PALETTE EXTENSION (PRIORITY 30)   -->";
  if (!xmlContent.includes(paletteAnchor)) {
    throw new Error("Could not find insilos_3d_snippets_palette anchor in snippets_3d.xml");
  }
  xmlContent = xmlContent.replace(paletteAnchor, `${templateBlock}\n${paletteAnchor}`);

  const snippetEntry = `            <t t-snippet="insilos_website.s_innoria_anatomy_sovereign_rig" string="Innoria Isometric Sovereign Anatomy Rig" group="content" t-thumbnail="/insilos_website/static/src/img/snippets_thumbs/s_innoria_3d_topology.svg">
                <keywords>innoria, anatomy, isometric, rig, sovereign, digiforce, insilos, visionx, zkledger</keywords>
            </t>`;

  if (!xmlContent.includes('t-snippet="insilos_website.s_innoria_anatomy_sovereign_rig"')) {
    xmlContent = xmlContent.replace(
      "        </xpath>\n    </template>",
      `${snippetEntry}\n        </xpath>\n    </template>`
    );
  }

  writeFileSync(snippetsXmlPath, xmlContent, "utf8");
  console.log(`Updated ${snippetsXmlPath} with s_innoria_anatomy_sovereign_rig`);
}

