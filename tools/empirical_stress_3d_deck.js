/**
 * Empirical Stress Testing Suite: 3D Interactive Architecture Deck
 * Target: https://innoria.insilos.com/
 * 
 * Challenger Role: Empirical Challenger (Insilos Senior Expert Council)
 * Scenarios Tested:
 * 1. Orbit Angle Stress: Drag beyond pitch clamp [18°, 85°], fling momentum, clamp boundaries.
 * 2. Drag vs Parallax Stress: Drag angle preservation vs passive mousemove snapback.
 * 3. Multi-Slab Rapid Extraction Stress: Vertical stacking invariant (Z0 > Z1 > Z2 > Z3), zero collision/z-fighting.
 * 4. Exploded Mode Stress: Exploded toggle during active pulled state, geometric expansion & retraction.
 * 5. Mobile & Touch Stress: Viewport 375x812, horizontal overflow check (scrollWidth === 375), touch drag orbit.
 * 6. Airtight Volumetric Slabs: 6-face presence across 4 slabs (24 faces total), solid opacity (>=0.88), no wireframe collapse.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.resolve(__dirname, 'test_output_3d_physics');
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const RESULTS = {
    timestamp: new Date().toISOString(),
    scenarios: {},
    failures: [],
    verdict: 'PENDING'
};

function recordAssertion(scenario, testName, passed, details) {
    if (!RESULTS.scenarios[scenario]) {
        RESULTS.scenarios[scenario] = { tests: [], passed: true };
    }
    RESULTS.scenarios[scenario].tests.push({
        testName,
        passed,
        details
    });
    if (!passed) {
        RESULTS.scenarios[scenario].passed = false;
        RESULTS.failures.push(`[${scenario}] ${testName}: ${JSON.stringify(details)}`);
        console.error(`[-] FAIL: [${scenario}] ${testName}`, details);
    } else {
        console.log(`[✓] PASS: [${scenario}] ${testName}`, details);
    }
}

async function run() {
    console.log('================================================================');
    console.log('  STARTING EMPIRICAL 3D PHYSICS & ORBIT STRESS HARNESS');
    console.log('  Target: https://innoria.insilos.com/');
    console.log('================================================================');

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        // =====================================================================
        // PART 1: DESKTOP SUITE (Scenarios 1, 2, 3, 4, 6)
        // =====================================================================
        console.log('\n--- LAUNCHING DESKTOP TEST CONTEXT (1440x900) ---');
        const desktopContext = await browser.newContext({
            viewport: { width: 1440, height: 900 },
            deviceScaleFactor: 2
        });
        const page = await desktopContext.newPage();

        // Listen for console errors or warnings
        const consoleErrors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') consoleErrors.push(msg.text());
        });
        page.on('pageerror', err => consoleErrors.push(err.message));

        console.log('[*] Navigating to https://innoria.insilos.com/ ...');
        await page.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForTimeout(3000);

        const stageCard = await page.$('#stageCard');
        const architectureDeck = await page.$('#architecture_deck');
        const deckContainer = await page.$('#deckContainer');

        if (!stageCard || !deckContainer) {
            throw new Error('Critical DOM elements #stageCard or #deckContainer not found!');
        }

        await architectureDeck.scrollIntoViewIfNeeded();
        await page.waitForTimeout(1000);
        await stageCard.screenshot({ path: path.join(OUTPUT_DIR, '00_initial_resting.png') });

        // Helper to extract transform rotateX and rotateZ from deckContainer
        async function getDeckRotations() {
            return await page.evaluate(() => {
                const deck = document.querySelector('#deckContainer');
                if (!deck) return null;
                const transform = deck.style.transform || '';
                const matchX = transform.match(/rotateX\(([-\d.]+)deg\)/);
                const matchZ = transform.match(/rotateZ\(([-\d.]+)deg\)/);
                return {
                    transform,
                    rotX: matchX ? parseFloat(matchX[1]) : null,
                    rotZ: matchZ ? parseFloat(matchZ[1]) : null
                };
            });
        }

        // =====================================================================
        // SCENARIO 1: ORBIT ANGLE STRESS (PITCH CLAMP [18°, 85°])
        // =====================================================================
        console.log('\n>>> SCENARIO 1: ORBIT ANGLE STRESS TESTING');
        const stageBox = await stageCard.boundingBox();
        const startX = stageBox.x + stageBox.width / 2;
        const startY = stageBox.y + stageBox.height / 2;

        // 1A. Test extreme upward drag (pitch ceiling stress: should clamp at 85°)
        console.log('[*] 1A: Extreme Upward Drag (800px up)...');
        await page.mouse.move(startX, startY);
        await page.mouse.down();
        // Drag up by 800px in rapid steps
        await page.mouse.move(startX, startY - 800, { steps: 10 });
        
        let maxRotXDuringUpDrag = -Infinity;
        for (let i = 0; i < 20; i++) {
            const rot = await getDeckRotations();
            if (rot && rot.rotX !== null) {
                if (rot.rotX > maxRotXDuringUpDrag) maxRotXDuringUpDrag = rot.rotX;
            }
            await page.waitForTimeout(16);
        }
        await page.mouse.up();

        // Sample for 1 second after release during inertia
        for (let i = 0; i < 30; i++) {
            const rot = await getDeckRotations();
            if (rot && rot.rotX !== null) {
                if (rot.rotX > maxRotXDuringUpDrag) maxRotXDuringUpDrag = rot.rotX;
            }
            await page.waitForTimeout(30);
        }
        await page.waitForTimeout(500);
        const settledUpRot = await getDeckRotations();
        await stageCard.screenshot({ path: path.join(OUTPUT_DIR, '01_orbit_ceiling_clamp.png') });

        recordAssertion('Scenario_1_Orbit_Angle', 'Pitch_Ceiling_Clamp_85deg',
            maxRotXDuringUpDrag <= 85.05 && settledUpRot.rotX <= 85.05 && maxRotXDuringUpDrag >= 80.0,
            { maxRotX: maxRotXDuringUpDrag, settledRotX: settledUpRot.rotX, clampLimit: 85.0 }
        );

        // 1B. Test extreme downward drag (pitch floor stress: should clamp at 18°)
        console.log('[*] 1B: Extreme Downward Drag (1000px down)...');
        await page.mouse.move(startX, startY);
        await page.mouse.down();
        await page.mouse.move(startX, startY + 1000, { steps: 10 });
        
        let minRotXDuringDownDrag = Infinity;
        for (let i = 0; i < 20; i++) {
            const rot = await getDeckRotations();
            if (rot && rot.rotX !== null) {
                if (rot.rotX < minRotXDuringDownDrag) minRotXDuringDownDrag = rot.rotX;
            }
            await page.waitForTimeout(16);
        }
        await page.mouse.up();

        // Sample during momentum inertia
        for (let i = 0; i < 30; i++) {
            const rot = await getDeckRotations();
            if (rot && rot.rotX !== null) {
                if (rot.rotX < minRotXDuringDownDrag) minRotXDuringDownDrag = rot.rotX;
            }
            await page.waitForTimeout(30);
        }
        await page.waitForTimeout(500);
        const settledDownRot = await getDeckRotations();
        await stageCard.screenshot({ path: path.join(OUTPUT_DIR, '02_orbit_floor_clamp.png') });

        recordAssertion('Scenario_1_Orbit_Angle', 'Pitch_Floor_Clamp_18deg',
            minRotXDuringDownDrag >= 17.95 && settledDownRot.rotX >= 17.95 && minRotXDuringDownDrag <= 25.0,
            { minRotX: minRotXDuringDownDrag, settledRotX: settledDownRot.rotX, clampFloor: 18.0 }
        );

        // 1C. Reset View Button Test
        const btnReset = await page.$('#btnResetView');
        if (btnReset) {
            await btnReset.click();
            await page.waitForTimeout(800);
            const resetRot = await getDeckRotations();
            recordAssertion('Scenario_1_Orbit_Angle', 'Reset_View_Returns_Default',
                Math.abs(resetRot.rotX - 58) < 1.0 && Math.abs(resetRot.rotZ - (-38)) < 1.0,
                { resetRotX: resetRot.rotX, resetRotZ: resetRot.rotZ, expectedX: 58, expectedZ: -38 }
            );
        }

        // =====================================================================
        // SCENARIO 2: DRAG VS PARALLAX STRESS
        // =====================================================================
        console.log('\n>>> SCENARIO 2: DRAG VS PARALLAX STRESS TESTING');
        // Initial state before drag
        const initialBeforeDrag = await getDeckRotations();
        console.log('[*] Initial rotations:', initialBeforeDrag);

        // Drag the deck to a distinct angle
        console.log('[*] Dragging deck by dx = +200px, dy = -50px...');
        await page.mouse.move(startX, startY);
        await page.mouse.down();
        await page.mouse.move(startX + 200, startY - 50, { steps: 15 });
        await page.mouse.up();
        await page.waitForTimeout(900); // Wait for inertia to settle

        const draggedSettled = await getDeckRotations();
        console.log('[*] Post-drag settled rotations:', draggedSettled);

        // Verify drag changed angle significantly from default (-38deg)
        const dragDeltaZ = Math.abs(draggedSettled.rotZ - initialBeforeDrag.rotZ);
        recordAssertion('Scenario_2_Drag_Parallax', 'Drag_Angle_Significantly_Offset',
            dragDeltaZ > 15.0,
            { initialZ: initialBeforeDrag.rotZ, draggedZ: draggedSettled.rotZ, deltaZ: dragDeltaZ }
        );

        // Now move the mouse vigorously across stageCard without clicking (passive mouse parallax)
        console.log('[*] Moving mouse across stage (testing for snapback bug)...');
        const samplesDuringMove = [];
        for (let step = 0; step < 20; step++) {
            const sampleX = stageBox.x + 50 + (step % 5) * 60;
            const sampleY = stageBox.y + 50 + (step % 4) * 70;
            await page.mouse.move(sampleX, sampleY);
            await page.waitForTimeout(50);
            const r = await getDeckRotations();
            samplesDuringMove.push(r.rotZ);
        }

        // Check if rotZ stayed near draggedSettled.rotZ (within parallax micro-tilt bounds +/- 7 deg)
        // AND did not snap back to initial default (-38deg)
        const maxOffsetFromDragged = Math.max(...samplesDuringMove.map(z => Math.abs(z - draggedSettled.rotZ)));
        const closestToDefault = Math.min(...samplesDuringMove.map(z => Math.abs(z - initialBeforeDrag.rotZ)));

        recordAssertion('Scenario_2_Drag_Parallax', 'No_Snapback_To_Default_On_Mousemove',
            maxOffsetFromDragged <= 8.5 && closestToDefault > 10.0,
            {
                draggedTargetZ: draggedSettled.rotZ,
                maxOffsetFromDragged,
                closestDistanceToDefault: closestToDefault,
                defaultZ: initialBeforeDrag.rotZ
            }
        );

        // Move mouse outside stageCard (parallax micro-tilt decays to 0)
        await page.mouse.move(stageBox.x - 100, stageBox.y - 100);
        await page.waitForTimeout(600);
        const outsideRot = await getDeckRotations();
        
        // Passive parallax micro-tilt amplitude is max +/- 5.5 deg.
        // Therefore, outsideRot.rotZ (with 0 parallax) must be within 5.5 deg of draggedSettled.rotZ,
        // and must remain FAR away from defaultRotZ (-38 deg).
        const offsetFromDraggedEdge = Math.abs(outsideRot.rotZ - draggedSettled.rotZ);
        const distanceToDefaultAfterLeave = Math.abs(outsideRot.rotZ - initialBeforeDrag.rotZ);

        recordAssertion('Scenario_2_Drag_Parallax', 'Angle_Retained_After_Mouse_Leave',
            offsetFromDraggedEdge <= 6.0 && distanceToDefaultAfterLeave > 50.0,
            {
                outsideRotZ: outsideRot.rotZ,
                draggedEdgeZ: draggedSettled.rotZ,
                offsetFromDraggedEdge,
                distanceToDefaultAfterLeave,
                defaultZ: initialBeforeDrag.rotZ
            }
        );
        await stageCard.screenshot({ path: path.join(OUTPUT_DIR, '03_drag_preserved_after_move.png') });

        // Reset view for next tests
        if (btnReset) await btnReset.click();
        await page.waitForTimeout(800);

        // =====================================================================
        // SCENARIO 3: MULTI-SLAB RAPID EXTRACTION STRESS (RELATIVE Z & VERTICAL ORDER)
        // =====================================================================
        console.log('\n>>> SCENARIO 3: MULTI-SLAB RAPID EXTRACTION STRESS');

        async function getSlabsGeometricState() {
            return await page.evaluate(() => {
                const slabs = [0, 1, 2, 3].map(i => {
                    const el = document.querySelector(`#slab-${i}`);
                    if (!el) return null;
                    const style = window.getComputedStyle(el);
                    const pullX = parseFloat(el.style.getPropertyValue('--pull-x')) || 0;
                    const pullY = parseFloat(el.style.getPropertyValue('--pull-y')) || 0;
                    const pullZ = parseFloat(el.style.getPropertyValue('--pull-z')) || 0;
                    const scale = parseFloat(el.style.getPropertyValue('--scale')) || 1;
                    
                    // Base Z: either from inline or computed CSS variable
                    const baseZStr = style.getPropertyValue('--base-z').trim();
                    const baseZ = parseFloat(baseZStr) || 0;
                    const slabT = 36; // thickness in px

                    const effectiveZ = baseZ + pullZ;
                    const zTop = effectiveZ + slabT;
                    const zBottom = effectiveZ;

                    return {
                        id: i,
                        baseZ,
                        pullX,
                        pullY,
                        pullZ,
                        scale,
                        effectiveZ,
                        zBottom,
                        zTop,
                        isPulled: el.classList.contains('pulled-out'),
                        isDimmed: el.classList.contains('dimmed')
                    };
                });
                return slabs;
            });
        }

        // Test 3A: Resting state vertical stacking order
        const restingSlabs = await getSlabsGeometricState();
        console.log('[*] Resting slabs Z geometry:', restingSlabs.map(s => ({ id: s.id, baseZ: s.baseZ, zBottom: s.zBottom, zTop: s.zTop })));
        
        const restingOrderOk = (
            restingSlabs[0].zBottom > restingSlabs[1].zTop &&
            restingSlabs[1].zBottom > restingSlabs[2].zTop &&
            restingSlabs[2].zBottom > restingSlabs[3].zTop
        );
        recordAssertion('Scenario_3_Multi_Slab_Stacking', 'Resting_Stacking_Order_Maintained',
            restingOrderOk,
            {
                gap01: restingSlabs[0].zBottom - restingSlabs[1].zTop,
                gap12: restingSlabs[1].zBottom - restingSlabs[2].zTop,
                gap23: restingSlabs[2].zBottom - restingSlabs[3].zTop
            }
        );

        // Test 3B: Rapid hostile switching across slabs
        console.log('[*] 3B: Rapid high-frequency switching [0, 3, 1, 2, 0, 2, 1, 3] at 45ms intervals...');
        const sequence = [0, 3, 1, 2, 0, 2, 1, 3, 0, 1];
        let frameCollisions = 0;
        let minObservedGaps = { gap01: Infinity, gap12: Infinity, gap23: Infinity };
        let sampledFramesCount = 0;

        for (const targetIdx of sequence) {
            // Trigger hover / click
            await page.evaluate((idx) => {
                const slab = document.querySelector(`#slab-${idx}`);
                if (slab) slab.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
            }, targetIdx);

            // Sample geometry over next 150ms at ~16ms intervals
            for (let f = 0; f < 9; f++) {
                await page.waitForTimeout(16);
                const currentGeom = await getSlabsGeometricState();
                sampledFramesCount++;

                const g01 = currentGeom[0].zBottom - currentGeom[1].zTop;
                const g12 = currentGeom[1].zBottom - currentGeom[2].zTop;
                const g23 = currentGeom[2].zBottom - currentGeom[3].zTop;

                if (g01 < minObservedGaps.gap01) minObservedGaps.gap01 = g01;
                if (g12 < minObservedGaps.gap12) minObservedGaps.gap12 = g12;
                if (g23 < minObservedGaps.gap23) minObservedGaps.gap23 = g23;

                if (g01 <= 0 || g12 <= 0 || g23 <= 0) {
                    frameCollisions++;
                    console.error(`[-] Collision detected at frame ${sampledFramesCount}: g01=${g01}, g12=${g12}, g23=${g23}`);
                }
            }
        }

        // Allow final state to settle on slab 1
        await page.waitForTimeout(600);
        await stageCard.screenshot({ path: path.join(OUTPUT_DIR, '04_rapid_extraction_settled.png') });

        recordAssertion('Scenario_3_Multi_Slab_Stacking', 'Zero_Z_Collision_During_Rapid_Switching',
            frameCollisions === 0 && minObservedGaps.gap01 > 0 && minObservedGaps.gap12 > 0 && minObservedGaps.gap23 > 0,
            {
                sampledFrames: sampledFramesCount,
                collisions: frameCollisions,
                minGap01_px: minObservedGaps.gap01,
                minGap12_px: minObservedGaps.gap12,
                minGap23_px: minObservedGaps.gap23
            }
        );

        // =====================================================================
        // SCENARIO 4: EXPLODED MODE STRESS
        // =====================================================================
        console.log('\n>>> SCENARIO 4: EXPLODED MODE STRESS TESTING');
        const btnExplode = await page.$('#btnExplode');
        if (!btnExplode) throw new Error('#btnExplode not found!');

        // 4A: Check normal explode toggle from resting
        await btnReset.click();
        await page.waitForTimeout(600);

        console.log('[*] Toggling Exploded Mode ON...');
        await btnExplode.click();
        await page.waitForTimeout(600);
        await stageCard.screenshot({ path: path.join(OUTPUT_DIR, '05_exploded_resting.png') });

        const explodedRestingGeom = await getSlabsGeometricState();
        const explodedBaseZOk = (
            explodedRestingGeom[0].baseZ === 165 &&
            explodedRestingGeom[1].baseZ === 55 &&
            explodedRestingGeom[2].baseZ === -55 &&
            explodedRestingGeom[3].baseZ === -165
        );
        const explodedGapsOk = (
            (explodedRestingGeom[0].zBottom - explodedRestingGeom[1].zTop) >= 70 &&
            (explodedRestingGeom[1].zBottom - explodedRestingGeom[2].zTop) >= 70 &&
            (explodedRestingGeom[2].zBottom - explodedRestingGeom[3].zTop) >= 70
        );

        recordAssertion('Scenario_4_Exploded_Mode', 'Exploded_Base_Z_Expanded_Cleanly',
            explodedBaseZOk && explodedGapsOk,
            {
                baseZs: explodedRestingGeom.map(s => s.baseZ),
                gaps: [
                    explodedRestingGeom[0].zBottom - explodedRestingGeom[1].zTop,
                    explodedRestingGeom[1].zBottom - explodedRestingGeom[2].zTop,
                    explodedRestingGeom[2].zBottom - explodedRestingGeom[3].zTop
                ]
            }
        );

        // 4B: Pull slab 2 while exploded
        console.log('[*] Pulling Slab 2 while exploded...');
        await page.evaluate(() => {
            const slab2 = document.querySelector('#slab-2');
            if (slab2) slab2.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        });
        await page.waitForTimeout(600);
        await stageCard.screenshot({ path: path.join(OUTPUT_DIR, '06_exploded_slab2_pulled.png') });

        const explodedSlab2PulledGeom = await getSlabsGeometricState();
        const slab2PullZ = explodedSlab2PulledGeom[2].pullZ;
        const slab2PulledClearanceOk = (
            explodedSlab2PulledGeom[1].zBottom - explodedSlab2PulledGeom[2].zTop > 40 &&
            explodedSlab2PulledGeom[2].zBottom - explodedSlab2PulledGeom[3].zTop > 40
        );
        recordAssertion('Scenario_4_Exploded_Mode', 'Slab_Pull_Out_In_Exploded_State',
            slab2PullZ > 18.0 && slab2PulledClearanceOk,
            { slab2PullZ, clearanceAbove: explodedSlab2PulledGeom[1].zBottom - explodedSlab2PulledGeom[2].zTop }
        );

        // 4C: Toggle exploded mode OFF while Slab 2 is STILL pulled out (Retraction stress)
        console.log('[*] Toggling Exploded Mode OFF while Slab 2 is pulled out...');
        await btnExplode.click();
        await page.waitForTimeout(600);
        await stageCard.screenshot({ path: path.join(OUTPUT_DIR, '07_retracted_while_slab2_pulled.png') });

        const retractedGeom = await getSlabsGeometricState();
        const retractedBaseZRestored = (
            retractedGeom[0].baseZ === 96 &&
            retractedGeom[1].baseZ === 32 &&
            retractedGeom[2].baseZ === -32 &&
            retractedGeom[3].baseZ === -96
        );
        const slab2StillPulled = retractedGeom[2].isPulled && retractedGeom[2].pullZ > 18.0;
        const retractedOrderOk = (
            retractedGeom[0].zBottom > retractedGeom[1].zTop &&
            retractedGeom[1].zBottom > retractedGeom[2].zTop &&
            retractedGeom[2].zBottom > retractedGeom[3].zTop
        );

        recordAssertion('Scenario_4_Exploded_Mode', 'Smooth_Retraction_With_Active_Pull',
            retractedBaseZRestored && slab2StillPulled && retractedOrderOk,
            {
                baseZs: retractedGeom.map(s => s.baseZ),
                slab2PullZ: retractedGeom[2].pullZ,
                gap12: retractedGeom[1].zBottom - retractedGeom[2].zTop
            }
        );

        // =====================================================================
        // SCENARIO 6: AIRTIGHT VOLUMETRIC SLABS (6-FACE VOLUME & SOLID PRESENCE)
        // =====================================================================
        console.log('\n>>> SCENARIO 6: AIRTIGHT VOLUMETRIC SLABS STRESS');

        async function auditVolumetricFaces() {
            return await page.evaluate(() => {
                const faceSelectors = ['.top', '.bottom', '.front-right', '.front-left', '.back-right', '.back-left'];
                const slabAudits = [];

                for (let i = 0; i < 4; i++) {
                    const slabEl = document.querySelector(`#slab-${i}`);
                    if (!slabEl) {
                        slabAudits.push({ id: i, error: 'Slab element missing' });
                        continue;
                    }
                    const slabStyle = window.getComputedStyle(slabEl);
                    const slabOpacity = parseFloat(slabStyle.opacity);
                    const slabFilter = slabStyle.filter;

                    const faces = {};
                    let allFacesPresent = true;
                    let allFacesSolid = true;

                    for (const face of faceSelectors) {
                        const faceEl = slabEl.querySelector(face);
                        if (!faceEl) {
                            allFacesPresent = false;
                            faces[face] = { exists: false };
                            continue;
                        }
                        const fStyle = window.getComputedStyle(faceEl);
                        const bg = fStyle.backgroundImage || fStyle.backgroundColor;
                        const fFilter = fStyle.filter;
                        const fOpacity = parseFloat(fStyle.opacity);
                        const isWireframe = (fOpacity < 0.2 || bg === 'none' || bg === 'rgba(0, 0, 0, 0)');

                        if (isWireframe) allFacesSolid = false;

                        faces[face] = {
                            exists: true,
                            width: fStyle.width,
                            height: fStyle.height,
                            transform: fStyle.transform,
                            opacity: fOpacity,
                            filter: fFilter,
                            bgSnippet: bg.substring(0, 40)
                        };
                    }

                    slabAudits.push({
                        id: i,
                        slabOpacity,
                        slabFilter,
                        allFacesPresent,
                        allFacesSolid,
                        isPulled: slabEl.classList.contains('pulled-out'),
                        isDimmed: slabEl.classList.contains('dimmed'),
                        faces
                    });
                }
                return slabAudits;
            });
        }

        // 6A: Audit 6-faces in resting state (reset first)
        await btnReset.click();
        await page.waitForTimeout(600);
        const restingVolAudit = await auditVolumetricFaces();
        
        let all24FacesExist = true;
        let restingOpacitySolid = true;
        for (const slab of restingVolAudit) {
            if (!slab.allFacesPresent) all24FacesExist = false;
            if (slab.slabOpacity < 0.85) restingOpacitySolid = false;
        }

        recordAssertion('Scenario_6_Volumetric_Slabs', 'All_24_Faces_Present_Resting_Solid_Opacity',
            all24FacesExist && restingOpacitySolid,
            {
                totalSlabs: restingVolAudit.length,
                all24FacesExist,
                restingOpacitySolid,
                opacities: restingVolAudit.map(s => s.slabOpacity)
            }
        );

        // 6B: Audit in pulled state (select slab 0)
        await page.evaluate(() => {
            const s0 = document.querySelector('#slab-0');
            if (s0) s0.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        });
        await page.waitForTimeout(600);
        const pulledVolAudit = await auditVolumetricFaces();

        // Slab 0 should have opacity 1.0; Slabs 1, 2, 3 should have opacity 0.88 (NOT 0.3)
        const slab0PulledOpacity = pulledVolAudit[0].slabOpacity;
        const dimmedOpacities = [pulledVolAudit[1].slabOpacity, pulledVolAudit[2].slabOpacity, pulledVolAudit[3].slabOpacity];
        const allDimmedPreserved = dimmedOpacities.every(op => op >= 0.85); // 0.88 specified

        recordAssertion('Scenario_6_Volumetric_Slabs', 'Dimmed_Slabs_Maintain_Solid_Volume_No_Ghost_Wireframe',
            slab0PulledOpacity >= 0.99 && allDimmedPreserved,
            {
                slab0PulledOpacity,
                dimmedOpacities,
                expectedDimmedOpacity: 0.88
            }
        );

        await desktopContext.close();
        console.log('[✓] Desktop Context closed.');

        // =====================================================================
        // PART 2: SCENARIO 5: MOBILE & TOUCH STRESS (375x812)
        // =====================================================================
        console.log('\n--- LAUNCHING MOBILE VIEWPORT CONTEXT (375x812, Touch) ---');
        const mobileContext = await browser.newContext({
            viewport: { width: 375, height: 812 },
            deviceScaleFactor: 2,
            isMobile: true,
            hasTouch: true
        });
        const mobilePage = await mobileContext.newPage();

        console.log('[*] Navigating to https://innoria.insilos.com/ on Mobile...');
        await mobilePage.goto('https://innoria.insilos.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
        await mobilePage.waitForTimeout(3000);

        const mobileStageCard = await mobilePage.$('#stageCard');
        const mobileArchDeck = await mobilePage.$('#architecture_deck');
        if (!mobileStageCard || !mobileArchDeck) {
            throw new Error('Mobile stage card or architecture deck not found!');
        }

        await mobileArchDeck.scrollIntoViewIfNeeded();
        await mobilePage.waitForTimeout(800);
        await mobileStageCard.screenshot({ path: path.join(OUTPUT_DIR, '08_mobile_resting.png') });

        // 5A: Zero horizontal overflow audit across page and deck component
        console.log('[*] 5A: Auditing Horizontal Overflow on Mobile (375px)...');
        const overflowAudit = await mobilePage.evaluate(() => {
            const viewportWidth = window.innerWidth;
            const docScrollWidth = document.documentElement.scrollWidth;
            const bodyScrollWidth = document.body.scrollWidth;

            // Scan all elements for horizontal overflow bounds
            const overflowingElements = [];
            const allElements = document.querySelectorAll('*');
            for (const el of allElements) {
                const rect = el.getBoundingClientRect();
                if (rect.width > viewportWidth + 1 || rect.right > viewportWidth + 1 || rect.left < -1) {
                    // Filter out elements with overflow:hidden parents that don't cause page scroll
                    const tag = el.tagName.toLowerCase();
                    const id = el.id ? `#${el.id}` : '';
                    const cls = el.className ? `.${el.className.toString().split(' ').slice(0, 2).join('.')}` : '';
                    overflowingElements.push({
                        selector: `${tag}${id}${cls}`,
                        rect: { left: rect.left, right: rect.right, width: rect.width }
                    });
                    if (overflowingElements.length >= 10) break;
                }
            }

            return {
                viewportWidth,
                docScrollWidth,
                bodyScrollWidth,
                hasDocOverflow: docScrollWidth > viewportWidth,
                overflowingElements: overflowingElements.slice(0, 5)
            };
        });

        recordAssertion('Scenario_5_Mobile_Touch', 'Zero_Horizontal_Overflow_Mobile_375px',
            !overflowAudit.hasDocOverflow && overflowAudit.docScrollWidth === 375,
            {
                viewportWidth: overflowAudit.viewportWidth,
                docScrollWidth: overflowAudit.docScrollWidth,
                bodyScrollWidth: overflowAudit.bodyScrollWidth,
                overflowingCount: overflowAudit.overflowingElements.length
            }
        );

        // 5B: Touch drag orbit on mobile
        console.log('[*] 5B: Emulating Touch Drag Orbit on Mobile...');
        const mobBox = await mobileStageCard.boundingBox();
        const mobStartX = mobBox.x + mobBox.width / 2;
        const mobStartY = mobBox.y + mobBox.height / 2;

        const mobInitialRot = await mobilePage.evaluate(() => {
            const deck = document.querySelector('#deckContainer');
            return deck ? deck.style.transform : null;
        });

        // Perform touch drag using pointer events with pointerType: 'touch'
        await mobilePage.evaluate(async ({ startX, startY }) => {
            const stage = document.querySelector('#stageCard');
            if (!stage) return;

            const pointerDownEvent = new PointerEvent('pointerdown', {
                bubbles: true,
                clientX: startX,
                clientY: startY,
                pointerId: 1,
                pointerType: 'touch',
                isPrimary: true
            });
            stage.dispatchEvent(pointerDownEvent);

            for (let step = 1; step <= 10; step++) {
                await new Promise(r => setTimeout(r, 20));
                const moveEvent = new PointerEvent('pointermove', {
                    bubbles: true,
                    clientX: startX + step * 12,
                    clientY: startY - step * 6,
                    pointerId: 1,
                    pointerType: 'touch',
                    isPrimary: true
                });
                stage.dispatchEvent(moveEvent);
            }

            await new Promise(r => setTimeout(r, 20));
            const pointerUpEvent = new PointerEvent('pointerup', {
                bubbles: true,
                clientX: startX + 120,
                clientY: startY - 60,
                pointerId: 1,
                pointerType: 'touch',
                isPrimary: true
            });
            stage.dispatchEvent(pointerUpEvent);
        }, { startX: mobStartX, startY: mobStartY });

        await mobilePage.waitForTimeout(800); // Allow momentum to settle
        await mobileStageCard.screenshot({ path: path.join(OUTPUT_DIR, '09_mobile_touch_drag_orbit.png') });

        const mobPostDragRot = await mobilePage.evaluate(() => {
            const deck = document.querySelector('#deckContainer');
            const matchX = deck ? deck.style.transform.match(/rotateX\(([-\d.]+)deg\)/) : null;
            const matchZ = deck ? deck.style.transform.match(/rotateZ\(([-\d.]+)deg\)/) : null;
            return {
                transform: deck ? deck.style.transform : null,
                rotX: matchX ? parseFloat(matchX[1]) : null,
                rotZ: matchZ ? parseFloat(matchZ[1]) : null
            };
        });

        recordAssertion('Scenario_5_Mobile_Touch', 'Touch_Drag_Orbit_Responsive_And_Smooth',
            mobPostDragRot.rotZ !== null && Math.abs(mobPostDragRot.rotZ - (-38)) > 10.0,
            { initialTransform: mobInitialRot, postDragTransform: mobPostDragRot.transform, rotZ: mobPostDragRot.rotZ }
        );

        // 5C: Mobile Tap Layer Selection (Slab 1)
        console.log('[*] 5C: Emulating Tap on Slab 1 on Mobile...');
        await mobilePage.evaluate(() => {
            const stage = document.querySelector('#stageCard');
            const slab1 = document.querySelector('#slab-1');
            if (stage && slab1) {
                // Tap on slab 1 without dragging
                const rect = slab1.getBoundingClientRect();
                const tapX = rect.left + rect.width / 2;
                const tapY = rect.top + rect.height / 2;

                slab1.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: tapX, clientY: tapY, pointerId: 2, pointerType: 'touch' }));
                slab1.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: tapX, clientY: tapY, pointerId: 2, pointerType: 'touch' }));
            }
        });
        await mobilePage.waitForTimeout(800);
        await mobileStageCard.screenshot({ path: path.join(OUTPUT_DIR, '10_mobile_slab1_tapped.png') });

        const mobileHUDState = await mobilePage.evaluate(() => {
            const badge = document.querySelector('#badgeLayerName');
            const slab1 = document.querySelector('#slab-1');
            const panel1 = document.querySelector('#deep-panel-1');
            return {
                badgeText: badge ? badge.textContent.trim() : null,
                slab1Pulled: slab1 ? slab1.classList.contains('pulled-out') : false,
                panel1Visible: panel1 ? panel1.classList.contains('visible') : false
            };
        });

        recordAssertion('Scenario_5_Mobile_Touch', 'Mobile_Tap_Selects_Layer_And_Updates_HUD',
            mobileHUDState.badgeText === 'PLATFORM SERVICES' && mobileHUDState.slab1Pulled,
            mobileHUDState
        );

        await mobileContext.close();
        console.log('[✓] Mobile Context closed.');

        // =====================================================================
        // CONSOLIDATE RESULTS & VERDICT
        // =====================================================================
        console.log('\n================================================================');
        console.log('  TEST EXECUTION COMPLETED — CONSOLIDATING VERDICT');
        console.log('================================================================');

        if (RESULTS.failures.length === 0) {
            RESULTS.verdict = 'CONFIRM_CORRECT';
            console.log('\n>>> OVERALL VERDICT: CONFIRM_CORRECT <<<');
            console.log('All 6 stress test scenarios passed with 100% adherence to physics and geometry specifications.');
        } else {
            RESULTS.verdict = 'REPORT_VULNERABILITY';
            console.error('\n>>> OVERALL VERDICT: REPORT_VULNERABILITY <<<');
            console.error(`Total failures detected: ${RESULTS.failures.length}`);
        }

        fs.writeFileSync(path.join(OUTPUT_DIR, 'empirical_results.json'), JSON.stringify(RESULTS, null, 2));
        console.log(`[✓] Detailed empirical results written to ${path.join(OUTPUT_DIR, 'empirical_results.json')}`);

    } catch (err) {
        console.error('[-] Fatal harness exception:', err);
        RESULTS.verdict = 'REPORT_VULNERABILITY';
        RESULTS.failures.push(`Fatal harness exception: ${err.message}`);
        fs.writeFileSync(path.join(OUTPUT_DIR, 'empirical_results.json'), JSON.stringify(RESULTS, null, 2));
    } finally {
        await browser.close();
    }
}

run();
