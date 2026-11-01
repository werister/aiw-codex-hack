import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { buildTrafficPlan, sampleFlight } from "./airport-traffic.ts";

const manifest = JSON.parse(readFileSync(
  new URL("../../public/models/airport/manifest.json", import.meta.url),
  "utf8",
));
const roles = ["arrive_north", "arrive_south", "depart_center", "depart_flex"];
const states = [
  { od: "25", r18Open: true },
  { od: "07", r18Open: true },
  { od: "25", r18Open: false },
  { od: "07", r18Open: false },
];

function closePoint(actual, expected, tolerance = 1e-3) {
  for (let axis = 0; axis < 3; axis += 1) {
    assert.ok(
      Math.abs(actual[axis] - expected[axis]) <= tolerance,
      "axis " + axis + ": " + actual[axis] + " != " + expected[axis],
    );
  }
}

function distance(a, b) {
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
}

test("runtime routes match all authored Blender waypoint fixtures", () => {
  for (const fixture of manifest.demonstration_phases) {
    const plan = buildTrafficPlan(manifest, {
      od: fixture.od,
      r18Open: fixture.runway_18_usable,
    });
    for (const role of roles) {
      assert.equal(plan.routes[role].length, fixture.paths[role].length, role);
      plan.routes[role].forEach((point, index) => closePoint(point, fixture.paths[role][index]));
    }
  }
});

test("both OD choices reverse all parallel runway arrival and centre-departure flows", () => {
  const parallel = [Math.sin((manifest.runways.center.heading * Math.PI) / 180),
    Math.cos((manifest.runways.center.heading * Math.PI) / 180)];
  for (const od of ["25", "07"]) {
    const direction = od === "07" ? 1 : -1;
    const plan = buildTrafficPlan(manifest, { od, r18Open: true });
    for (const role of ["arrive_north", "arrive_south", "depart_center"]) {
      const tangent = sampleFlight(plan, role, 0.999).tangent;
      assert.ok(tangent[0] * parallel[0] * direction > 0, role + " x follows OD " + od);
      assert.ok(tangent[1] * parallel[1] * direction > 0, role + " y follows OD " + od);
    }
  }
});

test("Runway 18 remains a southbound departure in either open state", () => {
  for (const od of ["25", "07"]) {
    const plan = buildTrafficPlan(manifest, { od, r18Open: true });
    const tangent = sampleFlight(plan, "depart_flex", 0.999).tangent;
    assert.ok(tangent[1] < 0, "Runway 18 course stays southbound for OD " + od);
    assert.ok(Math.abs(tangent[0]) < 0.1);
  }
});

test("closure diverts the flexible departure to the selected centre-runway direction", () => {
  for (const od of ["25", "07"]) {
    const direction = od === "07" ? 1 : -1;
    const plan = buildTrafficPlan(manifest, { od, r18Open: false });
    const centre = plan.routes.depart_center;
    const diverted = plan.routes.depart_flex;
    assert.deepEqual(diverted.slice(-3, -1), centre.slice(-3, -1));
    assert.equal(diverted.at(-1)[2] < 40, true);
    const tangent = sampleFlight(plan, "depart_flex", 0.999).tangent;
    const along = [Math.sin((manifest.runways.center.heading * Math.PI) / 180),
      Math.cos((manifest.runways.center.heading * Math.PI) / 180)];
    assert.ok(tangent[0] * along[0] * direction > 0);
    assert.ok(tangent[1] * along[1] * direction > 0);
  }
});

test("closed-runway departure is queued until the first centre departure clears", () => {
  const plan = buildTrafficPlan(manifest, { od: "25", r18Open: false });
  const first = plan.timing.depart_center;
  const queued = plan.timing.depart_flex;
  assert.ok(first.finish < queued.start);
  assert.equal(sampleFlight(plan, "depart_center", first.finish).progress, 1);
  assert.equal(sampleFlight(plan, "depart_flex", queued.start).progress, 0);
  closePoint(
    sampleFlight(plan, "depart_flex", queued.start - 0.001).position,
    plan.routes.depart_flex[0],
  );
  assert.ok(sampleFlight(plan, "depart_flex", queued.start + 0.01).progress > 0);
});

test("all routes reach their end points and hold before and after their time slot", () => {
  for (const state of states) {
    const plan = buildTrafficPlan(manifest, state);
    for (const role of roles) {
      const timing = plan.timing[role];
      closePoint(sampleFlight(plan, role, 0).position, plan.routes[role][0]);
      closePoint(sampleFlight(plan, role, 1).position, plan.routes[role].at(-1));
      closePoint(sampleFlight(plan, role, timing.start - 0.01).position, plan.routes[role][0]);
      closePoint(sampleFlight(plan, role, timing.finish + 0.01).position, plan.routes[role].at(-1));
      assert.equal(sampleFlight(plan, role, 1).progress, 1);
    }
  }
});

test("arc-length sampling stays finite, normalized and continuous across all states", () => {
  for (const state of states) {
    const plan = buildTrafficPlan(manifest, state);
    for (const role of roles) {
      let previous = sampleFlight(plan, role, 0);
      for (let step = 1; step <= 10000; step += 1) {
        const current = sampleFlight(plan, role, step / 10000);
        assert.ok([...current.position, ...current.tangent, current.progress].every(Number.isFinite));
        assert.ok(Math.abs(Math.hypot(...current.tangent) - 1) < 1e-8);
        assert.ok(distance(current.position, previous.position) < 0.5, role + " position jump at " + step);
        const tangentDot = current.tangent.reduce((sum, value, axis) => sum + value * previous.tangent[axis], 0);
        assert.ok(tangentDot > 0.98, role + " tangent jump at " + step);
        previous = current;
      }
    }
  }
});

test("all four visible aircraft stay separated throughout each scenario", () => {
  for (const state of states) {
    const plan = buildTrafficPlan(manifest, state);
    for (let step = 0; step <= 1000; step += 1) {
      const positions = roles.map((role) => sampleFlight(plan, role, step / 1000).position);
      for (let a = 0; a < positions.length; a += 1) {
        for (let b = a + 1; b < positions.length; b += 1) {
          assert.ok(distance(positions[a], positions[b]) >= 20,
            "flight centres overlap at " + step / 1000 + ": " + roles[a] + "/" + roles[b]);
        }
      }
    }
  }
});

test("manifest timing supports 25/07 with both open and closed runway 18 states", () => {
  for (const state of states) {
    const plan = buildTrafficPlan(manifest, state);
    assert.deepEqual(Object.keys(plan.routes).sort(), [...roles].sort());
    assert.deepEqual(Object.keys(plan.timing).sort(), [...roles].sort());
    for (const timing of Object.values(plan.timing)) {
      assert.ok(timing.start >= 0 && timing.start < timing.finish && timing.finish <= 1);
    }
  }
});
