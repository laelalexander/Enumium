// Headless acceptance tests: node run-tests.mjs  (writes results/latest.json)
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
import { TESTS, runTest, createPlant } from './public/model.js';
const here = path.dirname(fileURLToPath(import.meta.url));
const DB = JSON.parse(fs.readFileSync(path.join(here, '..', 'prototype', 'design_basis.json')));
const CALC = JSON.parse(fs.readFileSync(path.join(here, '..', 'prototype', 'thermal-fluid', 'calc.json')));
const res = TESTS.map((t) => runTest(t, DB, CALC));
for (const r of res) console.log((r.pass ? 'PASS ' : 'FAIL ') + r.id + '  ' + r.name + '  ->  ' + r.detail);
const p = createPlant(DB, CALC); for (let k = 0; k < 1500; k++) p.step(1);
const s = p.s; console.log('design point:', JSON.stringify({ inlet: s.inlet.map((x) => +x.toFixed(2)), coreMax: Math.max(...s.gpu).toFixed(1), plenumT: s.plenumT.toFixed(1), plenumP: s.plenumP.toFixed(1), demand: s.demand.toFixed(2), kW: s.towerKW.toFixed(1), feedA: s.feedA.toFixed(1), imp: s.impQ.map(Math.round), alarms: s.alarms }));
fs.mkdirSync(path.join(here, 'results'), { recursive: true });
fs.writeFileSync(path.join(here, 'results', 'latest.json'), JSON.stringify({ when: new Date().toISOString(), results: res }, null, 1));
process.exit(res.every((r) => r.pass) ? 0 : 1);
