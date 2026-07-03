#!/usr/bin/env node
/* Render smoke test: executes EVERY SPA route against a live server with a
   minimal DOM stub, so template errors, missing fields and bad API wiring
   surface before a human ever sees a tab. Usage:
     node webapp/test_render.js [port]         (server must be running)
   Exits 1 if any route throws. */
const PORT = process.argv[2] || 8787;
const BASE = `http://localhost:${PORT}`;
const fs = require("fs");
const path = require("path");

/* ---------------- minimal DOM stub ---------------- */
function makeEl() {
  return new Proxy({
    innerHTML: "", value: "", checked: false, dataset: {}, style: {},
    classList: { add(){}, remove(){}, contains(){ return false; } },
    addEventListener(){}, removeEventListener(){}, remove(){},
    scrollIntoView(){}, focus(){}, click(){},
    querySelector(){ return makeEl(); },
    querySelectorAll(){ return []; },
    getContext(){ return new Proxy({}, { get: (t, k) =>
      k === "measureText" ? () => ({ width: 10 }) : () => {} }); },
    clientWidth: 800, files: [],
    appendChild(){}, setAttribute(){},
  }, { get(t, k){ return k in t ? t[k] : (t[k] = ""); },
       set(t, k, v){ t[k] = v; return true; } });
}
const documentStub = {
  querySelector: () => makeEl(),
  querySelectorAll: () => [],
  getElementById: () => makeEl(),
  createElement: () => makeEl(),
  documentElement: makeEl(),
};
const storage = () => { const m = {}; return {
  getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); },
  removeItem: k => { delete m[k]; } }; };

const sandbox = {
  document: documentStub,
  addEventListener(){}, removeEventListener(){}, scrollTo(){},
  location: { hash: "#home", protocol: "http:" },
  localStorage: storage(), sessionStorage: storage(),
  devicePixelRatio: 1, navigator: { userAgent: "render-test" },
  getComputedStyle: () => ({ getPropertyValue: () => "#0071e3" }),
  setInterval: () => 0, clearInterval(){}, setTimeout: (f) => 0,
  prompt: () => null, alert(){},
  fetch: (u, o) => fetch(u.startsWith("http") ? u : BASE + u, o),
  console,
  CanvasRenderingContext2D: function(){},
};
sandbox.window = sandbox;   // window === globalThis-ish
sandbox.globalThis = sandbox;

/* ---------------- load the SPA scripts ---------------- */
const html = fs.readFileSync(path.join(__dirname, "static", "index.html"), "utf8");
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)]
  .map(m => m[1]).filter(s => s.trim());
const vm = require("vm");
const ctx = vm.createContext(sandbox);
for (const s of scripts) {
  // route() auto-runs at load; allow it, errors surface per-route below
  vm.runInContext(s, ctx);
}

/* ---------------- exercise every route ---------------- */
(async () => {
  // const/let live in the context's lexical scope, not on the global object
  const ROUTES = vm.runInContext(
    "typeof ROUTES !== 'undefined' ? ROUTES : null", ctx);
  sandbox.ROUTES = ROUTES;
  const routes = Object.keys(sandbox.ROUTES || {});
  if (!routes.length) { console.error("no ROUTES found"); process.exit(1); }
  // deep-link cases too
  const cases = [...routes.map(r => [r, []]), ["experiments", ["__detail__"]]];
  let failed = 0;
  for (const [r, rest] of cases) {
    const app = makeEl();
    try {
      let args = rest;
      if (rest[0] === "__detail__") {
        const st = await (await fetch(BASE + "/api/state")).json();
        args = [encodeURIComponent(st.runs[0].run_id)];
      }
      sandbox.location.hash = "#" + r;
      await sandbox.ROUTES[r](app, args);
      if (!String(app.innerHTML).trim()) throw new Error("rendered empty page");
      console.log(`route ${r}${rest.length ? "/" + rest[0] : ""}`.padEnd(28), "OK",
                  `(${String(app.innerHTML).length} chars)`);
    } catch (e) {
      failed++;
      console.log(`route ${r}`.padEnd(28), "FAIL:", e.message);
    }
  }
  // the interactive fitters
  try {
    const r = await (await fetch(BASE + "/api/try_equation", { method: "POST",
      body: JSON.stringify({ series: "moon_distance", periods_d: [27.555] }) })).json();
    if (r.error) throw new Error(r.error);
    console.log("try_equation".padEnd(28), "OK");
  } catch (e) { failed++; console.log("try_equation".padEnd(28), "FAIL:", e.message); }
  console.log(failed ? `\n${failed} FAILURES` : "\nALL ROUTES RENDER");
  process.exit(failed ? 1 : 0);
})();
