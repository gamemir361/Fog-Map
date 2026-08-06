const path = require('path');
const fs = require('fs');

const fogConfigPath = path.resolve(__dirname, '../../frontend/src/config/fogConfig.js');

console.log('--- Testing fogConfig.js Immutability and Parameters ---');

(async () => {
  const fogConfigModule = await import('file://' + fogConfigPath.replace(/\\/g, '/'));
  const FOG_CONFIG = fogConfigModule.FOG_CONFIG;
  const defaultConfig = fogConfigModule.default;

  console.log('1. Checking Exports:');
  console.log('   - FOG_CONFIG named export:', FOG_CONFIG !== undefined ? 'PASS' : 'FAIL');
  console.log('   - Default export matches FOG_CONFIG:', defaultConfig === FOG_CONFIG ? 'PASS' : 'FAIL');

  console.log('\n2. Testing Object.freeze Immutability:');
  const isFrozen = Object.isFrozen(FOG_CONFIG);
  console.log('   - Object.isFrozen(FOG_CONFIG):', isFrozen ? 'PASS (true)' : 'FAIL (false)');

  // Test mutation in non-strict mode: value must NOT change
  const origRadius = FOG_CONFIG.discoveryRadiusMeters;
  FOG_CONFIG.discoveryRadiusMeters = 999;
  const valueUnchangedNonStrict = FOG_CONFIG.discoveryRadiusMeters === origRadius;
  console.log('   - Non-strict mutation attempt ignored (value remains 150):', valueUnchangedNonStrict ? 'PASS' : 'FAIL');

  // Test property addition in non-strict mode: property must NOT be added
  FOG_CONFIG.newProp = 'illegal';
  const propNotAdded = FOG_CONFIG.newProp === undefined;
  console.log('   - Non-strict addition attempt ignored (property not added):', propNotAdded ? 'PASS' : 'FAIL');

  // Test deletion in non-strict mode: property must NOT be deleted
  delete FOG_CONFIG.fogColor;
  const colorNotDeleted = FOG_CONFIG.fogColor === '#0f172a';
  console.log('   - Non-strict deletion attempt ignored (property retained):', colorNotDeleted ? 'PASS' : 'FAIL');

  // Test mutation in strict mode function
  let strictMutationThrew = false;
  let strictAddThrew = false;
  let strictDeleteThrew = false;

  const testStrictMutation = () => {
    'use strict';
    FOG_CONFIG.discoveryRadiusMeters = 999;
  };
  const testStrictAdd = () => {
    'use strict';
    FOG_CONFIG.newProp = 'illegal';
  };
  const testStrictDelete = () => {
    'use strict';
    delete FOG_CONFIG.fogColor;
  };

  try { testStrictMutation(); } catch (e) { strictMutationThrew = true; }
  try { testStrictAdd(); } catch (e) { strictAddThrew = true; }
  try { testStrictDelete(); } catch (e) { strictDeleteThrew = true; }

  console.log('   - Strict mode mutation throws TypeError:', strictMutationThrew ? 'PASS' : 'FAIL');
  console.log('   - Strict mode addition throws TypeError:', strictAddThrew ? 'PASS' : 'FAIL');
  console.log('   - Strict mode deletion throws TypeError:', strictDeleteThrew ? 'PASS' : 'FAIL');

  const immutabilityPass = isFrozen && valueUnchangedNonStrict && propNotAdded && colorNotDeleted && strictMutationThrew && strictAddThrew && strictDeleteThrew;
  console.log('   - Overall Object.freeze Immutability Status:', immutabilityPass ? 'PASS' : 'FAIL');

  console.log('\n3. Testing Parameter Values Against Specification Limits:');
  const specLimits = {
    discoveryRadiusMeters: { expected: 150, check: (v) => typeof v === 'number' && v === 150 },
    duplicateThresholdMeters: { expected: 50, check: (v) => typeof v === 'number' && v === 50 },
    fogColor: { expected: '#0f172a', check: (v) => /^#[0-9a-fA-F]{6}$/.test(v) && v.toLowerCase() === '#0f172a' },
    fogOpacity: { expected: 0.88, check: (v) => typeof v === 'number' && v >= 0 && v <= 1 && v === 0.88 },
    clearCenterOpacity: { expected: 0.0, check: (v) => typeof v === 'number' && v === 0.0 },
    edgeFeatherWidthPx: { expected: '30-50px (40)', check: (v) => typeof v === 'number' && v >= 30 && v <= 50 && v === 40 },
    blendingMode: { expected: 'destination-out', check: (v) => typeof v === 'string' && v === 'destination-out' },
    enableNoise: { expected: true, check: (v) => typeof v === 'boolean' && v === true },
    noiseOpacity: { expected: 0.045, check: (v) => typeof v === 'number' && v >= 0 && v <= 1 && v === 0.045 },
  };

  let allParamsPass = true;
  for (const [key, spec] of Object.entries(specLimits)) {
    const val = FOG_CONFIG[key];
    const pass = spec.check(val);
    if (!pass) allParamsPass = false;
    console.log(`   - ${key}: value=${val}, expected=${spec.expected} -> ${pass ? 'PASS' : 'FAIL'}`);
  }

  console.log('\nOverall Immutability & Parameter Test Result:', immutabilityPass && allParamsPass ? 'ALL PASSED' : 'FAILED');
})();
