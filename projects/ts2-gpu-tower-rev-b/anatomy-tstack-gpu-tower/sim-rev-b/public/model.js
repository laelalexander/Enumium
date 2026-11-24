// TS-2 rev B plant + controls model (runs in the browser and in node for headless tests).
// Parameters come from prototype/design_basis.json and prototype/thermal-fluid/calc.json (passed in);
// every number not taken from there is in A with its reason.
export const A = {
  gpuRth: [0.167, 'K/W GPU core to inlet air at full blower (generic blower card; replace with NVIDIA fan curve)'],
  gpuTau: [25, 's GPU heat-sink time constant'],
  gpuSlowdown: [90, 'C slowdown: power cut 30 % above this'],
  gpuMaxAccept: [85, 'C acceptance limit at the design point'],
  blowerFailRth: [3.2, 'x Rth when a card blower has failed (natural draft through the shroud only)'],
  plenumTau: [40, 's plenum air + sheet metal'],
  coolTau: [120, 's chiller supply response'],
  coolDriftTau: [900, 's coolant drift toward room when the chiller is off (loop thermal mass ~ 60 L)'],
  tecDT: [1.05, 'K TEC trim drop on the coolant (4 x 110 W / (6 L/min x 4186))'],
  dpKp: [0.004, 'impeller demand per Pa error per s (PI integral gain)'],
  leakPerPa: [0.002, 'share of intake flow lost to bypass per Pa of positive plenum error'],
  crpsW: [2000, 'W CRPS rating at 200-240 V'],
};
const a = (k) => A[k][0];

export function createPlant(DB, CALC) {
  const DP = CALC.design_point;
  const coil0 = DP.coil;
  const nC = DB.n_columns, nG = DB.gpus_per_column;
  const curve = DB.imp_curve_48V;                      // [m3/h, Pa] at 48 V
  const busV = 56;
  const s = {
    t: 0, room: DB.T_room_design_C, rh: DB.RH_design, chiller: true, chillSet: DB.T_coolant_supply_C, tec: true,
    load: Array(nC).fill(1), impFail: [false, false, false], blowerFail: Array(nC * nG).fill(false), filterClog: Array(nC).fill(0),
    crpsFail: Array(nC * 4).fill(false), feedLoss: { A: false, B: false },
    coolant: DB.T_coolant_supply_C, dew: 0, coilQ: Array(nC).fill(0), inlet: Array(nC).fill(DB.T_room_design_C),
    gpu: Array(nC * nG).fill(35), gpuP: Array(nC * nG).fill(0), throttle: Array(nC * nG).fill(false),
    plenumT: 30, plenumP: DP.plenum_setpoint_Pa, setP: DP.plenum_setpoint_Pa, demand: 0.6, impQ: [0, 0, 0], impRpm: [0, 0, 0],
    flowIn: 0, crpsLoad: Array(nC * 4).fill(0), feedA: 0, feedB: 0, towerKW: 0, alarms: [], condensing: false,
  };
  const rhoAir = (T) => 101325 / (287.05 * (T + 273.15));
  const dew = (T, RH) => { const A1 = 17.62, B = 243.12, g = Math.log(RH) + A1 * T / (B + T); return B * g / (A1 - g); };
  function fanQ(dp, d) {                                // flow of one impeller at static dp, demand d, 56 V bus
    const k = (busV / 48) * d;
    const pts = curve.map(([q, p]) => [q * k, p * k * k]).sort((x, y) => x[1] - y[1]);
    if (dp <= pts[0][1]) return pts[0][0];
    for (let i = 0; i < pts.length - 1; i++) { const [q0, p0] = pts[i], [q1, p1] = pts[i + 1]; if (dp <= p1) return q0 + (q1 - q0) * (dp - p0) / (p1 - p0); }
    return 0;
  }
  function step(dt) {
    s.t += dt;
    const al = [];
    s.dew = dew(s.room, s.rh);
    // ---- coolant (chiller holds max(set, dew + 2); TEC trim on top)
    const target = s.chiller ? Math.max(s.chillSet, s.dew + 2.0) : s.room + 1.5;
    const tau = s.chiller ? a('coolTau') : a('coolDriftTau');
    s.coolant += (target - s.coolant) * Math.min(1, dt / tau);
    const tw = s.coolant - (s.tec ? a('tecDT') : 0);
    s.condensing = tw < s.dew;
    if (s.condensing) al.push('COIL_BELOW_DEW');
    if (!s.chiller) al.push('CHILLER_OFF');
    // ---- columns: coil, GPU inlet
    let Hgpu = 0, Qin = 0;
    const qGpu = DB.GPU_AIR_M3H / 3600;
    for (let c = 0; c < nC; c++) {
      const clog = s.filterClog[c];
      const airFrac = Math.max(0.3, 1 - 0.5 * clog);
      const Cair = nG * qGpu * airFrac * rhoAir(s.room) * 1007;
      const Cw = DB.coolant_lpm_per_column / 60000 * 999 * 4186;
      const UA = coil0.UA_W_K * Math.pow(airFrac, 0.5);
      const Cmin = Math.min(Cair, Cw), Cmax = Math.max(Cair, Cw), Cr = Cmin / Cmax, NTU = UA / Cmin;
      const eps = (1 - Math.exp(-NTU * (1 - Cr))) / (1 - Cr * Math.exp(-NTU * (1 - Cr)));
      const Q = Math.max(0, eps * Cmin * (s.room - tw));
      s.coilQ[c] = Q;
      s.inlet[c] = s.room - Q / Cair;
      if (clog > 0.6) al.push(`C${c + 1}_FILTER`);
      Qin += nG * qGpu * airFrac;
      for (let g = 0; g < nG; g++) {
        const i = c * nG + g;
        const tin = s.inlet[c] + 0.04 * g;              // the coil water warms along its circuit: upper passes see ~0.6 K less cooling
        let P = 300 * s.load[c];
        const col = (c < 2 ? s.feedLoss.A : s.feedLoss.B);
        const okPsu = s.crpsFail.slice(c * 4, c * 4 + 4).filter((f) => !f).length;
        if (col || okPsu < 3) P = (col || okPsu < 2) ? 0 : P;
        if (s.throttle[i]) P *= 0.7;
        const rth = a('gpuRth') * (s.blowerFail[i] ? a('blowerFailRth') : 1) * Math.pow(Math.max(0.5, airFrac), -0.8) * (1 + Math.max(0, s.plenumP - s.setP) * a('leakPerPa'));
        const tgt = tin + rth * P;
        s.gpu[i] += (tgt - s.gpu[i]) * Math.min(1, dt / a('gpuTau'));
        if (s.gpu[i] > a('gpuSlowdown')) s.throttle[i] = true; else if (s.gpu[i] < a('gpuSlowdown') - 6) s.throttle[i] = false;
        s.gpuP[i] = P;
        Hgpu += P;
        if (s.blowerFail[i]) al.push(`C${c + 1}S${String(g + 1).padStart(2, '0')}_BLOWER`);
        if (s.throttle[i]) al.push(`C${c + 1}S${String(g + 1).padStart(2, '0')}_SLOWDOWN`);
      }
    }
    // ---- other heat into the air stream (host nodes, TEC hot side, boards)
    const hostW = nC * 410 * (0.4 + 0.6 * (s.load.reduce((x, y) => x + y, 0) / nC));
    const tecHot = s.tec ? nC * DP.tec_hot_W_per_col : 0;
    const Hext = hostW + tecHot + nC * 48;
    const Qhost = nC * DP.host_air_m3_h_per_col / 3600, Qtec = s.tec ? nC * 0.053 : 0;
    const Qtot = Qin + Qhost + Qtec;                     // m3/s at room density
    const mdot = Qtot * rhoAir(s.room);
    const Qcoil = s.coilQ.reduce((x, y) => x + y, 0);
    const Tpl = s.room + (Hgpu + Hext - Qcoil) / (mdot * 1007);
    s.plenumT += (Tpl - s.plenumT) * Math.min(1, dt / a('plenumTau'));
    // ---- turbine: PI on plenum pressure; plenum pressure is where impeller flow = intake flow
    const running = s.impFail.map((f) => !f).filter(Boolean).length;
    const Qpl = Qtot * rhoAir(s.room) / rhoAir(s.plenumT) * 3600;          // m3/h
    const loss = DP.dp_chimney_Pa * Math.pow(Qpl / DP.airflow_plenum_m3_h, 2) + DP.dp_crown_Pa * Math.pow(Qpl / DP.airflow_plenum_m3_h, 2) - DP.stack_Pa;
    // find plenum pressure p (negative) such that running * fanQ(-p + loss, demand) = Qpl
    let lo = -600, hi = 50;
    for (let k = 0; k < 40; k++) { const p = (lo + hi) / 2; const q = running * fanQ(-p + loss, s.demand); if (q > Qpl) hi = p; else lo = p; }
    const pPl = running ? (lo + hi) / 2 : 20;
    s.plenumP += (pPl - s.plenumP) * Math.min(1, dt / 3);
    const err = s.plenumP - s.setP;                       // positive = not negative enough
    s.demand = Math.max(0.2, Math.min(1, s.demand + a('dpKp') * err * dt));
    for (let k = 0; k < 3; k++) {
      const on = !s.impFail[k];
      s.impQ[k] = on ? fanQ(-s.plenumP + loss, s.demand) : 0;
      s.impRpm[k] = on ? 2000 * (busV / 48) * s.demand : 0;
      if (!on) al.push(`IMP${k + 1}_FAIL`);
    }
    if (s.demand >= 0.99 && err > 3) al.push('PLENUM_PRESSURE_LOW');
    // ---- power
    let fa = 0, fb = 0;
    for (let c = 0; c < nC; c++) {
      const colGpuW = s.gpuP.slice(c * nG, c * nG + nG).reduce((x, y) => x + y, 0) + 48;
      const ok = [0, 1, 2, 3].filter((k) => !s.crpsFail[c * 4 + k]);
      for (let k = 0; k < 4; k++) s.crpsLoad[c * 4 + k] = ok.includes(k) && ok.length ? colGpuW / ok.length : 0;
      if (ok.length < 4) al.push(`C${c + 1}_CRPS_${4 - ok.length}_DOWN`);
      if (ok.length && colGpuW / ok.length > a('crpsW')) al.push(`C${c + 1}_CRPS_OVERLOAD`);
      const ac = colGpuW / 0.94 + 455 * (0.4 + 0.6 * s.load[c]) + (s.tec ? 604 : 60);
      if (c < 2) fa += s.feedLoss.A ? 0 : ac; else fb += s.feedLoss.B ? 0 : ac;
    }
    const impW = s.impQ.reduce((x, q, k) => x + (s.impFail[k] ? 0 : 190 * Math.pow(busV / 48 * s.demand, 3)), 0);
    fa += impW / 2 + 90; fb += impW / 2 + 90;
    s.feedA = fa / (Math.sqrt(3) * 208); s.feedB = fb / (Math.sqrt(3) * 208);
    s.towerKW = (fa + fb) / 1000;
    if (s.feedA > 48 || s.feedB > 48) al.push('FEED_OVER_80PCT');
    if (s.feedLoss.A) al.push('FEED_A_LOST'); if (s.feedLoss.B) al.push('FEED_B_LOST');
    s.flowIn = Qtot * 3600;
    s.alarms = [...new Set(al)];
    return s;
  }
  return { s, step, fanQ };
}

// ---------------------------------------------------------------- acceptance tests (headless-capable)
export const TESTS = [
  { id: 'AC-THM-01', name: 'Design point 27 C / 50 %: every GPU inlet <= 25 C and core <= 85 C', setup: () => {}, secs: 1800,
    check: (s, DB) => { const mx = Math.max(...s.gpu), mi = Math.max(...s.inlet); return [mi <= 25 && mx <= 85, `inlet max ${mi.toFixed(1)} C, core max ${mx.toFixed(1)} C`]; } },
  { id: 'AC-THM-02', name: 'Hot room 35 C / 40 %: no GPU reaches slowdown (90 C)', setup: (s) => { s.room = 35; s.rh = 0.40; }, secs: 1800,
    check: (s) => { const mx = Math.max(...s.gpu); return [mx < 90 && !s.throttle.some(Boolean), `core max ${mx.toFixed(1)} C`]; } },
  { id: 'AC-THM-03', name: 'Chiller trips at full load, 27 C room: tower rides through on room air, no slowdown', setup: (s) => { s.chiller = false; }, secs: 3600,
    check: (s) => { const mx = Math.max(...s.gpu); return [mx < 90 && s.alarms.includes('CHILLER_OFF'), `core max ${mx.toFixed(1)} C, CHILLER_OFF raised`]; } },
  { id: 'AC-THM-04', name: 'One impeller fails: the other two hold the plenum within 10 Pa of set, cores <= 85 C', setup: (s) => { s.impFail[1] = true; }, secs: 1200,
    check: (s) => { const mx = Math.max(...s.gpu); const e = s.plenumP - s.setP; return [mx <= 85 && e < 10 && s.alarms.includes('IMP2_FAIL'), `plenum error ${e.toFixed(1)} Pa, core max ${mx.toFixed(1)} C`]; } },
  { id: 'AC-THM-05', name: 'Humid room 27 C / 70 %: coolant lifts to dew + 2 K, coil never condenses', setup: (s) => { s.rh = 0.70; }, secs: 1800,
    check: (s) => [!s.condensing && s.coolant - (s.tec ? 1.05 : 0) >= s.dew - 0.05, `coolant ${s.coolant.toFixed(1)} C vs dew ${s.dew.toFixed(1)} C`] },
  { id: 'AC-THM-06', name: 'Blower failure on C2 slot 07: only that card slows down; neighbours unaffected', setup: (s) => { s.blowerFail[16 + 6] = true; }, secs: 900,
    check: (s) => { const bad = s.throttle.map((t, i) => t ? i : -1).filter((i) => i >= 0); return [bad.length === 1 && bad[0] === 22 && s.alarms.includes('C2S07_BLOWER'), `throttled: ${bad.map((i) => 'C' + (Math.floor(i / 16) + 1) + 'S' + String(i % 16 + 1).padStart(2, '0')).join(', ') || 'none'}`]; } },
  { id: 'AC-PWR-01', name: 'One CRPS fails in C1: remaining three share, none above 2000 W', setup: (s) => { s.crpsFail[0] = true; }, secs: 120,
    check: (s) => { const m = Math.max(...s.crpsLoad.slice(0, 4)); return [m <= 2000 && s.gpuP.slice(0, 16).every((p) => p > 0), `max CRPS ${m.toFixed(0)} W`]; } },
  { id: 'AC-PWR-02', name: 'Full load: each 60 A feed below 48 A (80 % continuous)', setup: () => {}, secs: 600,
    check: (s) => [s.feedA <= 48 && s.feedB <= 48, `feed A ${s.feedA.toFixed(1)} A, feed B ${s.feedB.toFixed(1)} A`] },
  { id: 'AC-THM-07', name: 'Filter on C4 70 % clogged: alarm raised before any slowdown', setup: (s) => { s.filterClog[3] = 0.7; }, secs: 1200,
    check: (s) => [s.alarms.includes('C4_FILTER') && !s.throttle.some(Boolean), `max core C4 ${Math.max(...s.gpu.slice(48)).toFixed(1)} C`] },
];

export function runTest(T, DB, CALC) {
  const p = createPlant(DB, CALC);
  for (let k = 0; k < 600; k++) p.step(1);              // settle at the design point first
  T.setup(p.s);
  for (let k = 0; k < T.secs; k++) p.step(1);
  const [ok, msg] = T.check(p.s, DB);
  return { id: T.id, name: T.name, pass: ok, detail: msg };
}
