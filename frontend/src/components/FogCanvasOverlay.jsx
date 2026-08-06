import { useEffect, useRef, useCallback } from 'react';
import { useMap } from 'react-leaflet';
import FOG_CONFIG from '../config/fogConfig';

/**
 * Safely extracts lat/lon object from various point representations.
 * Supports [lat, lon], {lat, lon}, {lat, lng}, {latitude, longitude}.
 */
const extractLatLng = (pt) => {
  if (!pt) return null;
  if (Array.isArray(pt)) {
    if (pt.length >= 2 && typeof pt[0] === 'number' && typeof pt[1] === 'number') {
      return { lat: pt[0], lon: pt[1] };
    }
    return null;
  }
  if (typeof pt === 'object') {
    const lat = pt.lat ?? pt.latitude;
    const lon = pt.lon ?? pt.lng ?? pt.longitude;
    if (typeof lat === 'number' && typeof lon === 'number') {
      return { lat, lon };
    }
  }
  return null;
};

/**
 * Pre-renders a static 256x256 noise canvas tile.
 */
const createNoiseCanvas = () => {
  const noiseCanvas = document.createElement('canvas');
  noiseCanvas.width = 256;
  noiseCanvas.height = 256;
  const ctx = noiseCanvas.getContext('2d');
  if (!ctx) return noiseCanvas;

  const imgData = ctx.createImageData(256, 256);
  const data = imgData.data;

  for (let i = 0; i < data.length; i += 4) {
    const val = Math.floor(Math.random() * 255);
    data[i] = val;     // R
    data[i + 1] = val; // G
    data[i + 2] = val; // B
    data[i + 3] = 255; // Alpha
  }

  ctx.putImageData(imgData, 0, 0);
  return noiseCanvas;
};

/**
 * FogCanvasOverlay Component
 *
 * High-performance Leaflet Canvas overlay for atmospheric Fog of War.
 * Implements two-pass mask compositing, S-curve radial feathering,
 * high-DPI support, and offscreen static noise overlay.
 */
export const FogCanvasOverlay = ({
  discoveredPoints = [],
  showFog = true,
  fogConfig = FOG_CONFIG,
}) => {
  const map = useMap();
  const canvasRef = useRef(null);
  const maskCanvasRef = useRef(null);
  const noiseCanvasRef = useRef(null);

  // Initialize offscreen noise canvas on mount
  useEffect(() => {
    noiseCanvasRef.current = createNoiseCanvas();
  }, []);

  // Main fog rendering function
  const drawFog = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !map || !showFog) return;

    const size = map.getSize();
    if (!size || size.x === 0 || size.y === 0) return;

    const dpr = window.devicePixelRatio || 1;
    const targetWidth = Math.round(size.x * dpr);
    const targetHeight = Math.round(size.y * dpr);

    // Sync main canvas dimensions
    if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
      canvas.width = targetWidth;
      canvas.height = targetHeight;
    }

    // Sync offscreen mask canvas dimensions
    if (!maskCanvasRef.current) {
      maskCanvasRef.current = document.createElement('canvas');
    }
    const maskCanvas = maskCanvasRef.current;
    if (maskCanvas.width !== targetWidth || maskCanvas.height !== targetHeight) {
      maskCanvas.width = targetWidth;
      maskCanvas.height = targetHeight;
    }

    const ctx = canvas.getContext('2d');
    const maskCtx = maskCanvas.getContext('2d');
    if (!ctx || !maskCtx) return;

    const currentConfig = fogConfig || FOG_CONFIG;
    const fogColor = currentConfig.fogColor || '#0f172a';
    const fogOpacity = currentConfig.fogOpacity ?? 0.88;
    const radiusMeters = currentConfig.discoveryRadiusMeters || 150;
    const featherWidthPx = currentConfig.edgeFeatherWidthPx ?? 40;
    const blendingMode = currentConfig.blendingMode || 'destination-out';
    const enableNoise = currentConfig.enableNoise !== false;
    const noiseOpacity = currentConfig.noiseOpacity ?? 0.045;
    const clearCenterOpacity = currentConfig.clearCenterOpacity ?? 0.0;

    // Reset scales & clear frames
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    maskCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

    ctx.clearRect(0, 0, size.x, size.y);
    maskCtx.clearRect(0, 0, size.x, size.y);

    // Pass 1a: Fill main canvas with solid atmospheric fog color
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = fogColor;
    ctx.globalAlpha = fogOpacity;
    ctx.fillRect(0, 0, size.x, size.y);
    ctx.globalAlpha = 1.0;

    // Pass 1b: Render discovery circles onto offscreen mask canvas using 'lighter'
    if (discoveredPoints && discoveredPoints.length > 0) {
      maskCtx.globalCompositeOperation = 'lighter';
      maskCtx.globalAlpha = 1.0;

      const bounds = map.getBounds();
      const centerLat = map.getCenter().lat;
      const latDelta = radiusMeters / 111320;
      const padLat = latDelta * 2;
      const padLon = (padLat / Math.cos((centerLat * Math.PI) / 180)) || padLat;

      const centerMaskAlpha = Math.max(0, Math.min(1, 1.0 - clearCenterOpacity));

      for (let i = 0; i < discoveredPoints.length; i++) {
        const coords = extractLatLng(discoveredPoints[i]);
        if (!coords) continue;

        const { lat, lon } = coords;

        // Viewport spatial culling
        if (
          lat < bounds.getSouth() - padLat ||
          lat > bounds.getNorth() + padLat ||
          lon < bounds.getWest() - padLon ||
          lon > bounds.getEast() + padLon
        ) {
          continue;
        }

        const centerPt = map.latLngToContainerPoint([lat, lon]);
        const edgePt = map.latLngToContainerPoint([lat + latDelta, lon]);
        const rPx = Math.hypot(edgePt.x - centerPt.x, edgePt.y - centerPt.y);

        if (rPx <= 0) continue;

        const feather = Math.min(featherWidthPx, rPx * 0.8);
        const rInner = Math.max(0, rPx - feather);
        const rOuter = rPx;

        const grad = maskCtx.createRadialGradient(
          centerPt.x, centerPt.y, rInner,
          centerPt.x, centerPt.y, rOuter
        );

        grad.addColorStop(0.00, `rgba(255, 255, 255, ${centerMaskAlpha})`);
        grad.addColorStop(0.25, `rgba(255, 255, 255, ${centerMaskAlpha * 0.92})`);
        grad.addColorStop(0.60, `rgba(255, 255, 255, ${centerMaskAlpha * 0.45})`);
        grad.addColorStop(0.85, `rgba(255, 255, 255, ${centerMaskAlpha * 0.15})`);
        grad.addColorStop(1.00, 'rgba(255, 255, 255, 0.00)');

        maskCtx.fillStyle = grad;
        maskCtx.beginPath();
        maskCtx.arc(centerPt.x, centerPt.y, rOuter, 0, Math.PI * 2);
        maskCtx.fill();
      }

      // Pass 1c: Single destination-out pass drawing maskCanvas onto main fog canvas
      ctx.globalCompositeOperation = blendingMode;
      ctx.globalAlpha = 1.0;
      // Use identity transform to blit mask directly 1:1
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.drawImage(maskCanvas, 0, 0);
    }

    // Pass 1d: Draw pre-rendered static 256x256 noise canvas tile using source-atop
    if (enableNoise && noiseCanvasRef.current) {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalCompositeOperation = 'source-atop';
      ctx.globalAlpha = noiseOpacity;
      const pattern = ctx.createPattern(noiseCanvasRef.current, 'repeat');
      if (pattern) {
        ctx.fillStyle = pattern;
        ctx.fillRect(0, 0, size.x, size.y);
      }
    }

    // Reset composite operation and alpha
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1.0;
  }, [map, showFog, discoveredPoints, fogConfig]);

  useEffect(() => {
    if (!showFog) return;

    drawFog();

    let animationFrameId = null;
    const handleMapEvent = () => {
      if (animationFrameId !== null) return;
      animationFrameId = requestAnimationFrame(() => {
        animationFrameId = null;
        drawFog();
      });
    };

    // Listen to end-of-move/zoom events to avoid flicker during animation
    map.on('moveend zoomend viewreset resize', handleMapEvent);

    return () => {
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId);
      }
      map.off('moveend zoomend viewreset resize', handleMapEvent);
    };
  }, [map, showFog, drawFog]);

  if (!showFog) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 400,
      }}
    />
  );
};

export default FogCanvasOverlay;
