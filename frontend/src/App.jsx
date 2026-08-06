import { useState, useEffect, useMemo, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap, Polyline } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import 'leaflet.heat'
import axios from 'axios'
import FOG_CONFIG from './config/fogConfig'
import FogCanvasOverlay from './components/FogCanvasOverlay'
import AuthModal from './components/AuthModal'
import LandingPage from './components/LandingPage'
import TrackingConfirmModal from './components/TrackingConfirmModal'

// 🗺️ Map Clicker Component for Fog Discovery & Location Pick (Extracted outside App)
function MapClicker({ pickingLocationFor, onSelectOrigin, onSelectDest, onDiscoverPoint }) {
  useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng
      if (pickingLocationFor === 'origin') {
        onSelectOrigin(lat, lng)
        return
      }
      if (pickingLocationFor === 'dest') {
        onSelectDest(lat, lng)
        return
      }
      onDiscoverPoint(lat, lng)
    }
  })
  return null
}


// Category styling
const CATEGORY_COLORS = {
  culture: '#a855f7',
  nature: '#10b981',
  energy: '#f59e0b',
  quiet: '#38bdf8',
  photography: '#ec4899',
  nightlife: '#6366f1',
  direct: '#38bdf8',
  default: '#38bdf8',
}

const CATEGORY_ICONS = {
  culture: '🏛️',
  nature: '🌿',
  energy: '⚡',
  quiet: '☕',
  photography: '📸',
  nightlife: '🌌',
  direct: '🧭',
  default: '📍',
}

// 🎨 Sleek Category Markers (Unknown vs Discovered)
function createCustomCategoryIcon(category, matchPercentage = null, isDiscovered = true, justDiscovered = false) {
  if (!isDiscovered || category === 'unknown') {
    const unknownHtml = `
      <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 34px; height: 34px; cursor: pointer;">
        <div style="position: absolute; width: 34px; height: 34px; border-radius: 50%; background: rgba(167, 139, 250, 0.25); animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
        <div style="width: 28px; height: 28px; background: linear-gradient(135deg, #4c1d95, #6d28d9); border: 2px solid #a78bfa; border-radius: 50%; box-shadow: 0 0 14px rgba(167, 139, 250, 0.8); display: flex; align-items: center; justify-content: center; transition: all 0.3s ease;">
          <span style="font-size: 14px; color: #f5f3ff; font-weight: 900;">❓</span>
        </div>
      </div>
    `
    return L.divIcon({
      html: unknownHtml,
      className: 'custom-poi-marker unknown-poi-marker',
      iconSize: [34, 34],
      iconAnchor: [17, 17],
      popupAnchor: [0, -18],
    })
  }

  const color = CATEGORY_COLORS[category] || CATEGORY_COLORS.default
  const emoji = CATEGORY_ICONS[category] || CATEGORY_ICONS.default
  const badgeHtml = matchPercentage
    ? `<div style="position: absolute; top: -14px; right: -12px; background: linear-gradient(135deg, #ec4899, #8b5cf6); color: #fff; font-size: 9px; font-weight: 800; padding: 2px 6px; border-radius: 10px; border: 1.5px solid #fff; white-space: nowrap; box-shadow: 0 2px 8px rgba(0,0,0,0.3); z-index: 10;">✨ ${matchPercentage}٪</div>`
    : ''

  const animClass = justDiscovered ? 'poi-discover-animated' : ''

  const svgHtml = `
    <div className="${animClass}" style="position: relative; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; cursor: pointer;">
      ${badgeHtml}
      <div style="width: 28px; height: 28px; background: ${color}; border: 2px solid #ffffff; border-radius: 50%; box-shadow: 0 4px 12px rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;">
        <span style="font-size: 13px; line-height: 1; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.4));">${emoji}</span>
      </div>
    </div>
  `

  return L.divIcon({
    html: svgHtml,
    className: `custom-poi-marker ${animClass}`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  })
}

// 🌡️ Heatmap Layer using leaflet.heat
function HeatLayer({ points, enabled }) {
  const map = useMap()
  useEffect(() => {
    if (!enabled || !points || points.length === 0) return
    const layer = L.heatLayer(points, {
      radius: 35,
      blur: 25,
      maxZoom: 17,
      gradient: { 0.0: 'blue', 0.3: 'lime', 0.6: 'yellow', 1.0: 'red' }
    })
    layer.addTo(map)
    return () => map.removeLayer(layer)
  }, [map, points, enabled])
  return null
}

// ✈️ Map FlyTo Helper
function MapFlyTo({ center }) {
  const map = useMap()
  useEffect(() => {
    if (center) {
      map.flyTo(center, 15, { animate: true, duration: 1.2 })
    }
  }, [center, map])
  return null
}

function App() {
  const tehranPosition = [35.7127, 51.4069]
  const [pois, setPois] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')

  // Search States (Unified POI + Streets)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState('pois') // 'pois' | 'streets'
  const [searchResults, setSearchResults] = useState([])
  const [streetResults, setStreetResults] = useState([])
  const [flyToCoords, setFlyToCoords] = useState(null)

  // User & Auth & Fog States
  const [currentUser, setCurrentUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authModalMode, setAuthModalMode] = useState('login')
  const [score, setScore] = useState(0)
  const [userProfile, setUserProfile] = useState(null)
  const [fogStats, setFogStats] = useState(null)
  const [message, setMessage] = useState("در نقشه کاوش کنید و مه‌جنگ را کنار بزنید...")
  const [discoveredPoints, setDiscoveredPoints] = useState([])
  const [routeCoords, setRouteCoords] = useState([])
  const [routeWaypoints, setRouteWaypoints] = useState([])
  const [routeMetrics, setRouteMetrics] = useState(null)

  // Architecture Settings & UI Controls
  const [explorationTrackingEnabled, setExplorationTrackingEnabled] = useState(true)
  const [showFog, setShowFog] = useState(true)
  const [trackingConfirmModalOpen, setTrackingConfirmModalOpen] = useState(false)
  const [isBusy, setIsBusy] = useState(false)
  const [error, setError] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [appTheme, setAppTheme] = useState('dark')
  const [showHeatmap, setShowHeatmap] = useState(false)
  const [mapTheme, setMapTheme] = useState('google')

  // Dual Routing States
  const [originInput, setOriginInput] = useState('')
  const [destInput, setDestInput] = useState('')
  const [originCoords, setOriginCoords] = useState([35.6997, 51.3347])
  const [destCoords, setDestCoords] = useState(null)
  const [selectedMood, setSelectedMood] = useState('direct')
  const [pickingLocationFor, setPickingLocationFor] = useState(null)

  const themeUrls = {
    google: "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    satellite: "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    carto_dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  }

  // ==========================================
  // API Fetching & Initial Load
  // ==========================================
  const fetchPois = useCallback(async (cat = selectedCategory, search = searchQuery) => {
    await Promise.resolve()
    setIsBusy(true)
    setError('')
    try {
      let url = `/api/v1/exploration/pois?limit=150`
      if (cat && cat !== 'all') url += `&category=${cat}`
      if (search && search.trim() && searchMode === 'pois') url += `&search=${encodeURIComponent(search.trim())}`

      const response = await axios.get(url)
      setPois(response.data)
      setMessage(`تعداد ${response.data.length} مکان روی نقشه بارگذاری شد.`)
    } catch (err) {
      console.error("Error fetching POIs:", err)
      setError("خطا در دریافت مکان‌ها")
    } finally {
      setIsBusy(false)
    }
  }, [selectedCategory, searchQuery, searchMode])

  const fetchRecommendations = async () => {
    setIsBusy(true)
    setError('')
    try {
      const response = await axios.get('/api/v1/exploration/pois/recommended?limit=10')
      setPois(response.data)
      setMessage("✨ ۱۰ پیشنهاد اختصاصی بر اساس بردار سلیقه شما پیدا شد!")
    } catch (err) {
      console.error("Error fetching recommendations:", err)
      setError("امکان دریافت پیشنهادها وجود ندارد.")
    } finally {
      setIsBusy(false)
    }
  }

  const fetchUserProfile = useCallback(async () => {
    try {
      const response = await axios.get('/api/v1/missions/profile')
      setUserProfile(response.data)
    } catch (err) {
      console.error("Error fetching profile:", err)
    }
  }, [])

  const fetchFogStats = useCallback(async () => {
    try {
      const response = await axios.get('/api/v1/fog/stats')
      setFogStats(response.data)
      const points = response.data?.all_points || response.data?.data?.all_points
      if (points && points.length > 0) {
        setDiscoveredPoints(points)
      } else {
        setDiscoveredPoints([])
      }
    } catch (err) {
      console.error("Error fetching fog stats:", err)
    }
  }, [])

  const handleLogout = async () => {
    try {
      await axios.post('/api/v1/auth/logout')
    } catch (e) {
      // ignore error
    }
    localStorage.removeItem('auth_token')
    delete axios.defaults.headers.common['Authorization']
    setCurrentUser(null)
    setIsAuthenticated(false)
    setUserProfile(null)
    setFogStats(null)
    setDiscoveredPoints([])
    setScore(0)
    setMessage("از حساب کاربری خارج شدید. 🚪")
  }

  const fetchUserSettings = useCallback(async () => {
    try {
      const res = await axios.get('/api/v1/users/settings')
      if (res.data) {
        if (res.data.exploration_tracking_enabled !== undefined) {
          setExplorationTrackingEnabled(res.data.exploration_tracking_enabled)
        }
        if (res.data.show_fog !== undefined) {
          setShowFog(res.data.show_fog)
        }
      }
    } catch (err) {
      console.error("Error fetching user settings:", err)
    }
  }, [])

  const handleToggleTracking = (newValue) => {
    if (newValue === false) {
      setTrackingConfirmModalOpen(true)
    } else {
      updateTrackingSetting(true)
    }
  }

  const updateTrackingSetting = async (enabled) => {
    setExplorationTrackingEnabled(enabled)
    try {
      await axios.patch('/api/v1/users/settings', { exploration_tracking_enabled: enabled })
    } catch (err) {
      console.error("Failed to update tracking setting:", err)
    }
  }

  const handleToggleShowFog = async (newValue) => {
    setShowFog(newValue)
    try {
      await axios.patch('/api/v1/users/settings', { show_fog: newValue })
    } catch (err) {
      console.error("Failed to update show_fog setting:", err)
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      axios.get('/api/v1/auth/me')
        .then(res => {
          setCurrentUser(res.data)
          setIsAuthenticated(true)
          if (res.data.exploration_tracking_enabled !== undefined) {
            setExplorationTrackingEnabled(res.data.exploration_tracking_enabled)
          }
          if (res.data.show_fog !== undefined) {
            setShowFog(res.data.show_fog)
          }
        })
        .catch(() => {
          localStorage.removeItem('auth_token')
          delete axios.defaults.headers.common['Authorization']
          setCurrentUser(null)
          setIsAuthenticated(false)
        })
        .finally(() => {
          setIsInitializing(false)
        })
    } else {
      setIsAuthenticated(false)
      setIsInitializing(false)
    }
  }, [])

  useEffect(() => {
    if (isAuthenticated) {
      fetchPois('all', '')
      fetchUserProfile()
      fetchFogStats()
      fetchUserSettings()
    }
  }, [isAuthenticated, fetchPois, fetchUserProfile, fetchFogStats, fetchUserSettings])

  // Auto-complete Search (POIs vs OpenStreetMap Streets)
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      return
    }

    if (searchMode === 'pois') {
      const filtered = pois.filter(p => p.name.includes(searchQuery) || (p.description && p.description.includes(searchQuery)))
      setSearchResults(filtered.slice(0, 5))
      setStreetResults([])
    } else {
      const timer = setTimeout(async () => {
        try {
          const resp = await axios.get('https://nominatim.openstreetmap.org/search', {
            params: {
              q: searchQuery + ' تهران',
              format: 'json',
              addressdetails: 1,
              limit: 5,
              'accept-language': 'fa',
            }
          })
          setStreetResults(resp.data || [])
          setSearchResults([])
        } catch (err) {
          console.error("Street search error:", err)
        }
      }, 350)
      return () => clearTimeout(timer)
    }
  }, [searchQuery, searchMode, pois])

  // Handlers for MapClicker
  const handleSelectOrigin = useCallback((lat, lng) => {
    setOriginCoords([lat, lng])
    setOriginInput(`موقعیت انتخابی (${lat.toFixed(3)}, ${lng.toFixed(3)})`)
    setPickingLocationFor(null)
    setMessage("📍 مبدأ مسیریابی تنظیم شد.")
  }, [])

  const handleSelectDest = useCallback((lat, lng) => {
    setDestCoords([lat, lng])
    setDestInput(`موقعیت انتخابی (${lat.toFixed(3)}, ${lng.toFixed(3)})`)
    setPickingLocationFor(null)
    setMessage("🎯 مقصد مسیریابی تنظیم شد.")
  }, [])

  const handleDiscoverPoint = useCallback(async (lat, lng) => {
    if (!explorationTrackingEnabled) {
      setMessage("ردیابی کاوش غیرفعال است. هیچ منطقه یا امتیازی ثبت نشد.")
      return
    }
    setIsBusy(true)
    try {
      const res = await axios.post('/api/v1/exploration/fog/discover', { user_id: currentUser?.id || 1, lat, lon: lng })
      if (res.data.status === 'paused') {
        setMessage("ردیابی کاوش غیرفعال است.")
        return
      }
      if (res.data.xp_feedback) {
        const fb = res.data.xp_feedback
        if (fb.level_up) {
          setMessage(`🎉 ارتقا سطح! شما به لول ${fb.new_level} رسیدید! 🌟`)
        } else if (fb.badge && fb.badge !== '+0 XP') {
          setMessage(`✨ ${fb.badge} • ${fb.reason}`)
        } else {
          setMessage(res.data.message || "منطقه جدید کشف شد!")
        }
      } else {
        setMessage(res.data.message || "منطقه جدید کشف شد!")
      }

      const points = res.data.data?.all_points || res.data.all_points
      const currentPts = res.data.data?.current_points ?? res.data.current_points

      if (currentPts !== undefined) setScore(currentPts)
      if (points && points.length > 0) {
        setDiscoveredPoints(points)
      } else {
        setDiscoveredPoints(prev => [...prev, { lat, lon: lng }])
      }

      fetchUserProfile()
      fetchFogStats()
      fetchPois()
    } catch (error) {
      console.error("Error in fog discover:", error)
      setDiscoveredPoints(prev => [...prev, { lat, lon: lng }])
      setMessage("منطقه کشف شد! 🧭")
    } finally {
      setIsBusy(false)
    }
  }, [fetchUserProfile, fetchFogStats, currentUser, explorationTrackingEnabled])

  // Route Planning Handler
  const handleDualPlanRoute = async () => {
    if (!originCoords) {
      setError("لطفاً مبدأ را مشخص کنید.")
      return
    }

    setIsBusy(true)
    setError('')
    try {
      const payload = {
        origin_lat: originCoords[0],
        origin_lon: originCoords[1],
        mood: selectedMood,
      }
      if (destCoords) {
        payload.dest_lat = destCoords[0]
        payload.dest_lon = destCoords[1]
      }

      const response = await axios.post('/api/v1/routes/dual-plan', payload)
      const data = response.data

      if (data.status === 'success') {
        setRouteCoords(data.route_coordinates || [])
        setRouteWaypoints(data.waypoints || [])
        setRouteMetrics({
          distance: data.distance_meters,
          duration: data.duration_seconds,
        })
        setMessage(data.message)
      } else {
        setError(data.message || "خطا در مسیریابی")
      }
    } catch (err) {
      console.error("Error planning route:", err)
      setError("سرویس مسیریابی در دسترس نیست.")
    } finally {
      setIsBusy(false)
    }
  }

  const heatPoints = useMemo(() => {
    return discoveredPoints.map(pt => {
      const lat = Array.isArray(pt) ? pt[0] : pt.lat
      const lon = Array.isArray(pt) ? pt[1] : pt.lon
      return [lat, lon, 0.8]
    })
  }, [discoveredPoints])

  if (isInitializing) {
    return (
      <div style={{ width: '100vw', height: '100vh', background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8', fontFamily: 'Vazirmatn' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '36px', marginBottom: '12px' }}>🧭</div>
          <div style={{ fontSize: '14px', fontWeight: 700 }}>در حال بررسی نشست کاربری...</div>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <>
        <LandingPage
          onOpenLogin={() => {
            setAuthModalMode('login')
            setAuthModalOpen(true)
          }}
          onOpenRegister={() => {
            setAuthModalMode('register')
            setAuthModalOpen(true)
          }}
        />
        <AuthModal
          isOpen={authModalOpen}
          initialMode={authModalMode}
          onClose={() => setAuthModalOpen(false)}
          onAuthSuccess={(user) => {
            setCurrentUser(user)
            setIsAuthenticated(true)
            setMessage(`خوش آمدید ${user.username} عزیز! 🌟`)
          }}
        />
      </>
    )
  }

  return (
    <div data-theme={appTheme} style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden' }}>

      {/* 🟢 NESHAN FLOATING TOP BAR (Search + Mode Selector + Categories) */}
      <div style={{ position: 'absolute', top: '16px', right: '16px', left: '16px', zIndex: 1000, display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '580px', margin: '0 auto' }}>

        {/* Unified Search Box */}
        <div className="glass-panel" style={{ padding: '8px 14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '18px' }}>🔍</span>

          {/* Search Mode Toggle */}
          <div style={{ display: 'flex', background: 'rgba(125, 125, 125, 0.15)', borderRadius: '8px', padding: '2px' }}>
            <button
              onClick={() => setSearchMode('pois')}
              style={{
                background: searchMode === 'pois' ? '#38bdf8' : 'transparent',
                color: searchMode === 'pois' ? '#fff' : 'var(--text-main)',
                border: 'none',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
              }}>
              📍 اماکن
            </button>
            <button
              onClick={() => setSearchMode('streets')}
              style={{
                background: searchMode === 'streets' ? '#38bdf8' : 'transparent',
                color: searchMode === 'streets' ? '#fff' : 'var(--text-main)',
                border: 'none',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
              }}>
              🛣️ معابر
            </button>
          </div>

          {/* Search Input */}
          <input
            type="text"
            placeholder={searchMode === 'pois' ? "جستجوی مکان‌ها (برج آزادی، گلستان...)" : "جستجوی خیابان و معابر (ولیعصر، انقلاب...)"}
            value={searchQuery}
            onChange={(e) => {
              const val = e.target.value
              setSearchQuery(val)
              if (!val.trim() || val.trim().length < 2) {
                setSearchResults([])
                setStreetResults([])
              }
            }}
            onKeyDown={(e) => e.key === 'Enter' && fetchPois(selectedCategory, searchQuery)}
            style={{ flex: 1, background: 'transparent', border: 'none', color: 'var(--text-main)', fontSize: '13px', outline: 'none', fontFamily: 'Vazirmatn' }}
          />

          {searchQuery && (
            <button onClick={() => setSearchQuery('')} style={{ background: 'none', border: 'none', color: 'var(--text-sub)', cursor: 'pointer', fontSize: '14px' }}>
              ✕
            </button>
          )}

          {/* Drawer Toggle Hamburger Button */}
          <button
            onClick={() => setDrawerOpen(!drawerOpen)}
            style={{
              background: drawerOpen ? 'linear-gradient(135deg, #a855f7, #6366f1)' : 'rgba(125,125,125,0.2)',
              border: '1px solid var(--panel-border)',
              color: 'var(--text-main)',
              padding: '6px 12px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: 800,
              fontSize: '15px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}>
            ☰
          </button>
        </div>

        {/* POI Search Results Dropdown */}
        {searchResults.length > 0 && (
          <div className="glass-panel" style={{ padding: '6px 0', maxHeight: '200px', overflowY: 'auto' }}>
            {searchResults.map((poi) => (
              <div
                key={poi.id}
                onClick={() => {
                  setSearchQuery(poi.name)
                  setSearchResults([])
                  setFlyToCoords([poi.lat, poi.lon])
                }}
                style={{ padding: '8px 16px', cursor: 'pointer', borderBottom: '1px solid var(--panel-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-main)' }}>{CATEGORY_ICONS[poi.category] || '📍'} {poi.name}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-sub)' }}>{poi.category}</span>
              </div>
            ))}
          </div>
        )}

        {/* Street Search Results Dropdown (Nominatim) */}
        {streetResults.length > 0 && (
          <div className="glass-panel" style={{ padding: '6px 0', maxHeight: '200px', overflowY: 'auto' }}>
            {streetResults.map((item, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setSearchQuery(item.display_name.split(',')[0])
                  setStreetResults([])
                  setFlyToCoords([parseFloat(item.lat), parseFloat(item.lon)])
                  setMessage(`نقشه به محدوده '${item.display_name.split(',')[0]}' هدایت شد.`)
                }}
                style={{ padding: '8px 16px', cursor: 'pointer', borderBottom: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ fontWeight: 600, fontSize: '13px', color: '#38bdf8' }}>🛣️ {item.display_name.split(',')[0]}</span>
                <span style={{ fontSize: '10px', color: 'var(--text-sub)' }}>{item.display_name}</span>
              </div>
            ))}
          </div>
        )}

        {/* Horizontal Category Pills Bar (Neshan Style) */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
          {[
            { id: 'all', name: 'همه', icon: '🌐' },
            { id: 'unknown', name: 'ناشناخته', icon: '❓' },
            { id: 'nature', name: 'طبیعت', icon: '🌿' },
            { id: 'culture', name: 'تاریخ', icon: '🏛️' },
            { id: 'quiet', name: 'کافه', icon: '☕' },
            { id: 'energy', name: 'بازار', icon: '⚡' },
            { id: 'photography', name: 'عکاسی', icon: '📸' },
            { id: 'nightlife', name: 'شب‌گردی', icon: '🌌' },
          ].map(cat => (
            <button
              key={cat.id}
              onClick={() => {
                setSelectedCategory(cat.id)
                fetchPois(cat.id, searchQuery)
              }}
              style={{
                background: selectedCategory === cat.id ? 'linear-gradient(135deg, #38bdf8, #8b5cf6)' : 'var(--panel-glass)',
                backdropFilter: 'blur(10px)',
                border: '1px solid var(--panel-border)',
                color: selectedCategory === cat.id ? '#fff' : 'var(--text-main)',
                padding: '5px 12px',
                borderRadius: '16px',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: 600,
                whiteSpace: 'nowrap',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}>
              <span>{cat.icon}</span> {cat.name}
            </button>
          ))}

          <button
            onClick={fetchRecommendations}
            style={{
              background: 'linear-gradient(135deg, #ec4899, #f59e0b)',
              border: 'none',
              color: '#fff',
              padding: '5px 12px',
              borderRadius: '16px',
              cursor: 'pointer',
              fontSize: '11px',
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}>
            ✨ پیشنهاد هوشمند
          </button>
        </div>
      </div>

      {/* 🔴 NESHAN RIGHT COLLAPSIBLE TOOLBAR DRAWER */}
      {drawerOpen && (
        <div
          className="glass-panel slide-in-right"
          style={{
            position: 'absolute',
            top: '0',
            right: '0',
            bottom: '0',
            width: '340px',
            zIndex: 2000,
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            overflowY: 'auto',
            borderRadius: '16px 0 0 16px',
            borderLeft: '1px solid var(--panel-border)',
          }}>

          {/* Drawer Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--panel-border)', paddingBottom: '12px' }}>
            <span style={{ fontWeight: 800, fontSize: '15px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px' }}>
              🛠️ ابزارها و داشبورد کاشف
            </span>
            <button onClick={() => setDrawerOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-sub)', cursor: 'pointer', fontSize: '18px' }}>
              ✕
            </button>
          </div>

          {/* Section 1: User Profile & Authentication */}
          <div style={{ background: 'rgba(125,125,125,0.1)', padding: '12px', borderRadius: '12px', border: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {currentUser ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, fontSize: '13px', color: '#38bdf8' }}>👤 {currentUser.username}</span>
                  <span style={{ background: '#a855f7', color: '#fff', fontSize: '10px', fontWeight: 800, padding: '2px 8px', borderRadius: '10px' }}>
                    سطح {userProfile?.level_stats?.level || 1}
                  </span>
                </div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(125,125,125,0.2)', borderRadius: '3px', overflow: 'hidden', margin: '4px 0' }}>
                  <div style={{ width: `${userProfile?.level_stats?.progress_pct || 0}%`, height: '100%', background: 'linear-gradient(90deg, #38bdf8, #a855f7)' }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-sub)' }}>
                  <span>XP کل: {userProfile?.score || score || 0}</span>
                  <span>پیشرفت: {userProfile?.level_stats?.progress_pct || 0}٪</span>
                </div>
                <button
                  onClick={handleLogout}
                  style={{
                    marginTop: '4px',
                    background: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#ef4444',
                    padding: '6px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}>
                  🚪 خروج از حساب کاربری
                </button>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '4px 0' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-sub)', display: 'block', marginBottom: '8px' }}>
                  برای ذخیره کاوش‌ها و امتیازات خود وارد حساب شوید.
                </span>
                <button
                  onClick={() => setAuthModalOpen(true)}
                  style={{
                    width: '100%',
                    background: 'linear-gradient(135deg, #38bdf8, #8b5cf6)',
                    color: '#fff',
                    border: 'none',
                    padding: '8px 14px',
                    borderRadius: '10px',
                    fontWeight: 800,
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}>
                  🔑 ورود / ثبت‌نام کاربر
                </button>
              </div>
            )}
          </div>

          {/* Section 2: PostGIS Fog Statistics */}
          {fogStats && (
            <div style={{ background: 'rgba(125,125,125,0.1)', padding: '12px', borderRadius: '12px', border: '1px solid var(--panel-border)' }}>
              <span style={{ fontWeight: 700, fontSize: '11px', color: '#10b981', display: 'block', marginBottom: '6px' }}>📊 آمار پوشش مه‌جنگ</span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px' }}>
                <div style={{ background: 'rgba(125,125,125,0.1)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ color: 'var(--text-sub)', fontSize: '9px' }}>مساحت کشف‌شده</div>
                  <div style={{ fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>{fogStats.covered_area_sq_km || fogStats.total_area_sqkm || (discoveredPoints.length * 0.2).toFixed(1)} km²</div>
                </div>
                <div style={{ background: 'rgba(125,125,125,0.1)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ color: 'var(--text-sub)', fontSize: '9px' }}>پوشش پایتخت</div>
                  <div style={{ fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>{fogStats.coverage_percentage_of_tehran || fogStats.city_coverage_percentage || 0}٪</div>
                </div>
              </div>
            </div>
          )}

          {/* Section 3: Dual Routing Panel */}
          <div style={{ background: 'rgba(125,125,125,0.1)', padding: '12px', borderRadius: '12px', border: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <span style={{ fontWeight: 700, fontSize: '12px', color: '#ec4899' }}>🧭 مسیریابی دوگانه A به B</span>

            <div style={{ display: 'flex', gap: '6px' }}>
              <input
                type="text"
                placeholder="مبدأ..."
                value={originInput}
                onChange={(e) => setOriginInput(e.target.value)}
                style={{ flex: 1, background: 'rgba(125,125,125,0.15)', border: '1px solid var(--panel-border)', color: 'var(--text-main)', padding: '6px 10px', borderRadius: '6px', fontSize: '11px', fontFamily: 'Vazirmatn' }}
              />
              <button
                onClick={() => {
                  setPickingLocationFor('origin')
                  setMessage("روی نقشه کلیک کنید تا نقطه مبدأ تنظیم شود.")
                }}
                style={{ background: pickingLocationFor === 'origin' ? '#ec4899' : 'rgba(125,125,125,0.2)', border: 'none', color: 'var(--text-main)', padding: '4px 8px', borderRadius: '6px', fontSize: '10px', cursor: 'pointer' }}>
                📍 انتخاب
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px' }}>
              <input
                type="text"
                placeholder="مقصد (اختیاری)..."
                value={destInput}
                onChange={(e) => setDestInput(e.target.value)}
                style={{ flex: 1, background: 'rgba(125,125,125,0.15)', border: '1px solid var(--panel-border)', color: 'var(--text-main)', padding: '6px 10px', borderRadius: '6px', fontSize: '11px', fontFamily: 'Vazirmatn' }}
              />
              <button
                onClick={() => {
                  setPickingLocationFor('dest')
                  setMessage("روی نقشه کلیک کنید تا نقطه مقصد تنظیم شود.")
                }}
                style={{ background: pickingLocationFor === 'dest' ? '#ec4899' : 'rgba(125,125,125,0.2)', border: 'none', color: 'var(--text-main)', padding: '4px 8px', borderRadius: '6px', fontSize: '10px', cursor: 'pointer' }}>
                🎯 انتخاب
              </button>
            </div>

            {/* Mood selector */}
            <div>
              <span style={{ fontSize: '10px', color: 'var(--text-sub)', display: 'block', marginBottom: '4px' }}>حالت مسیریابی:</span>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {['direct', 'nature', 'culture', 'energy', 'quiet', 'photography', 'nightlife'].map(m => (
                  <button
                    key={m}
                    onClick={() => setSelectedMood(m)}
                    style={{
                      background: selectedMood === m ? 'linear-gradient(135deg, #10b981, #3b82f6)' : 'rgba(125,125,125,0.1)',
                      border: '1px solid var(--panel-border)',
                      color: selectedMood === m ? '#fff' : 'var(--text-main)',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      fontSize: '10px',
                      cursor: 'pointer',
                    }}>
                    {CATEGORY_ICONS[m] || '✨'} {m === 'direct' ? 'مستقیم' : m}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleDualPlanRoute}
              style={{ background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', color: '#fff', padding: '8px', borderRadius: '8px', fontWeight: 700, fontSize: '12px', cursor: 'pointer', marginTop: '2px' }}>
              🚀 رسم مسیر پیاده‌روی
            </button>

            {routeMetrics && (
              <div style={{
                background: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: '8px',
                padding: '8px 12px',
                fontSize: '11px',
                color: 'var(--text-main)',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                marginTop: '6px'
              }}>
                <div style={{ fontWeight: 700, color: '#38bdf8' }}>📊 اطلاعات مسیر:</div>
                <div>📏 مسافت: <strong>{(routeMetrics.distance / 1000).toFixed(2)} کیلومتر</strong></div>
                <div>⏱️ زمان تخمینی: <strong>{Math.round(routeMetrics.duration / 60)} دقیقه</strong></div>
                {routeWaypoints && routeWaypoints.length > 0 && (
                  <div>📍 توقفگاه‌ها: <strong>{routeWaypoints.length} نقطه</strong></div>
                )}
              </div>
            )}
          </div>

          {/* Section 4: Architecture Settings (Exploration Tracking & Show Fog) */}
          <div style={{ background: 'rgba(125,125,125,0.1)', padding: '12px', borderRadius: '12px', border: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <span style={{ fontWeight: 700, fontSize: '12px', color: '#38bdf8' }}>⚙️ تنظیمات کاوش و مه‌جنگ</span>

            {/* Setting 1: Exploration Tracking */}
            <div style={{ background: 'rgba(125,125,125,0.1)', padding: '10px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 700, fontSize: '11px', color: 'var(--text-main)' }}>ردیابی کاوش (Exploration Tracking)</span>
                <button
                  onClick={() => handleToggleTracking(!explorationTrackingEnabled)}
                  style={{
                    background: explorationTrackingEnabled ? '#10b981' : '#6b7280',
                    border: 'none',
                    color: '#fff',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '10px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}>
                  {explorationTrackingEnabled ? 'فعال (Enabled)' : 'غیرفعال (Disabled)'}
                </button>
              </div>
              <span style={{ fontSize: '9.5px', color: 'var(--text-sub)', lineHeight: 1.4 }}>
                وقتی غیرفعال باشد، پیشرفت کاوش، امتیاز XP و مناطق جدید شما ثبت نمی‌شود.
              </span>
            </div>

            {/* Setting 2: Show Fog */}
            <div style={{ background: 'rgba(125,125,125,0.1)', padding: '10px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 700, fontSize: '11px', color: 'var(--text-main)' }}>نمایش مه‌جنگ (Show Fog)</span>
                <button
                  onClick={() => handleToggleShowFog(!showFog)}
                  style={{
                    background: showFog ? '#3b82f6' : '#6b7280',
                    border: 'none',
                    color: '#fff',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '10px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}>
                  {showFog ? 'نمایان (Visible)' : 'مخفی (Hidden)'}
                </button>
              </div>
              <span style={{ fontSize: '9.5px', color: 'var(--text-sub)', lineHeight: 1.4 }}>
                تنها کنترل می‌کند که آیا مه روی نقشه نشان داده شود یا خیر. کاوش و کسب امتیاز همچنان ادامه می‌یابد.
              </span>
            </div>

            <div style={{ display: 'flex', gap: '6px', marginTop: '2px' }}>
              <button
                onClick={() => setShowHeatmap(!showHeatmap)}
                style={{ flex: 1, background: showHeatmap ? '#ef4444' : 'rgba(125,125,125,0.2)', border: 'none', color: '#fff', padding: '6px', borderRadius: '6px', fontSize: '10px', cursor: 'pointer' }}>
                🌡️ هیت‌مپ ({showHeatmap ? 'روشن' : 'خاموش'})
              </button>
              <button
                onClick={() => setAppTheme(appTheme === 'dark' ? 'light' : 'dark')}
                style={{ flex: 1, background: 'rgba(125,125,125,0.15)', border: '1px solid var(--panel-border)', color: 'var(--text-main)', padding: '6px', borderRadius: '6px', fontSize: '10px', cursor: 'pointer' }}>
                {appTheme === 'dark' ? '☀️ تم روشن' : '🌙 تم تاریک'}
              </button>
            </div>
          </div>

          {/* Section 5: Missions & Badges */}
          {userProfile?.badges && userProfile.badges.length > 0 && (
            <div>
              <span style={{ fontWeight: 700, fontSize: '11px', color: '#f59e0b', display: 'block', marginBottom: '6px' }}>🏆 نشان‌های شما</span>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {userProfile.badges.map(b => (
                  <span key={b.id} style={{ background: 'rgba(245, 158, 11, 0.2)', border: '1px solid rgba(245, 158, 11, 0.4)', color: '#fcd34d', padding: '3px 8px', borderRadius: '10px', fontSize: '10px', fontWeight: 600 }}>
                    {b.icon} {b.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 🔵 FLOATING QUICK ACTION BUTTONS (Right Stack - Neshan Style) */}
      <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 999, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button
          onClick={() => setDrawerOpen(!drawerOpen)}
          className="glass-panel"
          style={{ width: '40px', height: '40px', border: 'none', color: 'var(--text-main)', fontSize: '18px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          ☰
        </button>

        <button
          onClick={() => setAppTheme(appTheme === 'dark' ? 'light' : 'dark')}
          className="glass-panel"
          style={{ width: '40px', height: '40px', border: 'none', color: 'var(--text-main)', fontSize: '16px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {appTheme === 'dark' ? '☀️' : '🌙'}
        </button>

        <button
          onClick={() => setFlyToCoords([35.7127, 51.4069])}
          className="glass-panel"
          style={{ width: '40px', height: '40px', border: 'none', color: '#38bdf8', fontSize: '16px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          🎯
        </button>
      </div>

      {/* 🗺️ BOTTOM-LEFT MAP STYLE THUMBNAIL SWITCHER (Neshan Style) */}
      <div className="glass-panel" style={{ position: 'absolute', bottom: '20px', left: '20px', zIndex: 1000, padding: '6px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-sub)' }}>نمای نقشه:</span>
        {[
          { id: 'google', label: 'گوگل' },
          { id: 'satellite', label: 'ماهواره' },
          { id: 'carto_dark', label: 'نمای شب' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setMapTheme(t.id)}
            style={{
              background: mapTheme === t.id ? '#38bdf8' : 'rgba(125,125,125,0.2)',
              color: mapTheme === t.id ? '#fff' : 'var(--text-main)',
              border: 'none',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '10px',
              fontWeight: 700,
              cursor: 'pointer',
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* 🔴 STATUS & MESSAGE TOAST BANNER (Bottom Center) */}
      <div className="glass-panel" style={{ position: 'absolute', bottom: '20px', left: '50%', transform: 'translateX(-50%)', zIndex: 1000, padding: '8px 20px', display: 'flex', alignItems: 'center', gap: '10px', maxWidth: '80vw' }}>
        <span style={{ fontSize: '14px' }}>💡</span>
        <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-main)' }}>{message}</span>
        {isBusy && <span style={{ fontSize: '11px', color: '#38bdf8' }}>⌛ در حال پردازش...</span>}
        {error && <span style={{ fontSize: '11px', color: '#ef4444' }}>⚠️ {error}</span>}
      </div>

      {/* 🗺️ MAIN LEAFLET MAP CONTAINER */}
      <MapContainer
        center={tehranPosition}
        zoom={13}
        style={{ width: '100%', height: '100%' }}
        zoomControl={false}>

        <TileLayer url={themeUrls[mapTheme] || themeUrls.google} />

        <MapClicker
          pickingLocationFor={pickingLocationFor}
          onSelectOrigin={handleSelectOrigin}
          onSelectDest={handleSelectDest}
          onDiscoverPoint={handleDiscoverPoint}
        />
        <MapFlyTo center={flyToCoords} />

        {/* 🌡️ Heatmap Layer */}
        <HeatLayer points={heatPoints} enabled={showHeatmap} />

        {/* 🌫️ Atmospheric Canvas Fog of War Overlay */}
        <FogCanvasOverlay
          discoveredPoints={discoveredPoints}
          showFog={showFog}
          fogConfig={FOG_CONFIG}
        />

        {/* 📍 Minimal Category POI Markers */}
        {pois.map((poi) => {
          if (!poi.lat || !poi.lon) return null
          return (
            <Marker
              key={poi.id}
              position={[poi.lat, poi.lon]}
              icon={createCustomCategoryIcon(poi.category, poi.match_percentage, poi.is_discovered ?? true, poi.just_discovered)}>
              <Popup>
                <div style={{ padding: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 800, fontSize: '14px', color: CATEGORY_COLORS[poi.category] || '#38bdf8' }}>
                      {CATEGORY_ICONS[poi.category] || '📍'} {poi.name}
                    </span>
                    {poi.match_percentage && (
                      <span style={{ background: 'linear-gradient(135deg, #ec4899, #8b5cf6)', color: '#fff', fontSize: '10px', fontWeight: 800, padding: '2px 6px', borderRadius: '8px' }}>
                        ✨ {poi.match_percentage}٪
                      </span>
                    )}
                  </div>

                  <p style={{ fontSize: '12px', color: 'var(--text-sub)', margin: '0 0 10px 0', lineHeight: 1.4 }}>
                    {poi.description || 'مکان شاخص کلان‌شهر تهران'}
                  </p>

                  <button
                    onClick={() => {
                      setDestCoords([poi.lat, poi.lon])
                      setDestInput(poi.name)
                      setDrawerOpen(true)
                    }}
                    style={{ background: 'linear-gradient(135deg, #38bdf8, #3b82f6)', border: 'none', color: '#fff', width: '100%', padding: '6px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '12px' }}>
                    🎯 مسیریابی به این مکان
                  </button>
                </div>
              </Popup>
            </Marker>
          )
        })}

        {/* 🛣️ Route Polyline */}
        {routeCoords.length > 0 && (
          <Polyline
            positions={routeCoords}
            pathOptions={{
              color: '#38bdf8',
              weight: 6,
              opacity: 0.9,
              dashArray: '8, 12',
            }}
          />
        )}
      </MapContainer>

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={(user) => {
          setCurrentUser(user)
          setMessage(`خوش آمدید ${user.username} عزیز! 🌟`)
          fetchUserProfile()
          fetchFogStats()
        }}
      />

      <TrackingConfirmModal
        isOpen={trackingConfirmModalOpen}
        onClose={() => setTrackingConfirmModalOpen(false)}
        onConfirm={() => updateTrackingSetting(false)}
      />
    </div>
  )
}

export default App