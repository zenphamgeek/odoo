const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

    // HTML test page with canvas
    const html = `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { background: #050a14; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: system-ui, -apple-system, sans-serif; }
            .card { width: 440px; background: radial-gradient(circle at 50% 40%, #0d1b30 0%, #050913 100%); border-radius: 16px; border: 1px solid rgba(0, 240, 255, 0.2); box-shadow: 0 20px 50px rgba(0,0,0,0.85), inset 0 0 35px rgba(15, 98, 254, 0.08); padding: 20px; color: white; position: relative; overflow: hidden; }
            canvas { width: 100%; height: 260px; display: block; cursor: grab; }
        </style>
    </head>
    <body>
        <div class="card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <span style="font-size: 11px; font-family: monospace; color: #00f0ff; letter-spacing: 0.08em; background: rgba(0, 240, 255, 0.1); padding: 3px 10px; border-radius: 12px; border: 1px solid rgba(0, 240, 255, 0.35); box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);">INSILOS SOVEREIGN // 3D DATABASE ENCLAVE</span>
                <span style="font-size: 11px; color: #42e6c3; font-family: monospace; font-weight: 600;">SYNC: &lt;0.8ms</span>
            </div>
            <canvas id="cv" width="400" height="260"></canvas>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 11px; color: rgba(255,255,255,0.7); font-family: monospace;">
                <span>KIẾN TRÚC DỮ LIỆU ĐỘC BẢN</span>
                <span style="color: #00f0ff; font-weight: 600;">ERP CORE ⇄ SOVEREIGN ⇄ AI</span>
            </div>
        </div>

        <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const width = canvas.width = 400;
        const height = canvas.height = 260;

        let rotX = 0.34, rotY = -0.32;
        let targetRotX = 0.34, targetRotY = -0.32;
        let time = 0;

        // 32 Quantum Ambient Particles in Insilos Cyan, Cobalt, and Mint
        const particles = [];
        const insilosColors = ['#00F0FF', '#0F62FE', '#42E6C3', '#38BDF8', '#FFFFFF'];
        for (let i = 0; i < 32; i++) {
            particles.push({
                x: (Math.random() - 0.5) * 280,
                y: (Math.random() - 0.5) * 160,
                z: (Math.random() - 0.5) * 140,
                size: Math.random() * 1.6 + 0.8,
                speedY: (Math.random() * 0.22 + 0.08),
                phase: Math.random() * Math.PI * 2,
                color: insilosColors[i % insilosColors.length]
            });
        }

        // SPATIAL 3D STAGGERED FORMATION (Sovereign Apex Triangle)
        // DB 1 (Foreground Left): ERP Core (z: +22, x: -74)
        // DB 2 (Elevated Center-Back Apex): Sovereign DB (z: -30, x: 0)
        // DB 3 (Foreground Right): AI & Analytics (z: +22, x: +74)
        const databases = [
            {
                id: 'db_erp',
                tag: 'ERP CORE',
                sub: 'DỮ LIỆU CỐT LÕI',
                kpi: 'IOPS: 150K',
                x: -74,
                z: 24, // Foreground Left
                rx: 21,
                rz: 12,
                yBottom: -26,
                yTop: 14,
                hudOffsetX: -6,
                hudOffsetY: 14,
                primaryColor: '#0F62FE',
                accentColor: '#38BDF8',
                lightColor: '#DBEAFE',
                shadowColor: '#041024',
                ledColor: '#00F0FF',
                glowColor: 'rgba(15, 98, 254, 0.45)'
            },
            {
                id: 'db_sovereign',
                tag: 'SOVEREIGN DB',
                sub: 'CƠ SỞ ĐỘC BẢN',
                kpi: 'LATENCY: <0.5ms',
                x: 0,
                z: -30, // Background Apex (recessed into depth, elevated crown)
                rx: 25,
                rz: 14.5,
                yBottom: -30,
                yTop: 26, // Elevated hero stature
                hudOffsetX: 0,
                hudOffsetY: 26, // Staggered crown
                primaryColor: '#00F0FF',
                accentColor: '#0284C7',
                lightColor: '#FFFFFF',
                shadowColor: '#031E36',
                ledColor: '#FFFFFF',
                glowColor: 'rgba(0, 240, 255, 0.55)'
            },
            {
                id: 'db_ai',
                tag: 'AI & ANALYTICS',
                sub: 'TRÍ TUỆ NHÂN TẠO',
                kpi: 'SYNC: REALTIME',
                x: 74,
                z: 24, // Foreground Right
                rx: 21,
                rz: 12,
                yBottom: -26,
                yTop: 14,
                hudOffsetX: 6,
                hudOffsetY: 14,
                primaryColor: '#42E6C3',
                accentColor: '#10B981',
                lightColor: '#ECFDF5',
                shadowColor: '#03261D',
                ledColor: '#42E6C3',
                glowColor: 'rgba(66, 230, 195, 0.45)'
            }
        ];

        // 3D Triangular Photonic Highway Mesh connecting the 3 databases
        const bridges = [
            { fromIdx: 0, toIdx: 1, color: '#00F0FF', glow: 'rgba(0, 240, 255, 0.45)' },
            { fromIdx: 1, toIdx: 2, color: '#42E6C3', glow: 'rgba(66, 230, 195, 0.45)' },
            { fromIdx: 0, toIdx: 2, color: '#0F62FE', glow: 'rgba(15, 98, 254, 0.35)' }
        ];

        function project(x, y, z, cosX, sinX, cosY, sinY, cx, cy, fov) {
            const x1 = x * cosY - z * sinY;
            const z1 = z * cosY + x * sinY;
            const y2 = y * cosX - z1 * sinX;
            const z2 = z1 * cosX + y * sinX + 270;
            const scale = fov / (z2 || 1);
            return {
                x: cx + x1 * scale,
                y: cy - y2 * scale,
                z: z2,
                scale: scale
            };
        }

        function renderFrame() {
            time += 0.02;
            rotX += (targetRotX - rotX) * 0.08;
            rotY += (targetRotY - rotY) * 0.08;
            rotY += 0.005; // auto orbit

            ctx.clearRect(0, 0, width, height);
            const cx = width / 2;
            const cy = height / 2 - 14;
            const fov = 270;

            const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
            const cosY = Math.cos(rotY), sinY = Math.sin(rotY);

            // 1. Cybernetic Ground Horizon & Compass Rings in Insilos Cyan & Cobalt
            const groundProj = project(0, -38, 0, cosX, sinX, cosY, sinY, cx, cy, fov);
            
            // Outer dashed compass ring
            ctx.save();
            ctx.beginPath();
            ctx.ellipse(groundProj.x, groundProj.y, 136 * groundProj.scale, 42 * groundProj.scale, 0, 0, Math.PI * 2);
            ctx.setLineDash([4, 6]);
            ctx.strokeStyle = 'rgba(0, 240, 255, 0.28)';
            ctx.lineWidth = 1;
            ctx.stroke();
            ctx.restore();

            // Inner solid glow ring in Insilos Blue & Cyan
            ctx.beginPath();
            ctx.ellipse(groundProj.x, groundProj.y, 82 * groundProj.scale, 26 * groundProj.scale, 0, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(15, 98, 254, 0.45)';
            ctx.lineWidth = 1.5;
            ctx.shadowColor = '#00F0FF';
            ctx.shadowBlur = 9;
            ctx.stroke();
            ctx.shadowBlur = 0;

            // 2. Ambient Particles
            particles.forEach(p => {
                p.y += p.speedY;
                if (p.y > 90) p.y = -90;
                const pr = project(p.x, p.y + Math.sin(time + p.phase) * 4, p.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                const alpha = Math.sin(time * 2 + p.phase) * 0.35 + 0.45;
                ctx.beginPath();
                ctx.arc(pr.x, pr.y, Math.max(0.6, p.size * pr.scale), 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.globalAlpha = Math.max(0, Math.min(1, alpha));
                ctx.shadowColor = p.color;
                ctx.shadowBlur = 6;
                ctx.fill();
            });
            ctx.globalAlpha = 1.0;
            ctx.shadowBlur = 0;

            // 3. Collect 3D Render Objects for Depth Sorting
            const items = [];

            // A. Data Highway Bridges
            bridges.forEach((b, bIdx) => {
                const dbA = databases[b.fromIdx];
                const dbB = databases[b.toIdx];
                const pA = project(dbA.x, (dbA.yBottom + dbA.yTop) * 0.4, dbA.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                const pB = project(dbB.x, (dbB.yBottom + dbB.yTop) * 0.4, dbB.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                items.push({
                    type: 'bridge',
                    bridge: b,
                    pA, pB,
                    z: (pA.z + pB.z) / 2
                });
            });

            // B. Database Monoliths
            databases.forEach((db, dIdx) => {
                const pMid = project(db.x, (db.yBottom + db.yTop) / 2, db.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                items.push({
                    type: 'cylinder',
                    db,
                    dIdx,
                    z: pMid.z
                });
            });

            // Sort back to front (highest Z to lowest Z)
            items.sort((a, b) => b.z - a.z);

            // 4. Render Sorted 3D Items
            items.forEach(item => {
                if (item.type === 'bridge') {
                    const pA = item.pA;
                    const pB = item.pB;

                    // Dual Laser Rails
                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo(pA.x, pA.y - 2);
                    ctx.lineTo(pB.x, pB.y - 2);
                    ctx.moveTo(pA.x, pA.y + 2);
                    ctx.lineTo(pB.x, pB.y + 2);
                    ctx.strokeStyle = item.bridge.color;
                    ctx.lineWidth = Math.max(1.1, 1.8 * pA.scale);
                    ctx.shadowColor = item.bridge.color;
                    ctx.shadowBlur = 8;
                    ctx.stroke();

                    // Translucent Optical Energy Ribbon
                    ctx.beginPath();
                    ctx.moveTo(pA.x, pA.y - 2);
                    ctx.lineTo(pB.x, pB.y - 2);
                    ctx.lineTo(pB.x, pB.y + 2);
                    ctx.lineTo(pA.x, pA.y + 2);
                    ctx.closePath();
                    ctx.fillStyle = item.bridge.glow;
                    ctx.fill();

                    // Luminous Flying Photon Data Packets
                    const packetCount = 3;
                    for (let k = 0; k < packetCount; k++) {
                        const prog = (time * 1.1 + k / packetCount) % 1;
                        const px = pA.x + (pB.x - pA.x) * prog;
                        const py = pA.y + (pB.y - pA.y) * prog;
                        const pz = pA.z + (pB.z - pA.z) * prog;
                        const pscale = fov / (pz || 1);

                        // Primary glowing packet
                        ctx.beginPath();
                        ctx.arc(px, py, Math.max(2.2, 3.8 * pscale), 0, Math.PI * 2);
                        ctx.fillStyle = k % 2 === 0 ? '#FFFFFF' : item.bridge.color;
                        ctx.shadowColor = item.bridge.color;
                        ctx.shadowBlur = 14;
                        ctx.fill();

                        // Trailing comet spark
                        ctx.beginPath();
                        ctx.moveTo(px, py);
                        const tailX = px - (pB.x - pA.x) * 0.1;
                        const tailY = py - (pB.y - pA.y) * 0.1;
                        ctx.lineTo(tailX, tailY);
                        ctx.strokeStyle = item.bridge.color;
                        ctx.lineWidth = 1.8 * pscale;
                        ctx.stroke();
                    }
                    ctx.restore();
                } else if (item.type === 'cylinder') {
                    const db = item.db;

                    // Projected center points at bottom and top of cylinder with 3D Z
                    const P_bot = project(db.x, db.yBottom, db.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                    const rx_bot = db.rx * P_bot.scale;
                    const ry_bot = db.rz * Math.abs(Math.sin(rotX)) * P_bot.scale;

                    const P_top = project(db.x, db.yTop, db.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                    const rx_top = db.rx * P_top.scale;
                    const ry_top = db.rz * Math.abs(Math.sin(rotX)) * P_top.scale;

                    // 1. Ambient Drop Shadow on ground
                    ctx.save();
                    ctx.beginPath();
                    ctx.ellipse(P_bot.x, P_bot.y + 2, rx_bot * 1.15, ry_bot * 1.15, 0, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(2, 6, 23, 0.65)';
                    ctx.shadowColor = db.primaryColor;
                    ctx.shadowBlur = 14;
                    ctx.fill();
                    ctx.restore();

                    // 2. Base Pedestal Foot Collar
                    const P_foot = project(db.x, db.yBottom - 5, db.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                    const rx_foot = db.rx * 1.08 * P_foot.scale;
                    const ry_foot = db.rz * 1.08 * Math.abs(Math.sin(rotX)) * P_foot.scale;
                    ctx.beginPath();
                    ctx.ellipse(P_foot.x, P_foot.y, rx_foot, ry_foot, 0, 0, Math.PI * 2);
                    ctx.fillStyle = '#040d1a';
                    ctx.strokeStyle = db.primaryColor;
                    ctx.lineWidth = 1;
                    ctx.fill();
                    ctx.stroke();

                    // 3. Volumetric Cylinder Body (Seamless Silhouette)
                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo(P_top.x - rx_top, P_top.y);
                    ctx.lineTo(P_bot.x - rx_bot, P_bot.y);
                    ctx.ellipse(P_bot.x, P_bot.y, rx_bot, ry_bot, 0, Math.PI, 0, true);
                    ctx.lineTo(P_top.x + rx_top, P_top.y);
                    ctx.ellipse(P_top.x, P_top.y, rx_top, ry_top, 0, 0, Math.PI, true);
                    ctx.closePath();

                    const bodyGrad = ctx.createLinearGradient(P_top.x - rx_top, P_top.y, P_top.x + rx_top, P_top.y);
                    bodyGrad.addColorStop(0.0, db.shadowColor);
                    bodyGrad.addColorStop(0.18, db.primaryColor);
                    bodyGrad.addColorStop(0.42, db.lightColor);
                    bodyGrad.addColorStop(0.70, db.accentColor);
                    bodyGrad.addColorStop(1.0, db.shadowColor);
                    ctx.fillStyle = bodyGrad;
                    ctx.fill();

                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                    ctx.restore();

                    // 4. Horizontal CNC Storage Drive Slots & LED Arrays
                    const slotFractions = [0.26, 0.50, 0.74];
                    slotFractions.forEach(function(frac, sIdx) {
                        const slotY = db.yBottom + (db.yTop - db.yBottom) * frac;
                        const P_slot = project(db.x, slotY, db.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                        const rx_slot = db.rx * P_slot.scale;
                        const ry_slot = db.rz * Math.abs(Math.sin(rotX)) * P_slot.scale;

                        // Dark recessed front groove
                        ctx.beginPath();
                        ctx.ellipse(P_slot.x, P_slot.y, rx_slot * 1.01, ry_slot * 1.01, 0, 0, Math.PI, false);
                        ctx.strokeStyle = 'rgba(2, 6, 23, 0.85)';
                        ctx.lineWidth = 2.4;
                        ctx.stroke();

                        // Glowing accent line directly beneath groove
                        ctx.beginPath();
                        ctx.ellipse(P_slot.x, P_slot.y + 0.8, rx_slot * 1.01, ry_slot * 1.01, 0, 0.1, Math.PI - 0.1, false);
                        ctx.strokeStyle = db.primaryColor;
                        ctx.lineWidth = 1.0;
                        ctx.shadowColor = db.primaryColor;
                        ctx.shadowBlur = 6;
                        ctx.stroke();
                        ctx.shadowBlur = 0;

                        // 3 Micro Status Indicator LEDs on each tier
                        for (let led = 0; led < 3; led++) {
                            const ledTh = Math.PI * 0.5 + (led - 1) * 0.32;
                            const ledX = P_slot.x + rx_slot * Math.cos(ledTh);
                            const ledY = P_slot.y + ry_slot * Math.sin(ledTh);
                            const isBlink = Math.sin(time * 5 + led * 1.8 + sIdx * 2.2) > -0.2;

                            ctx.beginPath();
                            ctx.arc(ledX, ledY, Math.max(1.1, 1.8 * P_slot.scale), 0, Math.PI * 2);
                            ctx.fillStyle = isBlink ? db.ledColor : 'rgba(255, 255, 255, 0.2)';
                            if (isBlink) {
                                ctx.shadowColor = db.ledColor;
                                ctx.shadowBlur = 6;
                            }
                            ctx.fill();
                            ctx.shadowBlur = 0;
                        }
                    });

                    // 5. Top Face Mirror Platter & Radial Specular Highlight
                    ctx.beginPath();
                    ctx.ellipse(P_top.x, P_top.y, rx_top, ry_top, 0, 0, Math.PI * 2);
                    const specX = P_top.x - rx_top * 0.22;
                    const specY = P_top.y - ry_top * 0.22;

                    const topGrad = ctx.createRadialGradient(
                        specX, specY, 1,
                        P_top.x, P_top.y, rx_top
                    );
                    topGrad.addColorStop(0, '#FFFFFF');
                    topGrad.addColorStop(0.28, db.lightColor);
                    topGrad.addColorStop(0.68, db.accentColor);
                    topGrad.addColorStop(1, db.primaryColor);

                    ctx.fillStyle = topGrad;
                    ctx.shadowColor = db.primaryColor;
                    ctx.shadowBlur = 10;
                    ctx.fill();
                    ctx.shadowBlur = 0;

                    // Concentric Circular Data Tracks on top disc
                    ctx.beginPath();
                    ctx.ellipse(P_top.x, P_top.y, rx_top * 0.72, ry_top * 0.72, 0, 0, Math.PI * 2);
                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
                    ctx.lineWidth = 0.8;
                    ctx.stroke();

                    ctx.beginPath();
                    ctx.ellipse(P_top.x, P_top.y, rx_top * 0.42, ry_top * 0.42, 0, 0, Math.PI * 2);
                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.55)';
                    ctx.lineWidth = 0.8;
                    ctx.stroke();

                    // Polished Outer Rim
                    ctx.strokeStyle = '#FFFFFF';
                    ctx.lineWidth = 1.2;
                    ctx.stroke();

                    // 6. Central Optical Emitter
                    ctx.beginPath();
                    ctx.arc(P_top.x, P_top.y, Math.max(3.2, 5.2 * P_top.scale), 0, Math.PI * 2);
                    ctx.fillStyle = '#FFFFFF';
                    ctx.shadowColor = db.primaryColor;
                    ctx.shadowBlur = 16;
                    ctx.fill();
                    ctx.shadowBlur = 0;
                }
            });

            // 5. Dedicated HUD Overlay Pass: Leader Pins & Floating Tag Badges (Always on top)
            databases.forEach(function(db) {
                const capTop = project(db.x, db.yTop + 2, db.z, cosX, sinX, cosY, sinY, cx, cy, fov);
                const tagProj = project(db.x + db.hudOffsetX, db.yTop + db.hudOffsetY, db.z, cosX, sinX, cosY, sinY, cx, cy, fov);

                // Glowing vertical leader pin
                ctx.beginPath();
                ctx.moveTo(capTop.x, capTop.y);
                ctx.lineTo(tagProj.x, tagProj.y + 7);
                ctx.strokeStyle = db.primaryColor;
                ctx.lineWidth = 1.1;
                ctx.stroke();

                // Micro dot at anchor
                ctx.beginPath();
                ctx.arc(capTop.x, capTop.y, 2.2, 0, Math.PI * 2);
                ctx.fillStyle = db.primaryColor;
                ctx.fill();

                // Holographic Tag Card with dynamic width
                ctx.save();
                const fontSize = Math.max(8.5, Math.round(9.5 * tagProj.scale));
                ctx.font = 'bold ' + fontSize + 'px monospace';
                const textWidth = ctx.measureText(db.tag).width;
                const tagW = Math.max(50, textWidth + 12 * tagProj.scale);
                const tagH = 17 * tagProj.scale;
                const rx = tagProj.x - tagW / 2;
                const ry = tagProj.y - tagH / 2;

                // Frosted Glass Plate in Deep Insilos Navy
                ctx.fillStyle = 'rgba(5, 14, 30, 0.94)';
                ctx.strokeStyle = db.primaryColor;
                ctx.lineWidth = 1.2;
                ctx.shadowColor = db.primaryColor;
                ctx.shadowBlur = 10;
                ctx.beginPath();
                ctx.roundRect(rx, ry, tagW, tagH, 3.5);
                ctx.fill();
                ctx.stroke();
                ctx.shadowBlur = 0;

                // Text Header
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#FFFFFF';
                ctx.fillText(db.tag, tagProj.x, tagProj.y);
                ctx.restore();
            });
        }

        // Render multiple frames for motion capture
        for (let f = 0; f < 30; f++) {
            renderFrame();
        }
        </script>
    </body>
    </html>
    `;

    await page.setContent(html);
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/home/zen/.gemini/antigravity/brain/db66bbb4-34a6-4675-a539-bdff11b8b865/test_3d_insilos_icon_preview.png' });
    await browser.close();
    console.log('3D preview captured!');
})();
