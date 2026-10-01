import { useState, useEffect, useMemo, useCallback } from 'react'
import { MapContainer, TileLayer, useMapEvents, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import 'leaflet.heat'
import axios from 'axios'
import FOG_CONFIG from './config/fogConfig'
import FogCanvasOverlay from './components/FogCanvasOverlay'
import AuthModal from './components/AuthModal'
import LandingPage from './components/LandingPage'

// 🗺️ Map Clicker for Fog Discovery
function MapClicker({ onDiscoverPoint }) {
  useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng
      onDiscoverPoint(lat, lng)
    },
  })
  return null
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
      gradient: { 0.0: '#38bdf8', 0.3: '#10b981', 0.6: '#f59e0b', 1.0: '#ef4444' },
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

  // UI Interactive States matching template
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [isSearchExpanded, setIsSearchExpanded] = useState(false)
  const [isAccountOpen, setIsAccountOpen] = useState(false)
  const [currentTheme, setCurrentTheme] = useState('dark')
  const [searchMode, setSearchMode] = useState('streets') // 'streets' | 'places'
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])

  // User & Auth States
  const [currentUser, setCurrentUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authModalMode, setAuthModalMode] = useState('login')

  // Fog & Heatmap States
  const [discoveredPoints, setDiscoveredPoints] = useState([])
  const [fogStats, setFogStats] = useState(null)
  const [showFog, setShowFog] = useState(true)
  const [showHeatmap, setShowHeatmap] = useState(false)
  const [flyToCoords, setFlyToCoords] = useState(null)
  const [mapTheme, setMapTheme] = useState('carto_dark')

  // Status & Notification
  const [message, setMessage] = useState('روی نقشه کلیک کنید تا مه‌جنگ کنار برود...')
  const [isBusy, setIsBusy] = useState(false)

  const themeUrls = {
    google: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    satellite: 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    carto_dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  }

  // Sync body state classes for transitions
  useEffect(() => {
    const body = document.body
    body.className = `text-on-surface antialiased h-screen w-screen overflow-hidden transition-colors duration-300 text-slate-900 dark:text-on-surface ${
      isDrawerOpen ? 'drawer-open' : 'drawer-closed'
    } ${isSearchExpanded ? 'search-expanded' : 'search-collapsed'} ${
      isAccountOpen ? 'account-open' : 'account-closed'
    }`
  }, [isDrawerOpen, isSearchExpanded, isAccountOpen])

  // Sync theme
  useEffect(() => {
    const html = document.documentElement
    if (currentTheme === 'dark') {
      html.classList.remove('light')
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
      html.classList.add('light')
    }
  }, [currentTheme])

  const toggleTheme = () => {
    setCurrentTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  // 1. Fetch Fog Statistics & Discovered Points from Backend
  const fetchFogStats = useCallback(async () => {
    try {
      const response = await axios.get('/api/v1/fog/stats')
      setFogStats(response.data)
      const points = response.data?.all_points
      if (points && points.length > 0) {
        setDiscoveredPoints(points)
      } else {
        setDiscoveredPoints([])
      }
    } catch (err) {
      console.error('Error fetching fog stats:', err)
    }
  }, [])

  // 2. Discover Fog at Point (Manual Click or GPS)
  const handleDiscoverPoint = useCallback(
    async (lat, lng, accuracy = 10.0) => {
      setIsBusy(true)
      try {
        const res = await axios.post('/api/v1/fog/discover', {
          user_id: currentUser?.id || 1,
          lat,
          lon: lng,
          accuracy: accuracy,
          timestamp: Date.now() / 1000,
        })

        if (res.data.status === 'rejected') {
          setMessage(`⚠️ ${res.data.message || 'موقعیت برای ثبت معتبر نیست.'}`)
          return
        }

        setMessage(res.data.message || 'منطقه جدید کشف شد!')

        if (res.data.all_points && res.data.all_points.length > 0) {
          setDiscoveredPoints(res.data.all_points)
        } else {
          setDiscoveredPoints((prev) => [...prev, { lat, lon: lng }])
        }

        if (res.data.coverage_stats) {
          setFogStats((prev) => ({
            ...(prev || {}),
            ...res.data.coverage_stats,
            areas_discovered_count: res.data.all_points?.length || (prev?.areas_discovered_count || 0) + 1,
          }))
        } else {
          fetchFogStats()
        }
      } catch (error) {
        console.error('Error in fog discover:', error)
        setDiscoveredPoints((prev) => [...prev, { lat, lon: lng }])
        setMessage('نقطه ثبت شد.')
      } finally {
        setIsBusy(false)
      }
    },
    [currentUser, fetchFogStats]
  )

  // 3. GPS Live Locate Button
  const handleGPSLocate = () => {
    if (!navigator.geolocation) {
      setMessage('⚠️ مرورگر شما از Geolocation پشتیبانی نمی‌کند.')
      return
    }
    setMessage('📡 در حال دریافت موقعیت مکانی GPS...')
    setIsBusy(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsBusy(false)
        const { latitude, longitude, accuracy } = pos.coords
        setFlyToCoords([latitude, longitude])
        handleDiscoverPoint(latitude, longitude, accuracy || 15.0)
      },
      (err) => {
        setIsBusy(false)
        console.warn('GPS location error:', err)
        setMessage('⚠️ دسترسی به موقعیت مکانی ناموفق بود.')
      },
      { enableHighAccuracy: true, timeout: 8000 }
    )
  }

  // 4. Street Search (Nominatim API)
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setSearchResults([])
      return
    }
    const timer = setTimeout(async () => {
      try {
        const resp = await axios.get('https://nominatim.openstreetmap.org/search', {
          params: {
            q: searchQuery + ' تهران',
            format: 'json',
            addressdetails: 1,
            limit: 5,
            'accept-language': 'fa',
          },
        })
        setSearchResults(resp.data || [])
      } catch (err) {
        console.error('Search error:', err)
      }
    }, 400)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // 5. Logout Handler
  const handleLogout = async () => {
    try {
      await axios.post('/api/v1/auth/logout')
    } catch {
      // ignore
    }
    localStorage.removeItem('auth_token')
    delete axios.defaults.headers.common['Authorization']
    setCurrentUser(null)
    setIsAuthenticated(false)
    setFogStats(null)
    setDiscoveredPoints([])
    setIsAccountOpen(false)
    setMessage('از حساب کاربری خارج شدید.')
  }

  // 6. Auth State Initialization
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      axios
        .get('/api/v1/auth/me')
        .then((res) => {
          setCurrentUser(res.data)
          setIsAuthenticated(true)
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
      fetchFogStats()
    }
  }, [isAuthenticated, fetchFogStats])

  // Heatmap points formatting
  const heatPoints = useMemo(() => {
    return discoveredPoints.map((pt) => {
      const lat = Array.isArray(pt) ? pt[0] : pt.lat
      const lon = Array.isArray(pt) ? pt[1] : pt.lon
      return [lat, lon, 0.8]
    })
  }, [discoveredPoints])

  if (isInitializing) {
    return (
      <div
        style={{
          width: '100vw',
          height: '100vh',
          background: '#0f1418',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#89ceff',
          fontFamily: 'Vazirmatn, Fira Sans',
        }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '38px', marginBottom: '12px' }}>🧭</div>
          <div style={{ fontSize: '15px', fontWeight: 700 }}>در حال بررسی نشست کاربری...</div>
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
    <>
      {/* 🗺️ Map Background (Underlay) */}
      <div className="map-bg">
        <MapContainer
          center={tehranPosition}
          zoom={13}
          style={{ width: '100%', height: '100%' }}
          zoomControl={false}>
          <TileLayer url={themeUrls[mapTheme] || themeUrls.carto_dark} />

          <MapClicker onDiscoverPoint={(lat, lng) => handleDiscoverPoint(lat, lng)} />
          <MapFlyTo center={flyToCoords} />

          {/* 🌡️ Heatmap Layer */}
          <HeatLayer points={heatPoints} enabled={showHeatmap} />

          {/* 🌫️ Atmospheric Canvas Fog of War Overlay */}
          <FogCanvasOverlay
            discoveredPoints={discoveredPoints}
            showFog={showFog}
            fogConfig={FOG_CONFIG}
          />
        </MapContainer>
      </div>

      {/* 🟢 MAIN UI LAYER (Over Map) */}
      <div className="absolute inset-0 z-10 flex flex-col pointer-events-none main-content transition-all duration-300">
        {/* Top App Bar */}
        <header className="flex justify-between items-center px-hud-margin-mobile md:px-hud-margin-desktop h-16 w-full glass-panel pointer-events-auto shadow-sm fixed top-0 z-50 transition-colors duration-300">
          {/* Profile Avatar */}
          <button
            onClick={() => {
              setIsAccountOpen(!isAccountOpen)
              if (isDrawerOpen && window.innerWidth < 768) setIsDrawerOpen(false)
            }}
            className="w-8 h-8 md:w-10 md:h-10 rounded-full overflow-hidden border border-black/10 dark:border-white/10 hover:shadow-md hover:scale-105 active:scale-95 transition-all duration-200 bg-primary/20 flex items-center justify-center text-primary font-bold"
            id="profileBtn">
            <span className="material-symbols-outlined text-[20px]">person</span>
          </button>

          {/* Logo */}
          <div className="font-display-lg text-display-lg-mobile md:text-display-lg text-primary dark:text-primary-fixed-dim tracking-tight transition-colors duration-300 flex items-center gap-2">
            <span>UrbanExplorer</span>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-primary/10 dark:bg-primary-container/20 text-primary dark:text-primary-fixed-dim border border-primary/20">
              FOG MAP
            </span>
          </div>

          {/* Hamburger Menu (Mobile & Toggle) */}
          <button
            onClick={() => {
              setIsDrawerOpen(!isDrawerOpen)
              setIsAccountOpen(false)
            }}
            className="p-2 text-primary dark:text-primary-fixed-dim hover:bg-black/5 dark:hover:bg-white/10 hover:scale-105 active:scale-95 rounded-full transition-all duration-200 ease-in-out flex items-center justify-center"
            id="menuBtn">
            <span className="material-symbols-outlined">menu</span>
          </button>
        </header>

        {/* Dynamic Search Area (Floats below top bar) */}
        <div
          className="pointer-events-auto mt-20 px-hud-margin-mobile relative z-40 md:w-1/2 lg:w-1/3 md:mx-auto"
          id="searchContainer">
          {/* Floating Search FAB (Visible when collapsed) */}
          <button
            onClick={() => setIsSearchExpanded(true)}
            className="absolute top-0 right-hud-margin-mobile w-12 h-12 rounded-full glass-panel flex items-center justify-center text-primary dark:text-primary-fixed-dim shadow-[0_4px_12px_rgba(0,0,0,0.05)] hover:scale-105 hover:shadow-lg transition-all duration-300 z-10 md:w-full md:rounded-xl md:h-12 md:right-0 md:justify-start md:px-4 md:gap-3"
            id="searchFab">
            <span className="material-symbols-outlined">search</span>
            <span className="hidden md:inline text-slate-500 font-body-base">جستجوی معابر و اماکن تهران...</span>
          </button>

          {/* Expanded Search Interface */}
          <div
            className="w-full glass-panel rounded-xl shadow-[0_8px_32px_rgba(15,23,42,0.12)] p-4 flex flex-col gap-4 transition-colors duration-300"
            id="searchInterface">
            {/* Search Input */}
            <div className="relative w-full">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 dark:text-slate-400">
                search
              </span>
              <input
                className="w-full bg-white/50 dark:bg-black/30 border border-black/10 dark:border-white/10 rounded-lg pl-10 pr-10 py-2 font-body-base text-body-base text-slate-900 dark:text-on-surface placeholder:text-slate-500 dark:placeholder:text-slate-400 focus:outline-none focus:border-primary/50 dark:focus:border-primary-fixed-dim/50 focus:ring-1 focus:ring-primary/50 dark:focus:ring-primary-fixed-dim/50 transition-all duration-300"
                placeholder="جستجوی خیابان یا محله (ولیعصر، آزادی...)"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button
                onClick={() => {
                  setSearchQuery('')
                  setSearchResults([])
                  setIsSearchExpanded(false)
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary-fixed-dim hover:rotate-90 transition-all duration-300"
                id="closeSearchBtn">
                <span className="material-symbols-outlined text-sm">close</span>
              </button>
            </div>

            {/* Toggle Modes */}
            <div className="flex bg-black/5 dark:bg-white/5 rounded-lg p-1 w-full relative transition-colors duration-300">
              <div
                className="absolute top-1 bottom-1 left-1 w-[calc(50%-4px)] bg-white dark:bg-surface-container-high rounded-md shadow-sm transition-transform duration-300 z-0"
                id="toggleBg"
                style={{ transform: searchMode === 'streets' ? 'translateX(0)' : 'translateX(100%)' }}
              />
              <button
                onClick={() => setSearchMode('streets')}
                className={`flex-1 py-1.5 font-label-sm text-label-sm z-10 relative transition-colors duration-300 ${
                  searchMode === 'streets' ? 'text-primary dark:text-primary-fixed-dim font-bold' : 'text-slate-500'
                }`}
                id="toggleStreets">
                معابر
              </button>
              <button
                onClick={() => setSearchMode('places')}
                className={`flex-1 py-1.5 font-label-sm text-label-sm z-10 relative transition-colors duration-300 ${
                  searchMode === 'places' ? 'text-primary dark:text-primary-fixed-dim font-bold' : 'text-slate-500'
                }`}
                id="togglePlaces">
                مناطق
              </button>
            </div>

            {/* Horizontal Quick Actions Bar */}
            <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1 -mx-2 px-2">
              <button
                onClick={() => setShowHeatmap(!showHeatmap)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-black/10 dark:border-white/10 font-label-sm text-label-sm whitespace-nowrap hover:scale-105 active:scale-95 transition-all duration-200 ${
                  showHeatmap
                    ? 'bg-amber-gold text-slate-900 font-bold shadow-sm'
                    : 'bg-white/60 dark:bg-surface-container-low text-slate-900 dark:text-on-surface'
                }`}>
                <span className="material-symbols-outlined text-[16px] text-amber-gold">local_fire_department</span>
                هیت‌مپ {showHeatmap ? 'روشن' : 'خاموش'}
              </button>

              <button
                onClick={() => setShowFog(!showFog)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-black/10 dark:border-white/10 font-label-sm text-label-sm whitespace-nowrap hover:scale-105 active:scale-95 transition-all duration-200 ${
                  showFog
                    ? 'bg-primary text-slate-900 font-bold shadow-sm'
                    : 'bg-white/60 dark:bg-surface-container-low text-slate-900 dark:text-on-surface'
                }`}>
                <span className="material-symbols-outlined text-[16px] text-primary">cloud</span>
                مه‌جنگ {showFog ? 'نمایان' : 'مخفی'}
              </button>

              <button
                onClick={handleGPSLocate}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/60 dark:bg-surface-container-low border border-black/10 dark:border-white/10 font-label-sm text-label-sm text-slate-900 dark:text-on-surface whitespace-nowrap hover:bg-white dark:hover:bg-surface-container-high hover:scale-105 hover:shadow-sm active:scale-95 transition-all duration-200">
                <span className="material-symbols-outlined text-[16px] text-vibrant-emerald">my_location</span>
                موقعیت من
              </button>
            </div>

            {/* Search Results Dropdown */}
            {searchResults.length > 0 && (
              <div className="flex flex-col gap-1 max-h-48 overflow-y-auto border-t border-black/10 dark:border-white/10 pt-2">
                {searchResults.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      const lat = parseFloat(item.lat)
                      const lon = parseFloat(item.lon)
                      setFlyToCoords([lat, lon])
                      handleDiscoverPoint(lat, lon, 10.0)
                      setSearchResults([])
                      setIsSearchExpanded(false)
                    }}
                    className="p-2 rounded-lg hover:bg-primary/10 cursor-pointer flex flex-col gap-0.5 text-right transition-colors">
                    <span className="font-bold text-[12px] text-primary">{item.display_name.split(',')[0]}</span>
                    <span className="text-[10px] text-slate-400 truncate">{item.display_name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Spacer */}
        <div className="flex-1"></div>

        {/* Bottom Nav Bar (Mobile Only) */}
        <nav className="glass-panel w-full h-16 pointer-events-auto flex justify-around items-center pb-safe z-50 transition-colors duration-300 md:hidden">
          {/* Map (Active) */}
          <button
            onClick={() => setFlyToCoords([35.7127, 51.4069])}
            className="flex flex-col items-center justify-center w-16 h-full gap-1 text-primary dark:text-primary-fixed-dim group active:scale-95 transition-all duration-200">
            <div className="px-4 py-1 rounded-full bg-primary/10 dark:bg-primary-container/20 group-hover:bg-primary/20 dark:group-hover:bg-primary-container/30 transition-colors duration-300">
              <span className="material-symbols-outlined" data-icon="map">
                map
              </span>
            </div>
            <span className="font-label-sm text-[10px] leading-tight font-semibold">نقشه</span>
          </button>

          {/* Heatmap Toggle */}
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex flex-col items-center justify-center w-16 h-full gap-1 group active:scale-95 transition-all duration-200 ${
              showHeatmap ? 'text-amber-gold' : 'text-slate-500 dark:text-slate-400'
            }`}>
            <div className="px-4 py-1 rounded-full group-hover:bg-black/5 dark:group-hover:bg-white/10 transition-colors duration-300">
              <span className="material-symbols-outlined">local_fire_department</span>
            </div>
            <span className="font-label-sm text-[10px] leading-tight">هیت‌مپ</span>
          </button>

          {/* GPS Locate */}
          <button
            onClick={handleGPSLocate}
            className="flex flex-col items-center justify-center w-16 h-full gap-1 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-on-surface group active:scale-95 transition-all duration-200">
            <div className="px-4 py-1 rounded-full group-hover:bg-black/5 dark:group-hover:bg-white/10 transition-colors duration-300">
              <span className="material-symbols-outlined">my_location</span>
            </div>
            <span className="font-label-sm text-[10px] leading-tight">موقعیت من</span>
          </button>
        </nav>
      </div>

      {/* 🔴 STATUS & MESSAGE TOAST BANNER (Bottom Center) */}
      <div
        className="glass-panel"
        style={{
          position: 'fixed',
          bottom: '80px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 40,
          padding: '8px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          maxWidth: '85vw',
          borderRadius: '24px',
        }}>
        <span style={{ fontSize: '14px' }}>💡</span>
        <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-main)' }}>{message}</span>
        {isBusy && <span style={{ fontSize: '11px', color: '#89ceff' }}>⌛ در حال ثبت...</span>}
      </div>

      {/* 🗺️ BOTTOM-LEFT MAP STYLE SWITCHER (Desktop) */}
      <div
        className="glass-panel hidden md:flex items-center gap-1.5 p-1.5 rounded-xl z-40 fixed bottom-6 left-6 shadow-md pointer-events-auto">
        {[
          { id: 'carto_dark', label: 'شب' },
          { id: 'google', label: 'گوگل' },
          { id: 'satellite', label: 'ماهواره' },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setMapTheme(t.id)}
            className={`px-3 py-1 rounded-lg text-[11px] font-bold transition-all ${
              mapTheme === t.id
                ? 'bg-primary text-slate-900 shadow-sm'
                : 'text-slate-400 hover:text-on-surface'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* OVERLAYS: SIDE DRAWER & ACCOUNT PANEL                             */}
      {/* ═══════════════════════════════════════════════════════════════════ */}

      {/* Side Drawer */}
      <div
        className="fixed inset-y-0 right-0 w-[92vw] max-w-[340px] md:w-[80px] glass-panel z-[100] md:z-40 md:pt-16 shadow-[-4px_0_24px_rgba(0,0,0,0.1)] flex flex-col pointer-events-auto translate-x-[100%] md:translate-x-0 transition-all duration-300"
        id="sideDrawer">
        {/* Drawer Header */}
        <div className="p-hud-margin-mobile flex justify-between items-center border-b border-black/10 dark:border-white/10 transition-colors duration-300">
          <div className="flex flex-col desktop-nav-text">
            <span className="font-headline-md text-headline-md text-slate-900 dark:text-on-surface transition-colors duration-300">
              UrbanExplorer
            </span>
            <span className="font-label-sm text-label-sm text-slate-500 dark:text-slate-400 transition-colors duration-300">
              ابزارها و تنظیمات مه‌جنگ
            </span>
          </div>
          <button
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            className="p-2 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-on-surface rounded-full hover:bg-black/5 dark:hover:bg-white/10 hover:rotate-90 active:scale-95 transition-all duration-200 -mx-2"
            id="closeMenuBtn">
            <span className="material-symbols-outlined md:hidden">close</span>
            <span className="material-symbols-outlined hidden md:block">menu</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-hud-margin-mobile flex flex-col gap-6">
          {/* Desktop Nav Items */}
          <section className="hidden md:flex flex-col gap-2">
            {/* Map Nav */}
            <button
              onClick={() => setFlyToCoords([35.7127, 51.4069])}
              className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 active:scale-95 transition-all duration-200 text-left text-primary dark:text-primary-fixed-dim bg-primary/10 dark:bg-primary-container/20 group">
              <div className="w-8 h-8 rounded-full flex items-center justify-center transition-colors duration-300 mx-auto md:mx-0">
                <span className="material-symbols-outlined group-hover:scale-110 transition-transform duration-200">
                  map
                </span>
              </div>
              <div className="flex-1 desktop-nav-text">
                <div className="font-body-bold text-body-bold transition-colors duration-300">نقشه تهران</div>
              </div>
            </button>

            {/* Heatmap Nav */}
            <button
              onClick={() => setShowHeatmap(!showHeatmap)}
              className={`w-full flex items-center gap-3 p-3 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 active:scale-95 transition-all duration-200 text-left group ${
                showHeatmap ? 'text-amber-gold bg-amber-gold/10' : 'text-slate-500 dark:text-slate-400'
              }`}>
              <div className="w-8 h-8 rounded-full flex items-center justify-center transition-colors duration-300 mx-auto md:mx-0">
                <span className="material-symbols-outlined group-hover:scale-110 transition-transform duration-200">
                  local_fire_department
                </span>
              </div>
              <div className="flex-1 desktop-nav-text">
                <div className="font-body-bold text-body-bold transition-colors duration-300">
                  هیت‌مپ ({showHeatmap ? 'روشن' : 'خاموش'})
                </div>
              </div>
            </button>

            {/* Fog Nav */}
            <button
              onClick={() => setShowFog(!showFog)}
              className={`w-full flex items-center gap-3 p-3 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 active:scale-95 transition-all duration-200 text-left group ${
                showFog ? 'text-primary bg-primary/10' : 'text-slate-500 dark:text-slate-400'
              }`}>
              <div className="w-8 h-8 rounded-full flex items-center justify-center transition-colors duration-300 mx-auto md:mx-0">
                <span className="material-symbols-outlined group-hover:scale-110 transition-transform duration-200">
                  cloud
                </span>
              </div>
              <div className="flex-1 desktop-nav-text">
                <div className="font-body-bold text-body-bold transition-colors duration-300">
                  مه‌جنگ ({showFog ? 'نمایان' : 'مخفی'})
                </div>
              </div>
            </button>

            {/* GPS Nav */}
            <button
              onClick={handleGPSLocate}
              className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 active:scale-95 transition-all duration-200 text-left text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-on-surface group">
              <div className="w-8 h-8 rounded-full flex items-center justify-center transition-colors duration-300 mx-auto md:mx-0">
                <span className="material-symbols-outlined group-hover:scale-110 transition-transform duration-200">
                  my_location
                </span>
              </div>
              <div className="flex-1 desktop-nav-text">
                <div className="font-body-bold text-body-bold transition-colors duration-300">موقعیت زنده GPS</div>
              </div>
            </button>
          </section>

          <div className="hidden md:block h-px bg-black/10 dark:bg-white/10 w-full transition-colors duration-300"></div>

          {/* Real-time Fog Coverage Stats Section (matching Updates in template) */}
          <section>
            <h3 className="font-label-sm text-label-sm text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider transition-colors duration-300 desktop-nav-text">
              آمار مه‌جنگ
            </h3>
            <div className="flex flex-col gap-2">
              {/* Stat Card 1: Area */}
              <div className="w-full flex items-center gap-3 p-3 rounded-lg bg-black/5 dark:bg-white/5 text-left group">
                <div className="w-10 h-10 rounded-full bg-vibrant-emerald/10 flex items-center justify-center text-vibrant-emerald transition-colors duration-300 mx-auto md:mx-0 shrink-0">
                  <span className="material-symbols-outlined">square_foot</span>
                </div>
                <div className="flex-1 desktop-nav-text">
                  <div className="font-body-bold text-body-bold text-slate-900 dark:text-on-surface transition-colors duration-300">
                    {fogStats?.total_area_sqkm ?? (discoveredPoints.length * 0.07).toFixed(2)} km²
                  </div>
                  <div className="font-label-sm text-label-sm text-slate-500 dark:text-slate-400 transition-colors duration-300 truncate">
                    مساحت کشف‌شده در پایتخت
                  </div>
                </div>
              </div>

              {/* Stat Card 2: Coverage % */}
              <div className="w-full flex items-center gap-3 p-3 rounded-lg bg-black/5 dark:bg-white/5 text-left group">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary transition-colors duration-300 mx-auto md:mx-0 shrink-0">
                  <span className="material-symbols-outlined">pie_chart</span>
                </div>
                <div className="flex-1 desktop-nav-text">
                  <div className="font-body-bold text-body-bold text-slate-900 dark:text-on-surface transition-colors duration-300">
                    {fogStats?.city_coverage_percentage ?? 0}٪
                  </div>
                  <div className="font-label-sm text-label-sm text-slate-500 dark:text-slate-400 transition-colors duration-300 truncate">
                    درصد پوشش کلان‌شهر
                  </div>
                </div>
              </div>

              {/* Stat Card 3: Discovered points */}
              <div className="w-full flex items-center gap-3 p-3 rounded-lg bg-black/5 dark:bg-white/5 text-left group">
                <div className="w-10 h-10 rounded-full bg-amber-gold/10 flex items-center justify-center text-amber-gold transition-colors duration-300 mx-auto md:mx-0 shrink-0">
                  <span className="material-symbols-outlined">pin_drop</span>
                </div>
                <div className="flex-1 desktop-nav-text">
                  <div className="font-body-bold text-body-bold text-slate-900 dark:text-on-surface transition-colors duration-300">
                    {discoveredPoints.length} نقطه
                  </div>
                  <div className="font-label-sm text-label-sm text-slate-500 dark:text-slate-400 transition-colors duration-300 truncate">
                    ثبت‌شده در پایگاه‌داده
                  </div>
                </div>
              </div>
            </div>
          </section>

          <div className="h-px bg-black/10 dark:bg-white/10 w-full transition-colors duration-300"></div>

          {/* Appearance Section */}
          <section>
            <h3 className="font-label-sm text-label-sm text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider transition-colors duration-300 desktop-nav-text">
              پوسته
            </h3>
            <div className="flex items-center justify-between bg-black/5 dark:bg-white/5 rounded-lg p-3 w-full transition-colors duration-300 desktop-nav-text">
              <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                <span className="material-symbols-outlined text-[18px]">light_mode</span>
              </div>
              <div className="theme-switch-wrapper">
                <label className="theme-switch" htmlFor="theme-toggle-switch">
                  <input
                    id="theme-toggle-switch"
                    type="checkbox"
                    checked={currentTheme === 'dark'}
                    onChange={toggleTheme}
                  />
                  <div className="slider"></div>
                </label>
              </div>
              <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                <span className="material-symbols-outlined text-[18px]">dark_mode</span>
              </div>
            </div>

            <div className="hidden md:flex flex-col gap-2 mt-4">
              <button
                onClick={toggleTheme}
                className="w-full flex items-center justify-center p-3 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 active:scale-95 transition-all duration-200 text-slate-500 dark:text-slate-400"
                title="Toggle Theme">
                <span className="material-symbols-outlined hover:rotate-180 transition-transform duration-500">
                  {currentTheme === 'dark' ? 'dark_mode' : 'light_mode'}
                </span>
              </button>
            </div>
          </section>
        </div>
      </div>

      {/* Account Panel Dropdown */}
      <div
        className="fixed top-20 left-hud-margin-mobile md:left-hud-margin-desktop w-72 glass-panel rounded-xl shadow-[0_8px_32px_rgba(15,23,42,0.12)] p-4 flex flex-col gap-4 z-[60] pointer-events-auto transition-colors duration-300"
        id="accountPanel">
        {/* User Info */}
        <div className="flex items-center gap-3 pb-4 border-b border-black/10 dark:border-white/10 transition-colors duration-300">
          <div className="w-12 h-12 rounded-full overflow-hidden border border-black/10 dark:border-white/10 bg-primary/20 flex items-center justify-center text-primary font-black">
            <span className="material-symbols-outlined text-2xl">person</span>
          </div>
          <div className="flex flex-col">
            <span className="font-body-bold text-body-bold text-slate-900 dark:text-on-surface transition-colors duration-300">
              {currentUser.username}
            </span>
            <span className="font-label-sm text-label-sm text-slate-500 dark:text-slate-400 transition-colors duration-300">
              {currentUser.email || `${currentUser.username}@urban.app`}
            </span>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="bg-black/5 dark:bg-white/5 p-2.5 rounded-lg flex justify-between items-center text-[11px]">
          <span className="text-slate-400">مساحت پوشش:</span>
          <span className="font-bold text-vibrant-emerald">
            {fogStats?.total_area_sqkm ?? (discoveredPoints.length * 0.07).toFixed(2)} km²
          </span>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-1">
          <button
            onClick={() => setMessage('شناسه کاربری شما در دیتابیس ثبت است.')}
            className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 active:scale-95 transition-all duration-200 text-left text-slate-900 dark:text-on-surface group">
            <span className="material-symbols-outlined text-slate-500 dark:text-slate-400 transition-colors duration-300 group-hover:text-primary dark:group-hover:text-primary-fixed-dim">
              person
            </span>
            <span className="font-body-base text-body-base">پروفایل کاربری</span>
          </button>

          <button
            onClick={() => setMessage('تنظیمات مه‌جنگ فعال است.')}
            className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 active:scale-95 transition-all duration-200 text-left text-slate-900 dark:text-on-surface group">
            <span className="material-symbols-outlined text-slate-500 dark:text-slate-400 transition-colors duration-300 group-hover:text-primary dark:group-hover:text-primary-fixed-dim">
              settings
            </span>
            <span className="font-body-base text-body-base">تنظیمات کاوش</span>
          </button>
        </div>

        <div className="pt-2 border-t border-black/10 dark:border-white/10 transition-colors duration-300">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-error/10 active:scale-95 transition-all duration-200 text-left text-[#ba1a1a] dark:text-error group">
            <span className="material-symbols-outlined group-hover:-translate-x-1 transition-transform">
              logout
            </span>
            <span className="font-body-base text-body-base">خروج از حساب</span>
          </button>
        </div>
      </div>

      {/* Backdrop for Drawer/Account Panel */}
      <div
        onClick={() => {
          if (isDrawerOpen && window.innerWidth < 768) setIsDrawerOpen(false)
          if (isAccountOpen) setIsAccountOpen(false)
        }}
        className={`fixed inset-0 bg-slate-900/20 dark:bg-black/40 backdrop-blur-sm z-[55] transition-all duration-300 md:hidden ${
          (isDrawerOpen || isAccountOpen) ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        id="backdrop"
      />
    </>
  )
}

export default App