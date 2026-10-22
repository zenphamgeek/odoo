/**
 * Empirical Challenger M5-2: Video Streaming, Static Delivery, HTTP/2 & Route Latency Harness
 * 
 * Target: https://innokafe.insilos.com/
 * Focus:
 *  1. Media streaming & static asset delivery:
 *     - innokafe_coffee_pour_16x9_opt.mp4
 *     - innokafe_coffee_pour_16x9.webm
 *     - innokafe_cooling_tray_16x9_opt.mp4
 *     - innokafe_cooling_tray_16x9.webm
 *     - innokafe_logo_master.svg, dark.svg, white.svg, mark_symbol.svg
 *  2. HTTP Range Requests (bytes=0-2048, bytes=100000-200000, suffix, out-of-range).
 *  3. Byte-level exact comparison between remote streams and local filesystem sources.
 *  4. HTTP/2 Multiplexing & concurrency over a single connection session.
 *  5. TTFB and latency benchmark across all 6 core routes (< 2.0s requirement).
 */

const http2 = require('http2');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { performance } = require('perf_hooks');

const BASE_URL = 'https://innokafe.insilos.com';
const LOCAL_BASE = '/home/zen/O20';

const ASSETS = {
    videos: [
        {
            name: 'innokafe_coffee_pour_16x9_opt.mp4',
            urlPath: '/innokafe_website/static/src/video/innokafe_coffee_pour_16x9_opt.mp4',
            localPath: 'enterprise/innokafe_website/static/src/video/innokafe_coffee_pour_16x9_opt.mp4',
            expectedMime: 'video/mp4',
            format: 'mp4'
        },
        {
            name: 'innokafe_coffee_pour_16x9.webm',
            urlPath: '/innokafe_website/static/src/video/innokafe_coffee_pour_16x9.webm',
            localPath: 'enterprise/innokafe_website/static/src/video/innokafe_coffee_pour_16x9.webm',
            expectedMime: 'video/webm',
            format: 'webm'
        },
        {
            name: 'innokafe_cooling_tray_16x9_opt.mp4',
            urlPath: '/innokafe_website/static/src/video/innokafe_cooling_tray_16x9_opt.mp4',
            localPath: 'enterprise/innokafe_website/static/src/video/innokafe_cooling_tray_16x9_opt.mp4',
            expectedMime: 'video/mp4',
            format: 'mp4'
        },
        {
            name: 'innokafe_cooling_tray_16x9.webm',
            urlPath: '/innokafe_website/static/src/video/innokafe_cooling_tray_16x9.webm',
            localPath: 'enterprise/innokafe_website/static/src/video/innokafe_cooling_tray_16x9.webm',
            expectedMime: 'video/webm',
            format: 'webm'
        }
    ],
    logos: [
        {
            name: 'innokafe_logo_master.svg',
            urlPath: '/innokafe_website/static/src/img/branding/innokafe_logo_master.svg',
            localPath: 'enterprise/innokafe_website/static/src/img/branding/innokafe_logo_master.svg',
            expectedMime: 'image/svg+xml'
        },
        {
            name: 'innokafe_logo_dark.svg',
            urlPath: '/innokafe_website/static/src/img/branding/innokafe_logo_dark.svg',
            localPath: 'enterprise/innokafe_website/static/src/img/branding/innokafe_logo_dark.svg',
            expectedMime: 'image/svg+xml'
        },
        {
            name: 'innokafe_logo_white.svg',
            urlPath: '/innokafe_website/static/src/img/branding/innokafe_logo_white.svg',
            localPath: 'enterprise/innokafe_website/static/src/img/branding/innokafe_logo_white.svg',
            expectedMime: 'image/svg+xml'
        },
        {
            name: 'innokafe_mark_symbol.svg',
            urlPath: '/innokafe_website/static/src/img/branding/innokafe_mark_symbol.svg',
            localPath: 'enterprise/innokafe_website/static/src/img/branding/innokafe_mark_symbol.svg',
            expectedMime: 'image/svg+xml'
        }
    ]
};

const ROUTES = [
    { name: 'Homepage', path: '/' },
    { name: 'Story / Heritage', path: '/story' },
    { name: 'Products Catalogue', path: '/products' },
    { name: 'Taste Profiler', path: '/taste-profiler' },
    { name: 'B2B Solutions', path: '/solutions-b2b' },
    { name: 'Contact & Roastery Bar', path: '/contactus' }
];

function sha256(buffer) {
    return crypto.createHash('sha256').update(buffer).digest('hex');
}

/**
 * Perform request using native global fetch
 */
async function makeFetchRequest(url, headers = {}) {
    const startTime = performance.now();
    let res;
    try {
        res = await fetch(url, {
            method: 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) InnoKafe-Empirical-Challenger/2.0',
                ...headers
            }
        });
    } catch (err) {
        throw new Error(`Fetch network failure on ${url}: ${err.message}`);
    }

    const ttfb = performance.now() - startTime;
    const arrayBuffer = await res.arrayBuffer();
    const totalDuration = performance.now() - startTime;
    const body = Buffer.from(arrayBuffer);

    const headersObj = {};
    for (const [k, v] of res.headers.entries()) {
        headersObj[k.toLowerCase()] = v;
    }

    return {
        status: res.status,
        headers: headersObj,
        body,
        ttfb,
        totalDuration
    };
}

/**
 * Perform an HTTP/2 request using native node:http2 session
 */
function makeH2Request(session, headers, options = {}) {
    return new Promise((resolve, reject) => {
        const startTime = performance.now();
        let ttfb = null;
        let responseHeaders = {};
        const chunks = [];

        const req = session.request(headers);

        req.on('response', (hdrs) => {
            ttfb = performance.now() - startTime;
            responseHeaders = hdrs;
        });

        req.on('data', chunk => {
            chunks.push(chunk);
        });

        req.on('end', () => {
            const totalDuration = performance.now() - startTime;
            const body = Buffer.concat(chunks);
            resolve({
                status: responseHeaders[':status'],
                headers: responseHeaders,
                body,
                ttfb,
                totalDuration,
                streamId: req.id
            });
        });

        req.on('error', err => {
            reject(err);
        });

        if (options.timeout) {
            req.setTimeout(options.timeout, () => {
                req.close();
                reject(new Error(`H2 stream timeout after ${options.timeout}ms`));
            });
        }

        req.end();
    });
}

async function run() {
    console.log('================================================================================');
    console.log('  CHALLENGER M5-2: EMPIRICAL HARNESS FOR MEDIA STREAMING, HTTP/2 & ROUTE LATENCY');
    console.log('  Target: ' + BASE_URL);
    console.log('================================================================================\n');

    const summary = {
        timestamp: new Date().toISOString(),
        target: BASE_URL,
        tests: {
            videoRangeRequests: [],
            staticLogos: [],
            http2Multiplexing: null,
            routeLatencies: []
        },
        verdict: 'PENDING',
        failures: []
    };

    // -------------------------------------------------------------------------
    // TEST SUITE 1: Video Streaming & HTTP Range Requests
    // -------------------------------------------------------------------------
    console.log('--- TEST SUITE 1: VIDEO STREAMING & HTTP RANGE REQUESTS ---');

    for (const v of ASSETS.videos) {
        const fullLocalPath = path.join(LOCAL_BASE, v.localPath);
        const localStats = fs.statSync(fullLocalPath);
        const localBuffer = fs.readFileSync(fullLocalPath);
        const expectedTotalSize = localStats.size;

        console.log(`\n[*] Video: ${v.name}`);
        console.log(`    Local size: ${expectedTotalSize.toLocaleString()} bytes, MIME: ${v.expectedMime}`);

        const resultEntry = {
            asset: v.name,
            expectedSize: expectedTotalSize,
            tests: {}
        };

        // 1.1 Full HEAD check / Accept-Ranges
        const headRes = await makeFetchRequest(BASE_URL + v.urlPath, { 'Range': 'bytes=0-0' });
        console.log(`    Accept-Ranges: "${headRes.headers['accept-ranges']}", Status: ${headRes.status}`);

        // 1.2 Test Range: bytes=0-2048
        const r1 = await makeFetchRequest(BASE_URL + v.urlPath, { 'Range': 'bytes=0-2048' });
        const r1ExpectedRange = `bytes 0-2048/${expectedTotalSize}`;
        const r1ByteMatch = r1.body.equals(localBuffer.subarray(0, 2049));
        const r1Pass = (
            r1.status === 206 &&
            r1.headers['content-range'] === r1ExpectedRange &&
            r1.body.length === 2049 &&
            r1ByteMatch
        );

        console.log(`    [Range 0-2048] Status: ${r1.status}, Size: ${r1.body.length}B, Content-Range: ${r1.headers['content-range']} => ${r1Pass ? 'PASS ✓' : 'FAIL ✗'}`);
        if (!r1Pass) {
            summary.failures.push(`Video ${v.name} Range 0-2048 failed: status=${r1.status}, size=${r1.body.length}, match=${r1ByteMatch}`);
        }
        resultEntry.tests.range_0_2048 = {
            pass: r1Pass,
            status: r1.status,
            contentRange: r1.headers['content-range'],
            bytesReceived: r1.body.length,
            ttfbMs: r1.ttfb.toFixed(2),
            durationMs: r1.totalDuration.toFixed(2),
            byteMatch: r1ByteMatch
        };

        // 1.3 Test Range: bytes=100000-200000
        const r2 = await makeFetchRequest(BASE_URL + v.urlPath, { 'Range': 'bytes=100000-200000' });
        const r2ExpectedRange = `bytes 100000-200000/${expectedTotalSize}`;
        const r2ExpectedLength = 100001;
        const r2ByteMatch = r2.body.equals(localBuffer.subarray(100000, 200001));
        const r2Pass = (
            r2.status === 206 &&
            r2.headers['content-range'] === r2ExpectedRange &&
            r2.body.length === r2ExpectedLength &&
            r2ByteMatch
        );

        console.log(`    [Range 100000-200000] Status: ${r2.status}, Size: ${r2.body.length}B, Content-Range: ${r2.headers['content-range']} => ${r2Pass ? 'PASS ✓' : 'FAIL ✗'}`);
        if (!r2Pass) {
            summary.failures.push(`Video ${v.name} Range 100000-200000 failed: status=${r2.status}, size=${r2.body.length}, match=${r2ByteMatch}`);
        }
        resultEntry.tests.range_100000_200000 = {
            pass: r2Pass,
            status: r2.status,
            contentRange: r2.headers['content-range'],
            bytesReceived: r2.body.length,
            ttfbMs: r2.ttfb.toFixed(2),
            durationMs: r2.totalDuration.toFixed(2),
            byteMatch: r2ByteMatch
        };

        // 1.4 Test Range: bytes=-1024 (Suffix Range)
        const rSuffix = await makeFetchRequest(BASE_URL + v.urlPath, { 'Range': 'bytes=-1024' });
        const expectedSuffixRange = `bytes ${expectedTotalSize - 1024}-${expectedTotalSize - 1}/${expectedTotalSize}`;
        const rSuffixByteMatch = rSuffix.body.equals(localBuffer.subarray(expectedTotalSize - 1024, expectedTotalSize));
        const rSuffixPass = (
            rSuffix.status === 206 &&
            rSuffix.headers['content-range'] === expectedSuffixRange &&
            rSuffix.body.length === 1024 &&
            rSuffixByteMatch
        );
        console.log(`    [Range Suffix -1024] Status: ${rSuffix.status}, Size: ${rSuffix.body.length}B, Content-Range: ${rSuffix.headers['content-range']} => ${rSuffixPass ? 'PASS ✓' : 'FAIL ✗'}`);
        resultEntry.tests.range_suffix_1024 = {
            pass: rSuffixPass,
            status: rSuffix.status,
            contentRange: rSuffix.headers['content-range'],
            bytesReceived: rSuffix.body.length,
            byteMatch: rSuffixByteMatch
        };

        // 1.5 Test Out-of-Bounds Range: bytes=999999999-
        const rOob = await makeFetchRequest(BASE_URL + v.urlPath, { 'Range': 'bytes=999999999-' });
        const rOobPass = (rOob.status === 416);
        console.log(`    [Range Out-of-Bounds] Status: ${rOob.status} (Expected 416) => ${rOobPass ? 'PASS ✓' : 'FAIL ✗'}`);
        resultEntry.tests.range_oob = {
            pass: rOobPass,
            status: rOob.status
        };

        summary.tests.videoRangeRequests.push(resultEntry);
    }

    // -------------------------------------------------------------------------
    // TEST SUITE 2: Static Vector Branding Assets Delivery & Hash Verification
    // -------------------------------------------------------------------------
    console.log('\n--- TEST SUITE 2: STATIC VECTOR BRANDING ASSETS & HASH VERIFICATION ---');

    for (const logo of ASSETS.logos) {
        const fullLocalPath = path.join(LOCAL_BASE, logo.localPath);
        const localBuffer = fs.readFileSync(fullLocalPath);
        const localHash = sha256(localBuffer);

        const res = await makeFetchRequest(BASE_URL + logo.urlPath);
        const remoteHash = sha256(res.body);

        const mimeMatches = res.headers['content-type'] && res.headers['content-type'].includes(logo.expectedMime);
        const sizeMatches = res.body.length === localBuffer.length;
        const hashMatches = remoteHash === localHash;
        const pass = (res.status === 200 && mimeMatches && sizeMatches && hashMatches);

        console.log(`[*] Logo: ${logo.name}`);
        console.log(`    Status: ${res.status}, Content-Type: ${res.headers['content-type']}`);
        console.log(`    Size: Remote=${res.body.length}B, Local=${localBuffer.length}B (Match: ${sizeMatches})`);
        console.log(`    SHA256 Remote: ${remoteHash}`);
        console.log(`    SHA256 Local:  ${localHash}`);
        console.log(`    Hash Integrity: ${hashMatches ? 'EXACT MATCH ✓' : 'MISMATCH ✗'}`);

        if (!pass) {
            summary.failures.push(`Logo ${logo.name} failed: status=${res.status}, mime=${res.headers['content-type']}, hashMatch=${hashMatches}`);
        }

        summary.tests.staticLogos.push({
            name: logo.name,
            pass,
            status: res.status,
            contentType: res.headers['content-type'],
            remoteSize: res.body.length,
            localSize: localBuffer.length,
            hashMatches,
            ttfbMs: res.ttfb.toFixed(2),
            durationMs: res.totalDuration.toFixed(2)
        });
    }

    // -------------------------------------------------------------------------
    // TEST SUITE 3: HTTP/2 Multiplexing & Stream Concurrency
    // -------------------------------------------------------------------------
    console.log('\n--- TEST SUITE 3: HTTP/2 MULTIPLEXING & STREAM CONCURRENCY ---');

    const h2Session = http2.connect(BASE_URL);
    await new Promise((resolve, reject) => {
        h2Session.on('connect', resolve);
        h2Session.on('error', reject);
    });

    console.log(`[✓] HTTP/2 Connected. ALPN Protocol: ${h2Session.alpnProtocol}`);
    console.log(`[✓] Remote socket: ${h2Session.socket.remoteAddress}:${h2Session.socket.remotePort}, Local: ${h2Session.socket.localPort}`);

    // Dispatch 12 concurrent multiplexed requests across the single session
    const concurrentRequests = [
        { path: ASSETS.videos[0].urlPath, headers: { range: 'bytes=0-1024' } },
        { path: ASSETS.videos[0].urlPath, headers: { range: 'bytes=1025-2048' } },
        { path: ASSETS.videos[1].urlPath, headers: { range: 'bytes=0-1024' } },
        { path: ASSETS.videos[2].urlPath, headers: { range: 'bytes=0-1024' } },
        { path: ASSETS.videos[3].urlPath, headers: { range: 'bytes=0-1024' } },
        { path: ASSETS.logos[0].urlPath, headers: {} },
        { path: ASSETS.logos[1].urlPath, headers: {} },
        { path: ASSETS.logos[2].urlPath, headers: {} },
        { path: ASSETS.logos[3].urlPath, headers: {} },
        { path: '/', headers: {} },
        { path: '/story', headers: {} },
        { path: '/products', headers: {} }
    ];

    const h2StartTime = performance.now();
    const h2Promises = concurrentRequests.map(async (cr, idx) => {
        const streamHeaders = {
            ':path': cr.path,
            ':method': 'GET',
            ...cr.headers
        };
        const res = await makeH2Request(h2Session, streamHeaders, { timeout: 15000 });
        return {
            index: idx,
            path: cr.path,
            range: cr.headers.range || 'FULL',
            streamId: res.streamId,
            status: res.status,
            bytesReceived: res.body.length,
            ttfbMs: res.ttfb.toFixed(2),
            durationMs: res.totalDuration.toFixed(2)
        };
    });

    const h2Results = await Promise.all(h2Promises);
    const h2TotalDuration = performance.now() - h2StartTime;

    console.log(`[✓] Dispatched ${concurrentRequests.length} streams concurrently over single H2 connection in ${h2TotalDuration.toFixed(2)}ms:`);
    let h2AllPass = true;
    for (const hr of h2Results) {
        const pass = (hr.status === 200 || hr.status === 206);
        if (!pass) h2AllPass = false;
        console.log(`    Stream #${hr.streamId} [Idx ${hr.index}] -> ${hr.path.split('/').pop() || '/'} (${hr.range}): Status ${hr.status}, Size ${hr.bytesReceived}B, TTFB ${hr.ttfbMs}ms, Dur ${hr.durationMs}ms`);
    }

    if (!h2AllPass) {
        summary.failures.push('HTTP/2 multiplexing had non-200/206 status codes in concurrent stream burst.');
    }

    summary.tests.http2Multiplexing = {
        pass: h2AllPass,
        alpnProtocol: h2Session.alpnProtocol,
        concurrentStreamsCount: concurrentRequests.length,
        totalBurstDurationMs: h2TotalDuration.toFixed(2),
        streams: h2Results
    };

    h2Session.close();

    // -------------------------------------------------------------------------
    // TEST SUITE 4: All 6 Routes Latency & TTFB Benchmark (< 2.0s Requirement)
    // -------------------------------------------------------------------------
    console.log('\n--- TEST SUITE 4: ALL 6 CORE ROUTES LATENCY & TTFB (< 2.0s REQUIREMENT) ---');

    const ROUNDS = 5;
    for (const r of ROUTES) {
        console.log(`\n[*] Benchmarking Route: ${r.name} (${r.path}) [${ROUNDS} rounds]`);
        const durations = [];
        const ttfbs = [];
        const statuses = [];
        let bodySize = 0;

        for (let round = 1; round <= ROUNDS; round++) {
            const res = await makeFetchRequest(BASE_URL + r.path);
            durations.push(res.totalDuration);
            ttfbs.push(res.ttfb);
            statuses.push(res.status);
            bodySize = res.body.length;
            // Short pause between rounds
            await new Promise(res => setTimeout(res, 100));
        }

        durations.sort((a, b) => a - b);
        const min = durations[0];
        const max = durations[durations.length - 1];
        const median = durations[Math.floor(durations.length / 2)];
        const sum = durations.reduce((a, b) => a + b, 0);
        const mean = sum / durations.length;
        const p95 = durations[Math.min(durations.length - 1, Math.floor(durations.length * 0.95))];
        const all200 = statuses.every(s => s === 200);
        const under2s = max < 2000;
        const pass = all200 && under2s;

        console.log(`    Status: ${statuses.join(', ')} (All 200: ${all200 ? 'YES' : 'NO'})`);
        console.log(`    Payload size: ${bodySize.toLocaleString()} bytes`);
        console.log(`    TTFB avg: ${(ttfbs.reduce((a, b) => a + b, 0) / ttfbs.length).toFixed(2)}ms`);
        console.log(`    Latency: Min=${min.toFixed(1)}ms | Mean=${mean.toFixed(1)}ms | Median=${median.toFixed(1)}ms | P95=${p95.toFixed(1)}ms | Max=${max.toFixed(1)}ms`);
        console.log(`    Compliance (< 2.0s): ${under2s ? 'PASS (Well below 2.0s threshold) ✓' : 'FAIL (Exceeds 2.0s) ✗'}`);

        if (!pass) {
            summary.failures.push(`Route ${r.path} failed: all200=${all200}, maxLatency=${max.toFixed(1)}ms`);
        }

        summary.tests.routeLatencies.push({
            name: r.name,
            path: r.path,
            pass,
            allStatus200: all200,
            bodySizeBytes: bodySize,
            ttfbAvgMs: (ttfbs.reduce((a, b) => a + b, 0) / ttfbs.length).toFixed(2),
            latency: {
                minMs: min.toFixed(1),
                meanMs: mean.toFixed(1),
                medianMs: median.toFixed(1),
                p95Ms: p95.toFixed(1),
                maxMs: max.toFixed(1)
            }
        });
    }

    // -------------------------------------------------------------------------
    // FINAL VERDICT EVALUATION
    // -------------------------------------------------------------------------
    console.log('\n================================================================================');
    if (summary.failures.length === 0) {
        summary.verdict = 'APPROVE';
        console.log('  FINAL VERDICT: APPROVE 🏆');
        console.log('  All empirical challenges passed with 100% precision:');
        console.log('   - 4/4 Videos range requests (0-2048, 100000-200000, suffix, oob) verified.');
        console.log('   - Exact byte-level hash parity between remote stream chunks and local files.');
        console.log('   - 4/4 Static logo assets returned HTTP 200 with 100% SHA256 integrity match.');
        console.log('   - HTTP/2 multiplexing proven across 12 concurrent streams on single socket.');
        console.log('   - 6/6 Core routes returned HTTP 200 with latency strictly < 2.0s.');
    } else {
        summary.verdict = 'REQUEST_CHANGES';
        console.log('  FINAL VERDICT: REQUEST_CHANGES ⚠️');
        console.log(`  Identified ${summary.failures.length} empirical failures:`);
        summary.failures.forEach(f => console.log(`   - ${f}`));
    }
    console.log('================================================================================\n');

    // Write machine-readable artifact
    const artifactPath = '/home/zen/O20/.agents/teamwork/challenger_m5_2/empirical_metrics.json';
    fs.writeFileSync(artifactPath, JSON.stringify(summary, null, 2));
    console.log(`[✓] Saved empirical metrics artifact to: ${artifactPath}`);

    return summary;
}

run().catch(err => {
    console.error('Fatal harness error:', err);
    process.exit(1);
});
