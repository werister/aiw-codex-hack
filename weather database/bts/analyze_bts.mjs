import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

// Input is the unmodified BTS export at airport/carrier/month level.
const dir = path.dirname(fileURLToPath(import.meta.url));
const input = path.join(dir, 'raw2025', 'Airline_Delay_Cause.csv');
const bytes = fs.readFileSync(input);
function parseCSV(text) {
  const rows = []; let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"') {
      if (quoted && text[i + 1] === '"') { field += '"'; i++; }
      else quoted = !quoted;
    } else if (ch === ',' && !quoted) { row.push(field); field = ''; }
    else if ((ch === '\r' || ch === '\n') && !quoted) {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(field); if (row.some(x => x !== '')) rows.push(row);
      row = []; field = '';
    } else field += ch;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  assert.equal(quoted, false, 'Unclosed CSV quoted field');
  return rows;
}
const [columns, ...raw] = parseCSV(bytes.toString('utf8').replace(/^\uFEFF/, ''));
const numeric = columns.slice(6);
const rows = raw.map((values, i) => {
  assert.equal(values.length, columns.length, `Row ${i + 2}: column count`);
  const row = Object.fromEntries(columns.map((key, j) => [key, values[j]]));
  for (const key of numeric) {
    if (row[key] === '') row[key] = null;
    else { row[key] = Number(row[key]); assert(Number.isFinite(row[key]), `Invalid ${key}`); }
  }
  return row;
});
assert(rows.every(r => r.year === '2025'), 'Unexpected year in downloaded export');
assert.equal(new Set(rows.map(r => r.month)).size, 12, 'Expected complete calendar year');
assert.equal(new Set(rows.map(r => `${r.year}/${r.month}/${r.carrier}/${r.airport}`)).size, rows.length, 'Duplicate aggregation keys');
const categories = ['carrier', 'weather', 'nas', 'security', 'late_aircraft'];
const nullRows = rows.filter(r => numeric.some(k => r[k] === null));
const sum = (items, key) => items.reduce((n, r) => n + (r[key] ?? 0), 0);
function aggregate(items) {
  const totals = Object.fromEntries(numeric.map(key => [key, sum(items, key)]));
  const minutesSum = categories.reduce((n, c) => n + totals[c + '_delay'], 0);
  const pct = (n, d) => d ? 100 * n / d : null;
  return {
    rows: items.length, totals, unallocated_delay_minutes: totals.arr_delay - minutesSum,
    rates: {
      delayed_arrivals_pct: pct(totals.arr_del15, totals.arr_flights),
      cancelled_pct: pct(totals.arr_cancelled, totals.arr_flights),
      diverted_pct: pct(totals.arr_diverted, totals.arr_flights),
      delay_minutes_per_scheduled_arrival: totals.arr_delay / totals.arr_flights,
      delay_minutes_per_delayed_arrival: totals.arr_delay / totals.arr_del15,
    },
    causes: Object.fromEntries(categories.map(c => [c, {
      delay_minutes: totals[c + '_delay'],
      share_of_delay_minutes_pct: pct(totals[c + '_delay'], totals.arr_delay),
      prorated_flight_equivalents: totals[c + '_ct'],
      share_of_prorated_delays_pct: pct(totals[c + '_ct'], totals.arr_del15),
      minutes_per_scheduled_arrival: totals[c + '_delay'] / totals.arr_flights,
    }]))
  };
}
const total = aggregate(rows);
assert(Math.abs(total.unallocated_delay_minutes / total.totals.arr_delay) < 0.001, 'Material cause-minute reconciliation gap: investigate before publishing');
const groups = key => [...new Set(rows.map(r => r[key]))].map(value => ({[key]:value,...aggregate(rows.filter(r => r[key] === value))}));
const monthly = groups('month').sort((a,b) => Number(a.month) - Number(b.month));
const airports = groups('airport').map(a => ({...a, name: rows.find(r => r.airport === a.airport).airport_name}));
const carriers = groups('carrier').map(a => ({...a, name: rows.find(r => r.carrier === a.carrier).carrier_name}));
const validation = {
  rows: rows.length, columns: columns.length,
  source_sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
  years: [...new Set(rows.map(r => r.year))],
  months: monthly.map(r => Number(r.month)),
  airports: airports.length, carriers: carriers.length,
  rows_with_missing_numeric_values: nullRows.length,
  missing_value_policy: 'Preserve missing values as null on import; sum available values; do not treat missing as evidence of no cause.',
  missing_rows: nullRows.slice(0,10).map(r=>({month:r.month,carrier:r.carrier,airport:r.airport,missing:numeric.filter(k=>r[k]===null)})),
  cause_minutes_minus_total_minutes: categories.reduce((n,c)=>n+total.totals[c+'_delay'],0)-total.totals.arr_delay,
  rows_with_cause_minute_mismatch: rows.filter(r=>Math.abs(categories.reduce((n,c)=>n+(r[c+'_delay']??0),0)-(r.arr_delay??0))>0.01).map(r=>({month:r.month,carrier:r.carrier,airport:r.airport,unallocated_minutes:r.arr_delay-categories.reduce((n,c)=>n+(r[c+'_delay']??0),0)})),
  prorated_cause_count_minus_delayed_count: categories.reduce((n,c)=>n+total.totals[c+'_ct'],0)-total.totals.arr_del15,
  definitions: {
    arr_del15: 'Arrivals delayed at least 15 minutes; denominator is scheduled arrivals, including cancellations/diversions.',
    arr_delay: 'Minutes attributed to delayed arrivals in this export; not all positive delays under 15 minutes.',
    cause_ct: 'Fractional flight-equivalent allocations, NOT distinct flights experiencing the cause.',
    weather: 'Explicit weather category, NOT full weather contribution across NAS and propagation.',
    no_causal_identification: 'Descriptive aggregation only; no weather-observation join or causal effect estimation.',
  }
};
const output = {validation,total,monthly,airports,carriers};
fs.writeFileSync(path.join(dir, 'analysis_results.json'), JSON.stringify(output,null,2)+'\n');
const major = airports.filter(a => a.totals.arr_flights >= 100000);
console.log(JSON.stringify({validation,total,monthly:monthly.map(m=>({month:m.month,...m.rates,weather_minutes:m.causes.weather.delay_minutes,weather_share:m.causes.weather.share_of_delay_minutes_pct,late_share:m.causes.late_aircraft.share_of_delay_minutes_pct})),majorAirports:major.sort((a,b)=>b.rates.delayed_arrivals_pct-a.rates.delayed_arrivals_pct).map(a=>({airport:a.airport,flights:a.totals.arr_flights,...a.rates,nas_share:a.causes.nas.share_of_delay_minutes_pct,weather_share:a.causes.weather.share_of_delay_minutes_pct,late_share:a.causes.late_aircraft.share_of_delay_minutes_pct}))},null,2));
