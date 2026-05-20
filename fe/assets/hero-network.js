(function () {
    "use strict";

    var COLOR = "#4E6B66";
    var NODE_COUNT_BASE = 90;
    var OVERSHOOT = 130;
    var K_NEIGHBOURS = 6;
    var EDGE_ALPHA = 0.26;
    var NODE_ALPHA = 0.75;
    var HALO_ALPHA = 0.14;
    var BIG_NODE_RATIO = 0.16;
    var SPRING = 0.0095;
    var DAMPING = 0.95;
    var KICK = 0.065;
    var RADIUS_PERIOD_MIN = 7000;
    var RADIUS_PERIOD_MAX = 15000;

    function attach(host) {
        if (!host || host.__heroNetworkAttached) return;
        host.__heroNetworkAttached = true;

        host.replaceChildren();
        var canvas = document.createElement("canvas");
        canvas.className = "hero-network__canvas";
        canvas.setAttribute("aria-hidden", "true");
        host.appendChild(canvas);

        var ctx = canvas.getContext("2d");
        var dpr = window.devicePixelRatio || 1;
        var width = 0;
        var height = 0;
        var nodes = [];
        var edges = [];
        var rafId = null;
        var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        function resize() {
            var rect = host.getBoundingClientRect();
            width = Math.max(1, rect.width);
            height = Math.max(1, rect.height);
            canvas.style.width = width + "px";
            canvas.style.height = height + "px";
            canvas.width = Math.floor(width * dpr);
            canvas.height = Math.floor(height * dpr);
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }

        function densityScale() {
            return Math.max(0.55, Math.min(1.4, (width * height) / (1400 * 500)));
        }

        // Anchors are scattered with light de-clustering: each new candidate
        // keeps the farthest of a few random tries from existing anchors, so
        // the mesh doesn't pile points into knots.
        function initNodes() {
            var count = Math.round(NODE_COUNT_BASE * densityScale());
            var minX = -OVERSHOOT, maxX = width + OVERSHOOT;
            var minY = -OVERSHOOT, maxY = height + OVERSHOOT;
            nodes = [];
            for (var i = 0; i < count; i++) {
                var best = null;
                var bestScore = -1;
                for (var t = 0; t < 6; t++) {
                    var cx = minX + Math.random() * (maxX - minX);
                    var cy = minY + Math.random() * (maxY - minY);
                    var minDist = Infinity;
                    for (var k = 0; k < nodes.length; k++) {
                        var n = nodes[k];
                        var dx = cx - n.xa, dy = cy - n.ya;
                        var d = dx * dx + dy * dy;
                        if (d < minDist) minDist = d;
                    }
                    if (minDist > bestScore) { bestScore = minDist; best = { x: cx, y: cy }; }
                }
                var big = Math.random() < BIG_NODE_RATIO;
                var rSmall = 1.3 + Math.random() * 1.6;
                var rBig = 3.4 + Math.random() * 4.2;
                nodes.push({
                    x: best.x, y: best.y,
                    xa: best.x, ya: best.y,
                    vx: 0, vy: 0,
                    r: big ? rBig : rSmall,
                    r0: big ? rBig : rSmall,
                    rAlt: big ? rSmall : rBig,
                    phase: Math.random() * Math.PI * 2,
                    period: RADIUS_PERIOD_MIN + Math.random() * (RADIUS_PERIOD_MAX - RADIUS_PERIOD_MIN),
                });
            }
        }

        // k-nearest-neighbour graph over anchor positions. Topology is fixed
        // for the lifetime of the attach (anchors don't move), so vibration
        // just makes existing edges flex.
        function buildEdges() {
            edges = [];
            var N = nodes.length;
            var seen = new Set();
            for (var i = 0; i < N; i++) {
                var dists = [];
                for (var j = 0; j < N; j++) {
                    if (j === i) continue;
                    var dx = nodes[i].xa - nodes[j].xa;
                    var dy = nodes[i].ya - nodes[j].ya;
                    dists.push([j, dx * dx + dy * dy]);
                }
                dists.sort(function (u, v) { return u[1] - v[1]; });
                var take = Math.min(K_NEIGHBOURS, dists.length);
                for (var k = 0; k < take; k++) {
                    var jj = dists[k][0];
                    var key = i < jj ? i + "_" + jj : jj + "_" + i;
                    if (!seen.has(key)) { seen.add(key); edges.push([i, jj]); }
                }
            }
        }

        function frame(tNow) {
            if (typeof tNow !== "number") tNow = performance.now();
            ctx.clearRect(0, 0, width, height);

            // Each node breathes between its initial radius and an inverse
            // (small <-> big), on its own period and phase so the network
            // continuously churns through size swaps with no sync.
            for (var s = 0; s < nodes.length; s++) {
                var ns = nodes[s];
                var ang = (tNow / ns.period) * Math.PI * 2 + ns.phase;
                var mix = (Math.sin(ang) + 1) * 0.5;
                ns.r = ns.r0 * (1 - mix) + ns.rAlt * mix;
            }

            ctx.globalAlpha = EDGE_ALPHA;
            ctx.strokeStyle = COLOR;
            ctx.lineWidth = 0.65;
            ctx.beginPath();
            for (var i = 0; i < edges.length; i++) {
                var a = nodes[edges[i][0]];
                var b = nodes[edges[i][1]];
                ctx.moveTo(a.x, a.y);
                ctx.lineTo(b.x, b.y);
            }
            ctx.stroke();

            ctx.fillStyle = COLOR;
            for (var p = 0; p < nodes.length; p++) {
                var nd = nodes[p];
                // Halo fades in/out smoothly with current radius rather than
                // popping on the r>3 threshold.
                var haloT = Math.max(0, Math.min(1, (nd.r - 2.4) / 2.0));
                if (haloT > 0) {
                    ctx.globalAlpha = HALO_ALPHA * haloT;
                    ctx.beginPath();
                    ctx.arc(nd.x, nd.y, nd.r * 2.6, 0, Math.PI * 2);
                    ctx.fill();
                }
                ctx.globalAlpha = NODE_ALPHA;
                ctx.beginPath();
                ctx.arc(nd.x, nd.y, nd.r, 0, Math.PI * 2);
                ctx.fill();
            }
            ctx.globalAlpha = 1;

            // Vibration: each frame the node gets a random kick, a spring
            // pull-back toward its anchor, and damping. Equilibrium amplitude
            // stays ~6–12 px from anchor with current constants.
            for (var m = 0; m < nodes.length; m++) {
                var q = nodes[m];
                q.vx = q.vx * DAMPING + (Math.random() - 0.5) * KICK + (q.xa - q.x) * SPRING;
                q.vy = q.vy * DAMPING + (Math.random() - 0.5) * KICK + (q.ya - q.y) * SPRING;
                q.x += q.vx;
                q.y += q.vy;
            }

            rafId = window.requestAnimationFrame(frame);
        }

        function start() {
            resize();
            initNodes();
            buildEdges();
            if (rafId) window.cancelAnimationFrame(rafId);
            if (reduced) {
                frame();
                if (rafId) window.cancelAnimationFrame(rafId);
                rafId = null;
            } else {
                rafId = window.requestAnimationFrame(frame);
            }
        }

        var resizeTimer = null;
        window.addEventListener("resize", function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(start, 140);
        });

        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                if (rafId) window.cancelAnimationFrame(rafId);
                rafId = null;
            } else if (!reduced && rafId === null) {
                rafId = window.requestAnimationFrame(frame);
            }
        });

        start();
    }

    function scan() {
        var hosts = document.querySelectorAll(".hero-network");
        for (var i = 0; i < hosts.length; i++) attach(hosts[i]);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", scan);
    } else {
        scan();
    }

    var mo = new MutationObserver(function () { scan(); });
    mo.observe(document.documentElement, { childList: true, subtree: true });
})();
