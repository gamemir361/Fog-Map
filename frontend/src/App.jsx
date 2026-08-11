import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap, Polyline, Circle, CircleMarker } from 'react-leaflet'
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
    },
  })
  return null
}

// 🎯 Viewport-aware Density Event Handler (Phase 4.1.5)
function ViewportDensityHandler({ onViewportChange }) {
  const map = useMapEvents({
    moveend: () => {
      const bounds = map.getBounds()
      const zoom = map.getZoom()
      onViewportChange(bounds, zoom)
    },
    zoomend: () => {
      const bounds = map.getBounds()
      const zoom = map.getZoom()
      onViewportChange(bounds, zoom)
    },
  })

  useEffect(() => {
    if (map) {
      const bounds = map.getBounds()
      const zoom = map.getZoom()
      onViewportChange(bounds, zoom)
    }
  }, [map, onViewportChange])

  return null
}

const createClusterCountIcon = (count) => {
  return L.divIcon({
    className: 'custom-cluster-count-icon',
    html: `
      <div style="
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.95), rgba(124, 58, 237, 0.95));
        color: #ffffff;
        font-weight: 900;
        font-size: 11px;
        font-family: Vazirmatn, sans-serif;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #ffffff;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.6);
      ">
        ${count}
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
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

const RARITY_CONFIG = {
  legendary: { label: 'افسانه‌ای', icon: '⭐', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b' },
  epic: { label: 'حماسی', icon: '🟣', color: '#a855f7', bg: 'rgba(168, 85, 247, 0.15)', border: '#a855f7' },
  rare: { label: 'کمیاب', icon: '🔹', color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.15)', border: '#38bdf8' },
  common: { label: 'معمولی', icon: '🟢', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981' },
}

// 🎪 Exploration Event Styling & Icons (Phase 4.1.3)
const EVENT_TYPE_COLORS = {
  cultural: '#a855f7',
  historical: '#f59e0b',
  challenge: '#ef4444',
  nature: '#10b981',
  exploration: '#38bdf8',
  default: '#a855f7',
}

const EVENT_TYPE_ICONS = {
  cultural: '🎭',
  historical: '🏛️',
  challenge: '🔥',
  nature: '🌿',
  exploration: '💎',
  default: '🎪',
}

function createCustomEventIcon(eventType, insideGeofence = false) {
  const color = EVENT_TYPE_COLORS[eventType] || EVENT_TYPE_COLORS.default
  const emoji = EVENT_TYPE_ICONS[eventType] || EVENT_TYPE_ICONS.default
  const borderColor = insideGeofence ? '#10b981' : '#f59e0b'
  const glowColor = insideGeofence ? 'rgba(16, 185, 129, 0.6)' : 'rgba(245, 158, 11, 0.5)'

  const html = `
    <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; cursor: pointer;">
      <div style="position: absolute; width: 40px; height: 40px; border-radius: 50%; background: ${glowColor}; animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
      <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #1e1b4b, ${color}); border: 2.5px solid ${borderColor}; border-radius: 50%; box-shadow: 0 0 14px ${glowColor}; display: flex; align-items: center; justify-content: center; z-index: 2;">
        <span style="font-size: 15px; line-height: 1; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.5));">${emoji}</span>
      </div>
      <div style="position: absolute; bottom: -6px; background: linear-gradient(135deg, #f59e0b, #ef4444); color: #fff; font-size: 8px; font-weight: 900; padding: 1px 5px; border-radius: 6px; border: 1px solid #fff; white-space: nowrap; z-index: 3;">رویداد</div>
    </div>
  `

  return L.divIcon({
    html: html,
    className: 'custom-event-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20],
  })
}

function getDistanceMeters(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return null
  const R = 6371000.0
  const phi1 = (lat1 * Math.PI) / 180.0
  const phi2 = (lat2 * Math.PI) / 180.0
  const deltaPhi = ((lat2 - lat1) * Math.PI) / 180.0
  const deltaLambda = ((lon2 - lon1) * Math.PI) / 180.0
  const a = Math.sin(deltaPhi / 2.0) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2.0) ** 2
  const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a))
  return Math.round(R * c)
}

function formatDistancePersian(meters) {
  if (meters == null) return ''
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)} کیلومتر`
  }
  return `${meters} متر`
}

// 🎨 Sleek Category Markers (Unknown vs Discovered with Rarity Visuals)
function createCustomCategoryIcon(category, matchPercentage = null, isDiscovered = true, justDiscovered = false, rarity = 'common') {
  const rCfg = RARITY_CONFIG[rarity] || RARITY_CONFIG.common

  if (!isDiscovered || category === 'unknown') {
    const unknownHtml = `
      <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 34px; height: 34px; cursor: pointer;">
        <div style="position: absolute; width: 34px; height: 34px; border-radius: 50%; background: ${rCfg.bg}; animation: ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
        <div style="width: 28px; height: 28px; background: linear-gradient(135deg, #3b0764, #6b21a8); border: 2px solid ${rCfg.border}; border-radius: 50%; box-shadow: 0 0 12px ${rCfg.color}; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease;">
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
      <div style="width: 28px; height: 28px; background: ${color}; border: 2.5px solid ${rCfg.border}; border-radius: 50%; box-shadow: 0 0 10px ${rCfg.color}; display: flex; align-items: center; justify-content: center; transition: all 0.2s ease;">
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
  const [userProfile, setUserProfile] = useState(null)
  const [progression, setProgression] = useState({
    level: 1,
    total_xp: 0,
    xp_in_level: 0,
    xp_needed_for_next: 50,
    progress_pct: 0,
  })
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

  // Leaderboard States (Phase 3.4)
  const [leaderboardType, setLeaderboardType] = useState('overall')
  const [leaderboardData, setLeaderboardData] = useState(null)
  const [leaderboardLoading, setLeaderboardLoading] = useState(false)
  const [leaderboardError, setLeaderboardError] = useState(false)

  // Nearby Exploration Events & Filtering State (Phase 4.1.3 - 4.1.8)
  const [nearbyEvents, setNearbyEvents] = useState([])
  const [participatingEventId, setParticipatingEventId] = useState(null)
  const [eventLeaderboards, setEventLeaderboards] = useState({})
  const [eventActivities, setEventActivities] = useState({})

  // Event Filter & Discovery HUD State (Phase 4.1.8)
  const [eventFilterType, setEventFilterType] = useState('all')
  const [eventFilterStatus, setEventFilterStatus] = useState('active')
  const [eventFilterSort, setEventFilterSort] = useState('distance')

  // Event Heatmap & Density Clustering State (Phase 4.1.5)
  const [eventDensityClusters, setEventDensityClusters] = useState([])
  const latestDensityReqRef = useRef(0)

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

  const handleViewportChange = useCallback((bounds, zoom) => {
    if (!bounds) return
    const minLat = bounds.getSouth()
    const minLon = bounds.getWest()
    const maxLat = bounds.getNorth()
    const maxLon = bounds.getEast()

    const reqId = ++latestDensityReqRef.current

    axios
      .get(
        `/api/v1/exploration/events/density?min_lat=${minLat}&min_lon=${minLon}&max_lat=${maxLat}&max_lon=${maxLon}&zoom=${zoom}&status=${eventFilterStatus}&event_type=${eventFilterType}`
      )
      .then((res) => {
        if (reqId === latestDensityReqRef.current && res.data && res.data.clusters) {
          setEventDensityClusters(res.data.clusters)
        }
      })
      .catch((err) => {
        console.error("Error fetching event density:", err)
      })
  }, [eventFilterStatus, eventFilterType])

  // ==========================================
  // API Fetching & Initial Load
  // ==========================================
  const fetchEventActivities = useCallback(async (eventId) => {
    if (!eventId) return
    try {
      const response = await axios.get(`/api/v1/exploration/events/activity?event_id=${eventId}&limit=5`)
      if (response.data && response.data.status === 'success') {
        setEventActivities((prev) => ({
          ...prev,
          [eventId]: response.data.activities || [],
        }))
      }
    } catch (err) {
      console.error(`Error fetching activities for event ${eventId}:`, err)
    }
  }, [])

  const fetchEventLeaderboard = useCallback(async (eventId) => {
    if (!eventId) return
    try {
      const response = await axios.get(`/api/v1/exploration/events/${eventId}/leaderboard?limit=5`)
      if (response.data && response.data.status === 'success') {
        setEventLeaderboards((prev) => ({
          ...prev,
          [eventId]: response.data,
        }))
      }
    } catch (err) {
      console.error(`Error fetching event ${eventId} leaderboard:`, err)
    }
  }, [])

  const fetchNearbyEvents = useCallback(async (lat, lon) => {
    try {
      const targetLat = lat != null ? lat : (originCoords ? originCoords[0] : 35.7127)
      const targetLon = lon != null ? lon : (originCoords ? originCoords[1] : 51.4069)
      const typeParam = eventFilterType !== 'all' ? `&event_type=${eventFilterType}` : ''
      const statusParam = `&status=${eventFilterStatus}`
      const sortParam = `&sort=${eventFilterSort}`
      const response = await axios.get(`/api/v1/exploration/events/nearby?lat=${targetLat}&lon=${targetLon}&radius=10000${statusParam}${typeParam}${sortParam}`)
      if (response.data && response.data.events) {
        setNearbyEvents(response.data.events)
        response.data.events.forEach((evt) => {
          fetchEventLeaderboard(evt.id)
          fetchEventActivities(evt.id)
        })
      }
    } catch (err) {
      console.error("Error fetching nearby events:", err)
    }
  }, [originCoords, eventFilterType, eventFilterStatus, eventFilterSort, fetchEventLeaderboard, fetchEventActivities])

  const handleParticipateEvent = async (eventId) => {
    const lat = originCoords ? originCoords[0] : 35.7127
    const lon = originCoords ? originCoords[1] : 51.4069
    setParticipatingEventId(eventId)
    setIsBusy(true)
    setError('')
    try {
      const response = await axios.post(`/api/v1/exploration/events/${eventId}/participate`, {
        latitude: lat,
        longitude: lon,
      })
      const data = response.data
      if (data.status === 'success') {
        setMessage(data.message)
        if (data.progression) {
          setProgression(data.progression)
        }
        fetchUserProfile()
        fetchNearbyEvents(lat, lon)
        fetchEventLeaderboard(eventId)
        fetchEventActivities(eventId)
        fetchLeaderboard()
      } else {
        setError(data.message || "خطا در شرکت در رویداد")
      }
    } catch (err) {
      console.error("Error participating in event:", err)
      const errDetail = err.response?.data?.detail || "خطا در برقراری ارتباط با سرور."
      setError(errDetail)
    } finally {
      setIsBusy(false)
      setParticipatingEventId(null)
    }
  }

  const handleShareEvent = async (evt) => {
    if (!evt) return
    const shareUrl = `${window.location.origin}/events/${evt.id}`
    const shareText = `🎪 ${evt.title}\n\nیک رویداد کاوشگری در شهر پیدا کردم!\n+${evt.xp_reward} XP\n\nبرای مشاهده رویداد:\n${shareUrl}`

    if (navigator.share) {
      try {
        await navigator.share({
          title: evt.title,
          text: shareText,
          url: shareUrl,
        })
        setMessage("رویداد با موفقیت به اشتراک گذاشته شد. 🚀")
        return
      } catch (err) {
        if (err.name === 'AbortError') return
      }
    }

    copyLinkToClipboard(shareUrl)
  }

  const copyLinkToClipboard = async (url) => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url)
        setMessage("لینک رویداد کپی شد. 📋")
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = url
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        setMessage("لینک رویداد کپی شد. 📋")
      }
    } catch (err) {
      setMessage("خطا در کپی کردن لینک رویداد.")
    }
  }

  const fetchDeepLinkedEvent = useCallback(async (eventId) => {
    if (!eventId) return
    try {
      const lat = originCoords ? originCoords[0] : 35.7127
      const lon = originCoords ? originCoords[1] : 51.4069
      const response = await axios.get(`/api/v1/exploration/events/${eventId}?lat=${lat}&lon=${lon}`)
      if (response.data && response.data.status === 'success' && response.data.event) {
        const evt = response.data.event
        setNearbyEvents((prev) => {
          if (prev.some((e) => e.id === evt.id)) {
            return prev
          }
          return [evt, ...prev]
        })
        if (evt.latitude && evt.longitude) {
          setFlyToCoords([evt.latitude, evt.longitude])
        }
        fetchEventLeaderboard(evt.id)
        fetchEventActivities(evt.id)
        setMessage(`🎯 رویداد '${evt.title}' بارگذاری شد.`)
      }
    } catch (err) {
      console.error(`Error loading deep-linked event ${eventId}:`, err)
      const errDetail = err.response?.data?.detail || "رویداد مورد نظر یافت نشد."
      setError(errDetail)
    }
  }, [originCoords, fetchEventLeaderboard, fetchEventActivities])

  // Deep Link URL detection on mount (Phase 4.1.9)
  useEffect(() => {
    const path = window.location.pathname
    const hash = window.location.hash
    const query = new URLSearchParams(window.location.search)

    let eventIdMatch = path.match(/\/events\/(\d+)/) || hash.match(/#\/events\/(\d+)/)
    let eventId = eventIdMatch ? parseInt(eventIdMatch[1], 10) : (query.get('event') ? parseInt(query.get('event'), 10) : null)

    if (eventId) {
      fetchDeepLinkedEvent(eventId)
    }
  }, [fetchDeepLinkedEvent])

  useEffect(() => {
    if (isAuthenticated) {
      const lat = originCoords ? originCoords[0] : 35.7127
      const lon = originCoords ? originCoords[1] : 51.4069
      fetchNearbyEvents(lat, lon)
    }
  }, [isAuthenticated, originCoords, fetchNearbyEvents])
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
      if (response.data?.level_stats) {
        setProgression({
          level: response.data.level_stats.level,
          total_xp: response.data.score ?? response.data.level_stats.score ?? 0,
          xp_in_level: response.data.level_stats.xp_in_level,
          xp_needed_for_next: response.data.level_stats.xp_needed_for_next,
          progress_pct: response.data.level_stats.progress_pct,
        })
      }
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

  const fetchLeaderboard = useCallback(async (type = leaderboardType) => {
    setLeaderboardLoading(true)
    setLeaderboardError(false)
    try {
      const response = await axios.get(`/api/v1/leaderboard?type=${type}&limit=10`)
      setLeaderboardData(response.data)
    } catch (err) {
      console.error("Error fetching leaderboard:", err)
      setLeaderboardError(true)
    } finally {
      setLeaderboardLoading(false)
    }
  }, [leaderboardType])

  useEffect(() => {
    if (drawerOpen) {
      fetchLeaderboard(leaderboardType)
    }
  }, [drawerOpen, leaderboardType, fetchLeaderboard])

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
    setProgression({
      level: 1,
      total_xp: 0,
      xp_in_level: 0,
      xp_needed_for_next: 50,
      progress_pct: 0,
    })
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
      if (res.data.progression) {
        setProgression(res.data.progression)
      }
      if (res.data.xp_feedback) {
        const fb = res.data.xp_feedback
        if (fb.level_up) {
          setMessage(`🎉 ارتقا سطح! شما به سطح ${fb.new_level || res.data.progression?.level} رسیدید! 🌟`)
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

  const handleManualDiscoverPOI = useCallback(async (poiId) => {
    setIsBusy(true)
    try {
      const res = await axios.post(`/api/v1/exploration/pois/${poiId}/discover`)
      if (res.data.status === 'error') {
        setMessage(`⚠️ ${res.data.message}`)
        return
      }
      const xpEarned = res.data.xp_earned || 0
      const poiName = res.data.name || 'مکان جدید'
      if (res.data.just_discovered && xpEarned > 0) {
        setMessage(`✨ +${xpEarned} XP • مکان '${poiName}' کشف شد! 🎉`)
      } else {
        setMessage(`📍 مکان '${poiName}' قبلاً کشف شده است.`)
      }
      if (res.data.progression) {
        setProgression(res.data.progression)
      }
      fetchUserProfile()
      fetchPois()
    } catch (err) {
      console.error("Error discovering POI:", err)
      setError("خطا در کشف مکان")
    } finally {
      setIsBusy(false)
    }
  }, [fetchUserProfile, fetchPois])

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

        {/* 🌟 PRIMARY HUD PROGRESSION BAR (Level + Progress Bar + XP Counter) */}
        {isAuthenticated && (
          <div className="glass-panel" style={{
            padding: '8px 14px',
            display: 'flex',
            alignItems: 'center',
            justify: 'space-between',
            gap: '12px',
            borderRadius: '14px',
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.35)',
          }}>
            {/* Left Side: Level Badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                background: 'linear-gradient(135deg, #a855f7, #6366f1)',
                color: '#ffffff',
                fontWeight: 900,
                fontSize: '12px',
                padding: '3px 10px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(168, 85, 247, 0.4)',
                whiteSpace: 'nowrap',
              }}>
                سطح {progression.level || 1}
              </div>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-sub)' }}>
                {currentUser?.username || 'کاشف'}
              </span>
            </div>

            {/* Center: Visual Progress Bar */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', fontWeight: 700 }}>
                <span style={{ color: '#38bdf8' }}>پیشرفت سطح</span>
                <span style={{ color: 'var(--text-sub)' }}>
                  {progression.xp_in_level || 0} / {progression.xp_needed_for_next || 50} XP ({progression.progress_pct || 0}٪)
                </span>
              </div>
              <div style={{
                width: '100%',
                height: '7px',
                background: 'rgba(125, 125, 125, 0.2)',
                borderRadius: '4px',
                overflow: 'hidden',
                boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.3)',
              }}>
                <div style={{
                  width: `${Math.min(100, Math.max(0, progression.progress_pct || 0))}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #38bdf8, #a855f7, #ec4899)',
                  borderRadius: '4px',
                  transition: 'width 0.5s ease-in-out',
                }} />
              </div>
            </div>

            {/* Right Side: Total XP Counter */}
            <div style={{
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              padding: '3px 10px',
              borderRadius: '10px',
              fontSize: '11px',
              fontWeight: 800,
              color: '#38bdf8',
              whiteSpace: 'nowrap',
            }}>
              ⭐ {progression.total_xp ?? score ?? 0} XP
            </div>
          </div>
        )}

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

          {/* Section 2: PostGIS Fog & Exploration Statistics */}
          <div style={{ background: 'rgba(125,125,125,0.1)', padding: '12px', borderRadius: '12px', border: '1px solid var(--panel-border)' }}>
            <span style={{ fontWeight: 700, fontSize: '11px', color: '#10b981', display: 'block', marginBottom: '8px' }}>📊 آمار هویت کاشف</span>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px' }}>
              <div style={{ background: 'rgba(125,125,125,0.1)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-sub)', fontSize: '9px' }}>مناطق کشف‌شده</div>
                <div style={{ fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>🗺️ {userProfile?.stats?.discovered_areas_count ?? (discoveredPoints.length || 0)}</div>
              </div>
              <div style={{ background: 'rgba(125,125,125,0.1)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-sub)', fontSize: '9px' }}>اماکن فتح‌شده</div>
                <div style={{ fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>🏛️ {userProfile?.stats?.discovered_pois_count || 0}</div>
              </div>
              <div style={{ background: 'rgba(125,125,125,0.1)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-sub)', fontSize: '9px' }}>مساحت پوشش</div>
                <div style={{ fontWeight: 700, color: '#a855f7', marginTop: '2px' }}>📏 {userProfile?.stats?.explored_area_sqkm || (fogStats?.covered_area_sq_km || fogStats?.total_area_sqkm || 0)} km²</div>
              </div>
              <div style={{ background: 'rgba(125,125,125,0.1)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
                <div style={{ color: 'var(--text-sub)', fontSize: '9px' }}>تنوع دسته‌ها</div>
                <div style={{ fontWeight: 700, color: '#f59e0b', marginTop: '2px' }}>🌐 {userProfile?.stats?.discovered_categories_count || 0} دسته</div>
              </div>
            </div>
          </div>

          {/* Section 5: Milestones & Badges */}
          <div style={{ background: 'rgba(125,125,125,0.1)', padding: '12px', borderRadius: '12px', border: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontWeight: 700, fontSize: '11.5px', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '4px' }}>
              🏆 دستاوردها و مایلستون‌های کاوش
            </span>

            {userProfile?.badges && userProfile.badges.length > 0 && (
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '4px' }}>
                {userProfile.badges.map(b => (
                  <span key={b.name} style={{ background: 'rgba(245, 158, 11, 0.2)', border: '1px solid rgba(245, 158, 11, 0.4)', color: '#fcd34d', padding: '3px 8px', borderRadius: '10px', fontSize: '10px', fontWeight: 600 }}>
                    {b.icon} {b.name}
                  </span>
                ))}
              </div>
            )}

            {userProfile?.milestones && userProfile.milestones.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '200px', overflowY: 'auto' }}>
                {userProfile.milestones.map((m) => (
                  <div key={m.id} style={{ background: 'rgba(125,125,125,0.1)', padding: '8px 10px', borderRadius: '8px', border: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: '11px', color: m.is_completed ? '#10b981' : 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>{m.badge_icon || '⭐'}</span> {m.title}
                      </span>
                      <span style={{ fontSize: '10px', fontWeight: 800, color: m.is_completed ? '#10b981' : '#38bdf8' }}>
                        {m.is_completed ? `✓ (+${m.reward_points} XP)` : `${m.progress} / ${m.target}`}
                      </span>
                    </div>
                    <div style={{ fontSize: '9.5px', color: 'var(--text-sub)' }}>{m.description}</div>
                    {!m.is_completed && (
                      <div style={{ width: '100%', height: '4px', background: 'rgba(125,125,125,0.2)', borderRadius: '2px', overflow: 'hidden', marginTop: '2px' }}>
                        <div style={{ width: `${Math.min(100, (m.progress / Math.max(1, m.target)) * 100)}%`, height: '100%', background: 'linear-gradient(90deg, #38bdf8, #a855f7)' }} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 6: Recent Activity History */}
          {userProfile?.recent_activities && userProfile.recent_activities.length > 0 && (
            <div style={{ background: 'rgba(125,125,125,0.1)', padding: '12px', borderRadius: '12px', border: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span style={{ fontWeight: 700, fontSize: '11.5px', color: '#a855f7', display: 'flex', alignItems: 'center', gap: '4px' }}>
                📜 تاریخچه فعالیت‌های اخیر
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '160px', overflowY: 'auto' }}>
                {userProfile.recent_activities.map((act) => (
                  <div key={act.id} style={{ background: 'rgba(125,125,125,0.1)', padding: '6px 10px', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
                      <span>{act.icon}</span>
                      <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{act.title}</span>
                    </div>
                    <span style={{ fontSize: '10px', fontWeight: 800, color: '#38bdf8', whiteSpace: 'nowrap' }}>+{act.xp_value} XP</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 7: Social & Community City Leaderboard */}
          <div style={{ background: 'rgba(125,125,125,0.1)', padding: '12px', borderRadius: '12px', border: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 800, fontSize: '12px', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                🏆 رتبه‌بندی کاوشگران شهر
              </span>
              {leaderboardData?.current_user && (
                <span style={{ background: 'rgba(245, 158, 11, 0.2)', border: '1px solid rgba(245, 158, 11, 0.4)', color: '#fcd34d', fontSize: '9.5px', fontWeight: 800, padding: '2px 6px', borderRadius: '8px' }}>
                  رتبه شما: #{leaderboardData.current_user.rank}
                </span>
              )}
            </div>

            {/* Leaderboard Category Tabs */}
            <div style={{ display: 'flex', gap: '4px', background: 'rgba(125,125,125,0.15)', padding: '3px', borderRadius: '8px' }}>
              <button
                onClick={() => setLeaderboardType('overall')}
                style={{ flex: 1, background: leaderboardType === 'overall' ? '#f59e0b' : 'transparent', border: 'none', color: leaderboardType === 'overall' ? '#fff' : 'var(--text-sub)', padding: '4px 2px', borderRadius: '6px', fontSize: '9.5px', fontWeight: 700, cursor: 'pointer' }}>
                🏆 XP کل
              </button>
              <button
                onClick={() => setLeaderboardType('weekly')}
                style={{ flex: 1, background: leaderboardType === 'weekly' ? '#ef4444' : 'transparent', border: 'none', color: leaderboardType === 'weekly' ? '#fff' : 'var(--text-sub)', padding: '4px 2px', borderRadius: '6px', fontSize: '9.5px', fontWeight: 700, cursor: 'pointer' }}>
                🔥 هفته
              </button>
              <button
                onClick={() => setLeaderboardType('poi')}
                style={{ flex: 1, background: leaderboardType === 'poi' ? '#38bdf8' : 'transparent', border: 'none', color: leaderboardType === 'poi' ? '#fff' : 'var(--text-sub)', padding: '4px 2px', borderRadius: '6px', fontSize: '9.5px', fontWeight: 700, cursor: 'pointer' }}>
                📍 اماکن
              </button>
              <button
                onClick={() => setLeaderboardType('exploration')}
                style={{ flex: 1, background: leaderboardType === 'exploration' ? '#a855f7' : 'transparent', border: 'none', color: leaderboardType === 'exploration' ? '#fff' : 'var(--text-sub)', padding: '4px 2px', borderRadius: '6px', fontSize: '9.5px', fontWeight: 700, cursor: 'pointer' }}>
                🗺️ مناطق
              </button>
            </div>

            {/* Content States */}
            {leaderboardLoading ? (
              <div style={{ textAlign: 'center', padding: '12px 0', fontSize: '11px', color: 'var(--text-sub)' }}>
                در حال بارگذاری رتبه‌بندی...
              </div>
            ) : leaderboardError ? (
              <div style={{ textAlign: 'center', padding: '12px 0', fontSize: '11px', color: '#ef4444' }}>
                رتبه‌بندی فعلاً در دسترس نیست.
              </div>
            ) : leaderboardData?.entries && leaderboardData.entries.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '200px', overflowY: 'auto' }}>
                {leaderboardData.entries.map((entry) => {
                  const isSelf = currentUser && entry.user_id === currentUser.id
                  const medal = entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`
                  const unitLabel = leaderboardType === 'overall' || leaderboardType === 'weekly' ? 'XP' : leaderboardType === 'poi' ? 'مکان' : 'منطقه'
                  return (
                    <div
                      key={entry.user_id}
                      style={{
                        background: isSelf ? 'rgba(245, 158, 11, 0.15)' : 'rgba(125,125,125,0.1)',
                        border: isSelf ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid var(--panel-border)',
                        padding: '6px 10px',
                        borderRadius: '8px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
                        <span style={{ fontWeight: 800, minWidth: '22px', textAlign: 'center', color: entry.rank <= 3 ? '#fcd34d' : 'var(--text-sub)' }}>
                          {medal}
                        </span>
                        <span style={{ color: isSelf ? '#fcd34d' : 'var(--text-main)', fontWeight: isSelf ? 700 : 500 }}>
                          {entry.display_name} {isSelf && '(شما)'}
                        </span>
                      </div>
                      <span style={{ fontSize: '10.5px', fontWeight: 800, color: '#38bdf8' }}>
                        {entry.score.toLocaleString('fa-IR')} {unitLabel}
                      </span>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '12px 0', fontSize: '10.5px', color: 'var(--text-sub)', lineHeight: 1.4 }}>
                هنوز کاوشگری در این رتبه‌بندی نیست.<br />اولین نفری باش که شهر را کشف می‌کند!
              </div>
            )}
          </div>

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

      {/* 🎪 EVENT DISCOVERY & FILTERING HUD (Phase 4.1.8) */}
      <div className="glass-panel" style={{ position: 'absolute', top: '70px', right: '16px', zIndex: 999, width: '240px', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 800, fontSize: '12px', color: '#a855f7', display: 'flex', alignItems: 'center', gap: '4px' }}>
            🎪 رویدادهای کاوش ({nearbyEvents.length})
          </span>
          <span style={{ fontSize: '9px', color: 'var(--text-sub)', background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '6px' }}>
            {nearbyEvents.length} در محدوده
          </span>
        </div>

        {/* Category Filter Pills */}
        <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap' }}>
          {[
            { id: 'all', label: 'همه', icon: '📍' },
            { id: 'cultural', label: 'فرهنگی', icon: '🎨' },
            { id: 'historical', label: 'تاریخی', icon: '🏛️' },
            { id: 'challenge', label: 'چالش', icon: '⚡' },
            { id: 'nature', label: 'طبیعت', icon: '🌿' },
            { id: 'exploration', label: 'کاوشگری', icon: '🧭' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setEventFilterType(cat.id)}
              style={{
                background: eventFilterType === cat.id ? 'linear-gradient(135deg, #a855f7, #6366f1)' : 'rgba(255,255,255,0.05)',
                color: eventFilterType === cat.id ? '#fff' : 'var(--text-main)',
                border: eventFilterType === cat.id ? 'none' : '1px solid rgba(255,255,255,0.1)',
                borderRadius: '6px',
                padding: '2px 6px',
                fontSize: '9.5px',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}>
              {cat.icon} {cat.label}
            </button>
          ))}
        </div>

        {/* Status & Sort Select Row */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '9px', color: 'var(--text-sub)' }}>وضعیت:</span>
            <select
              value={eventFilterStatus}
              onChange={(e) => setEventFilterStatus(e.target.value)}
              style={{
                background: 'rgba(0,0,0,0.4)',
                color: 'var(--text-main)',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '6px',
                padding: '3px 5px',
                fontSize: '9.5px',
                fontFamily: 'Vazirmatn',
                cursor: 'pointer',
              }}>
              <option value="active">🔥 فعال</option>
              <option value="scheduled">⏳ به‌زودی</option>
              <option value="ending_soon">⏰ در حال پایان</option>
              <option value="all">📍 همه وضعیت‌ها</option>
              <option value="ended">🏁 پایان یافته</option>
            </select>
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '9px', color: 'var(--text-sub)' }}>مرتب‌سازی:</span>
            <select
              value={eventFilterSort}
              onChange={(e) => setEventFilterSort(e.target.value)}
              style={{
                background: 'rgba(0,0,0,0.4)',
                color: 'var(--text-main)',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '6px',
                padding: '3px 5px',
                fontSize: '9.5px',
                fontFamily: 'Vazirmatn',
                cursor: 'pointer',
              }}>
              <option value="distance">🧭 نزدیک‌ترین</option>
              <option value="xp">🎁 بیشترین XP</option>
              <option value="ending_soon">⏳ پایان نزدیک</option>
            </select>
          </div>
        </div>
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

        {/* 🎯 Viewport Density Handler (Phase 4.1.5) */}
        <ViewportDensityHandler onViewportChange={handleViewportChange} />

        {/* 🌡️ Heatmap Layer */}
        <HeatLayer points={heatPoints} enabled={showHeatmap} />

        {/* 🌫️ Atmospheric Canvas Fog of War Overlay */}
        <FogCanvasOverlay
          discoveredPoints={discoveredPoints}
          showFog={showFog}
          fogConfig={FOG_CONFIG}
        />

        {/* 📊 Event Density Heatmap Clusters Layer (Phase 4.1.5) */}
        {eventDensityClusters.map((cluster, cIdx) => {
          if (!cluster.latitude || !cluster.longitude) return null
          const radiusSize = Math.min(36, 12 + cluster.event_count * 4)

          return (
            <div key={`density-cluster-${cIdx}-${cluster.latitude}-${cluster.longitude}`}>
              <CircleMarker
                center={[cluster.latitude, cluster.longitude]}
                radius={radiusSize}
                pathOptions={{
                  color: '#a855f7',
                  fillColor: '#c084fc',
                  fillOpacity: 0.35,
                  weight: 2,
                }}
              />
              <Marker
                position={[cluster.latitude, cluster.longitude]}
                icon={createClusterCountIcon(cluster.event_count)}>
                <Popup>
                  <div style={{ padding: '6px', width: '210px', fontFamily: 'Vazirmatn' }}>
                    <div style={{ fontWeight: 800, fontSize: '13px', color: '#a855f7', marginBottom: '6px' }}>
                      🔥 تراکم رویدادها: {cluster.event_count} رویداد
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-sub)', marginBottom: '6px' }}>
                      تفکیک دسته‌بندی رویدادها در این محدوده:
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      {Object.entries(cluster.event_types || {}).map(([typeKey, count]) => {
                        const typeIcon = EVENT_TYPE_ICONS[typeKey] || '📍'
                        const typeColor = EVENT_TYPE_COLORS[typeKey] || '#a855f7'
                        return (
                          <div
                            key={typeKey}
                            style={{
                              display: 'flex',
                              justify: 'space-between',
                              fontSize: '10.5px',
                              background: 'rgba(255,255,255,0.05)',
                              padding: '3px 6px',
                              borderRadius: '4px',
                            }}>
                            <span style={{ color: typeColor, fontWeight: 700 }}>
                              {typeIcon} {typeKey}
                            </span>
                            <span style={{ fontWeight: 800 }}>{count} رویداد</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </Popup>
              </Marker>
            </div>
          )
        })}

        {/* 🎪 Interactive Exploration Events & Geofence Circles (Phase 4.1.3) */}
        {nearbyEvents.map((evt) => {
          if (!evt.latitude || !evt.longitude) return null
          const evtColor = EVENT_TYPE_COLORS[evt.event_type] || EVENT_TYPE_COLORS.default
          const evtIcon = EVENT_TYPE_ICONS[evt.event_type] || EVENT_TYPE_ICONS.default
          const distMeters = Math.round(evt.distance_meters)
          const distFormatted = formatDistancePersian(distMeters)

          return (
            <div key={`evt-layer-${evt.id}`}>
              {/* Geofence Circle Overlay */}
              <Circle
                center={[evt.latitude, evt.longitude]}
                radius={evt.radius_meters}
                pathOptions={{
                  color: evt.inside_geofence ? '#10b981' : evtColor,
                  fillColor: evtColor,
                  fillOpacity: evt.inside_geofence ? 0.25 : 0.15,
                  weight: evt.inside_geofence ? 3 : 2,
                  dashArray: evt.inside_geofence ? undefined : '6, 8',
                }}
              />

              {/* Event Marker & Interactive Popup */}
              <Marker
                position={[evt.latitude, evt.longitude]}
                icon={createCustomEventIcon(evt.event_type, evt.inside_geofence)}
                eventHandlers={{
                  click: () => {
                    fetchEventLeaderboard(evt.id)
                    fetchEventActivities(evt.id)
                  },
                }}>
                <Popup>
                  <div style={{ padding: '6px', width: '250px', fontFamily: 'Vazirmatn' }}>
                    {/* Header: Title & Event Type Badge */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: 800, fontSize: '13px', color: evtColor, display: 'flex', alignItems: 'center', gap: '4px' }}>
                        {evtIcon} {evt.title}
                      </span>
                      <span style={{
                        background: evt.already_participated ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: evt.already_participated ? '#10b981' : '#f59e0b',
                        border: evt.already_participated ? '1px solid #10b981' : '1px solid #f59e0b',
                        fontSize: '9px',
                        fontWeight: 800,
                        padding: '2px 6px',
                        borderRadius: '8px',
                        whiteSpace: 'nowrap'
                      }}>
                        {evt.already_participated ? '✓ تکمیل شده' : '🎪 رویداد ویژه'}
                      </span>
                    </div>

                    {/* Geofence & Participation Status Banner */}
                    {evt.already_participated ? (
                      <div style={{
                        background: 'rgba(16, 185, 129, 0.15)',
                        border: '1px solid #10b981',
                        borderRadius: '6px',
                        padding: '6px 8px',
                        fontSize: '10.5px',
                        fontWeight: 800,
                        color: '#10b981',
                        marginBottom: '8px',
                        textAlign: 'center'
                      }}>
                        ✓ شما قبلاً در این رویداد شرکت کرده‌اید.
                      </div>
                    ) : evt.inside_geofence ? (
                      <div style={{
                        background: 'rgba(16, 185, 129, 0.15)',
                        border: '1px solid #10b981',
                        borderRadius: '6px',
                        padding: '6px 8px',
                        fontSize: '10.5px',
                        fontWeight: 800,
                        color: '#10b981',
                        marginBottom: '8px',
                        textAlign: 'center'
                      }}>
                        ✨ شما در محدوده رویداد هستید! (فاصله: {distFormatted})
                      </div>
                    ) : (
                      <div style={{
                        background: 'rgba(245, 158, 11, 0.15)',
                        border: '1px solid #f59e0b',
                        borderRadius: '6px',
                        padding: '6px 8px',
                        fontSize: '10.5px',
                        fontWeight: 700,
                        color: '#f59e0b',
                        marginBottom: '8px',
                        textAlign: 'center'
                      }}>
                        📍 برای شرکت در رویداد وارد محدوده شوید (فاصله: {distFormatted})
                      </div>
                    )}

                    {/* Description */}
                    <p style={{ fontSize: '11px', color: 'var(--text-sub)', margin: '0 0 8px 0', lineHeight: 1.45 }}>
                      {evt.description}
                    </p>

                    {/* Info Pill Grid: XP & Radius */}
                    <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
                      <span style={{ flex: 1, background: 'rgba(168, 85, 247, 0.15)', border: '1px solid rgba(168, 85, 247, 0.3)', color: '#c084fc', padding: '3px 6px', borderRadius: '6px', fontSize: '10px', fontWeight: 700, textAlign: 'center' }}>
                        🎁 +{evt.xp_reward} XP
                      </span>
                      <span style={{ flex: 1, background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38bdf8', padding: '3px 6px', borderRadius: '6px', fontSize: '10px', fontWeight: 700, textAlign: 'center' }}>
                        ⭕ شعاع: {evt.radius_meters}m
                      </span>
                    </div>

                    {/* 🏆 Event Leaderboard & 🌍 Community Challenge Section (Phase 4.1.6) */}
                    {(() => {
                      const lbData = eventLeaderboards[evt.id]
                      if (!lbData) {
                        return (
                          <div style={{ fontSize: '9.5px', color: 'var(--text-sub)', textAlign: 'center', margin: '4px 0 8px 0' }}>
                            ⌛ در حال بارگذاری اطلاعات رتبه‌بندی...
                          </div>
                        )
                      }
                      const challenge = lbData.challenge || {}
                      const isCompleted = challenge.status === 'completed'
                      const isExpired = challenge.status === 'expired'

                      return (
                        <div style={{ background: 'rgba(0, 0, 0, 0.25)', borderRadius: '8px', padding: '6px 8px', marginBottom: '8px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                          {/* 🌍 Community Challenge */}
                          <div style={{ marginBottom: '6px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                              <span style={{ fontSize: '10px', fontWeight: 800, color: '#38bdf8' }}>
                                🌍 چالش جامعه
                              </span>
                              <span style={{
                                fontSize: '8.5px',
                                fontWeight: 800,
                                padding: '1px 5px',
                                borderRadius: '4px',
                                background: isCompleted ? 'rgba(16, 185, 129, 0.2)' : isExpired ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.2)',
                                color: isCompleted ? '#10b981' : isExpired ? '#ef4444' : '#38bdf8',
                              }}>
                                {isCompleted ? '✓ تکـمیل شد' : isExpired ? 'منقضی' : '🔥 فعال'}
                              </span>
                            </div>

                            {/* Progress Bar */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--text-sub)', marginBottom: '2px' }}>
                              <span>مشارکت: {challenge.current_participants} / {challenge.target_participants}</span>
                              <span>{challenge.participants_progress_pct}%</span>
                            </div>
                            <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${challenge.participants_progress_pct}%`, background: isCompleted ? '#10b981' : 'linear-gradient(90deg, #38bdf8, #a855f7)', borderRadius: '2px', transition: 'width 0.4s ease' }} />
                            </div>
                          </div>

                          {/* 🏆 Top Explorers & Current User Rank */}
                          <div>
                            <div style={{ fontSize: '10px', fontWeight: 800, color: '#f59e0b', marginBottom: '3px', display: 'flex', justifyContent: 'space-between' }}>
                              <span>🏆 کاوشگران برتر</span>
                              {lbData.current_user && lbData.current_user.has_participated ? (
                                <span style={{ color: '#10b981', fontWeight: 900 }}>
                                  رتبه شما: #{lbData.current_user.rank}
                                </span>
                              ) : (
                                <span style={{ color: 'var(--text-sub)', fontSize: '8.5px', fontWeight: 500 }}>
                                  شرکت نکرده‌اید
                                </span>
                              )}
                            </div>

                            {lbData.entries && lbData.entries.length > 0 ? (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                {lbData.entries.slice(0, 3).map((entry) => {
                                  const badge = entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`
                                  return (
                                    <div key={`lb-${evt.id}-${entry.user_id}`} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9.5px', background: 'rgba(255,255,255,0.04)', padding: '2px 4px', borderRadius: '4px' }}>
                                      <span>{badge} {entry.display_name}</span>
                                      <span style={{ fontWeight: 800, color: '#c084fc' }}>+{entry.score} XP</span>
                                    </div>
                                  )
                                })}
                              </div>
                            ) : (
                              <div style={{ fontSize: '9px', color: 'var(--text-sub)', fontStyle: 'italic' }}>
                                هنوز کسی شرکت نکرده است.
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })()}

                    {/* 📢 Event Activity Feed (Phase 4.1.7) */}
                    {(() => {
                      const acts = eventActivities[evt.id] || []
                      if (acts.length === 0) return null

                      return (
                        <div style={{ background: 'rgba(0, 0, 0, 0.2)', borderRadius: '8px', padding: '5px 7px', marginBottom: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                          <div style={{ fontSize: '9.5px', fontWeight: 800, color: '#38bdf8', marginBottom: '3px' }}>
                            📢 فعالیت اخیر کاوشگران
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            {acts.slice(0, 2).map((act) => {
                              const isComp = act.activity_type === 'challenge_completed'
                              return (
                                <div
                                  key={`act-${act.id}`}
                                  style={{
                                    fontSize: '8.5px',
                                    color: isComp ? '#10b981' : 'var(--text-main)',
                                    background: isComp ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.03)',
                                    padding: '2px 4px',
                                    borderRadius: '4px',
                                    lineHeight: 1.3,
                                  }}>
                                  {isComp ? '🏆 ' : '⚡ '}
                                  {act.description}
                                  {act.xp_earned > 0 && <span style={{ color: '#c084fc', fontWeight: 700 }}> (+{act.xp_earned} XP)</span>}
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })()}

                    {/* Interactive CTA & Status Handling */}
                    {evt.status === 'scheduled' ? (
                      <button
                        disabled
                        style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid #f59e0b', color: '#f59e0b', width: '100%', padding: '6.5px', borderRadius: '8px', cursor: 'default', fontWeight: 700, fontSize: '10.5px' }}>
                        ⏳ این رویداد هنوز شروع نشده است.
                      </button>
                    ) : evt.status === 'ended' ? (
                      <button
                        disabled
                        style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#ef4444', width: '100%', padding: '6.5px', borderRadius: '8px', cursor: 'default', fontWeight: 700, fontSize: '10.5px' }}>
                        🏁 این رویداد به پایان رسیده است.
                      </button>
                    ) : evt.already_participated ? (
                      <button
                        disabled
                        style={{ background: 'rgba(125,125,125,0.2)', border: '1px solid var(--panel-border)', color: 'var(--text-sub)', width: '100%', padding: '6.5px', borderRadius: '8px', cursor: 'default', fontWeight: 700, fontSize: '11px' }}>
                        ✓ شرکت شده (کسب امتیاز انجام شد)
                      </button>
                    ) : evt.inside_geofence ? (
                      <button
                        onClick={() => handleParticipateEvent(evt.id)}
                        disabled={participatingEventId === evt.id}
                        style={{ background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', color: '#fff', width: '100%', padding: '6.5px', borderRadius: '8px', cursor: 'pointer', fontWeight: 800, fontSize: '11px' }}>
                        {participatingEventId === evt.id ? '⌛ در حال ثبت مشارکت...' : `⚡ شرکت در رویداد (+${evt.xp_reward} XP)`}
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          setFlyToCoords([evt.latitude, evt.longitude])
                          setMessage(`نقشه به سمت رویداد '${evt.title}' هدایت شد.`)
                        }}
                        style={{ background: 'linear-gradient(135deg, #38bdf8, #3b82f6)', border: 'none', color: '#fff', width: '100%', padding: '6.5px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, fontSize: '11px' }}>
                        🧭 هدایت نقشه به رویداد
                      </button>
                    )}

                    {/* 🔗 Event Share & Social Link Actions (Phase 4.1.9) */}
                    <div style={{ display: 'flex', gap: '4px', marginTop: '6px' }}>
                      <button
                        onClick={() => handleShareEvent(evt)}
                        style={{ flex: 1, background: 'linear-gradient(135deg, #a855f7, #6366f1)', border: 'none', color: '#fff', padding: '5.5px', borderRadius: '6px', cursor: 'pointer', fontWeight: 700, fontSize: '10px' }}>
                        🔗 اشتراک‌گذاری
                      </button>
                      <button
                        onClick={() => copyLinkToClipboard(`${window.location.origin}/events/${evt.id}`)}
                        style={{ background: 'rgba(255, 255, 255, 0.08)', border: '1px solid rgba(255, 255, 255, 0.15)', color: 'var(--text-main)', padding: '5.5px 8px', borderRadius: '6px', cursor: 'pointer', fontWeight: 700, fontSize: '10px' }}>
                        📋 کپی لینک
                      </button>
                    </div>
                  </div>
                </Popup>
              </Marker>
            </div>
          )
        })}

        {/* 📍 Interactive POI Discovery Cards & Markers */}
        {pois.map((poi) => {
          if (!poi.lat || !poi.lon) return null
          const isDisc = poi.discovery_state === 'discovered' || (poi.is_discovered ?? true)
          const poiRarity = poi.rarity || 'common'
          const rCfg = RARITY_CONFIG[poiRarity] || RARITY_CONFIG.common
          const distMeters = originCoords ? getDistanceMeters(originCoords[0], originCoords[1], poi.lat, poi.lon) : null
          const distText = distMeters != null ? formatDistancePersian(distMeters) : null

          let proximityText = ''
          if (distMeters != null && !isDisc) {
            if (distMeters <= 100) {
              proximityText = `✨ بسیار نزدیک! (${distText})`
            } else if (distMeters <= 300) {
              proximityText = `🧭 در حال نزدیک شدن... (${distText})`
            } else {
              proximityText = `📍 حدود ${distText} تا این مکان`
            }
          }

          return (
            <Marker
              key={poi.id}
              position={[poi.lat, poi.lon]}
              icon={createCustomCategoryIcon(poi.category, poi.match_percentage, isDisc, poi.just_discovered, poiRarity)}>
              <Popup>
                <div style={{ padding: '6px', width: '230px', fontFamily: 'Vazirmatn' }}>
                  
                  {/* Header: Title + Rarity Badge */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 800, fontSize: '13px', color: isDisc ? (CATEGORY_COLORS[poi.category] || '#38bdf8') : '#a855f7', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      {isDisc ? (CATEGORY_ICONS[poi.category] || '📍') : '❓'} {poi.name}
                    </span>
                    <span style={{
                      background: rCfg.bg,
                      color: rCfg.color,
                      border: `1px solid ${rCfg.border}`,
                      fontSize: '9px',
                      fontWeight: 800,
                      padding: '2px 6px',
                      borderRadius: '8px',
                      whiteSpace: 'nowrap'
                    }}>
                      {rCfg.icon} {rCfg.label}
                    </span>
                  </div>

                  {/* Distance Hint Banner */}
                  {distText && (
                    <div style={{
                      background: 'rgba(56, 189, 248, 0.1)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      borderRadius: '6px',
                      padding: '4px 8px',
                      fontSize: '10px',
                      fontWeight: 700,
                      color: '#38bdf8',
                      marginBottom: '8px',
                      textAlign: 'center'
                    }}>
                      {proximityText || `📍 فاصله: ${distText}`}
                    </div>
                  )}

                  {/* Description */}
                  <p style={{ fontSize: '11px', color: 'var(--text-sub)', margin: '0 0 10px 0', lineHeight: 1.45 }}>
                    {poi.description || (isDisc ? 'مکان شاخص کلان‌شهر تهران' : 'این مکان هنوز کشف نشده است. برای کشف آن به محدوده نزدیک شوید!')}
                  </p>

                  {/* Action Buttons */}
                  {isDisc ? (
                    <button
                      onClick={() => {
                        setDestCoords([poi.lat, poi.lon])
                        setDestInput(poi.name)
                        setDrawerOpen(true)
                      }}
                      style={{ background: 'linear-gradient(135deg, #38bdf8, #3b82f6)', border: 'none', color: '#fff', width: '100%', padding: '6px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, fontSize: '11px' }}>
                      🎯 مسیریابی به این مکان
                    </button>
                  ) : (
                    <button
                      onClick={() => handleManualDiscoverPOI(poi.id)}
                      style={{ background: 'linear-gradient(135deg, #a855f7, #ec4899)', border: 'none', color: '#fff', width: '100%', padding: '6px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, fontSize: '11px' }}>
                      🔍 کشف این مکان (+{poi.xp_reward || 25} XP)
                    </button>
                  )}
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