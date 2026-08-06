export const FOG_CONFIG = {
  // Gameplay physics
  discoveryRadiusMeters: 150,
  duplicateThresholdMeters: 50,

  // Visual aesthetics
  fogColor: '#0f172a', // dark slate blue-gray
  fogOpacity: 0.88,

  // Feathering ratios (0-1 of radius)
  featherInnerRatio: 0.75, // inner 75% fully clear
  edgeFeatherWidthPx: 40, // pixel width for feathering at fog edge

  // Edge noise (optional, can be toggled)
  enableEdgeNoise: true,
  noiseAmplitudePx: 4,

  // Performance tuning
  renderThrottleMs: 16, // approx 60 FPS
  blendingMode: 'destination-out', // canvas composite mode for clearing fog
  enableNoise: true, // toggles static noise overlay
  noiseOpacity: 0.045, // opacity of static noise overlay
};

export default FOG_CONFIG;
