import { useState, useEffect, useRef } from 'react'

// Simple SVG Icons
const SearchIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
)

const PlayIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M8 5v14l11-7z"/>
  </svg>
)

const PauseIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
  </svg>
)

interface Render {
  id: string
  style_phrase: string
  model_key: string
  base_prompt: string
  image_path: string
  thumb_path: string
  created_at: string
}

interface SearchResult {
  results: Render[]
  total: number
  offset: number
  limit: number
  query: string | null
}

export default function Gallery() {
  const [renders, setRenders] = useState<Render[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchFocused, setSearchFocused] = useState(false)
  const [isAutoScrolling, setIsAutoScrolling] = useState(true)
  const [selectedRender, setSelectedRender] = useState<Render | null>(null)

  const galleryRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const autoScrollRef = useRef<NodeJS.Timeout>()

  // API base URL - adapt for Vercel deployment
  const API_BASE = process.env.NODE_ENV === 'production'
    ? '/api'  // Vercel API routes
    : 'http://localhost:8000/api'  // Local FastAPI

  // Load initial data
  useEffect(() => {
    loadDefaultRenders()
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === '/') {
        e.preventDefault()
        searchInputRef.current?.focus()
        setSearchFocused(true)
      } else if (e.key === ' ') {
        e.preventDefault()
        toggleAutoScroll()
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault()
        scrollGallery(-200)
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        scrollGallery(200)
      } else if (e.key === 'Escape') {
        setSelectedRender(null)
        setSearchFocused(false)
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [])

  // Auto-scroll functionality
  useEffect(() => {
    if (isAutoScrolling && galleryRef.current) {
      autoScrollRef.current = setInterval(() => {
        scrollGallery(20) // 20px per interval for steady readable speed
      }, 100)
    } else {
      if (autoScrollRef.current) {
        clearInterval(autoScrollRef.current)
      }
    }

    return () => {
      if (autoScrollRef.current) {
        clearInterval(autoScrollRef.current)
      }
    }
  }, [isAutoScrolling])

  const loadDefaultRenders = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/default?limit=10`)
      const data: { results: Render[] } = await response.json()
      setRenders(data.results)
    } catch (error) {
      console.error('Failed to load renders:', error)
    } finally {
      setLoading(false)
    }
  }

  const searchRenders = async (query: string) => {
    try {
      setLoading(true)
      const url = query
        ? `${API_BASE}/search?q=${encodeURIComponent(query)}&limit=10`
        : `${API_BASE}/default?limit=10`

      const response = await fetch(url)
      const data: SearchResult = await response.json()
      setRenders(data.results)

      // Reset scroll position
      if (galleryRef.current) {
        galleryRef.current.scrollLeft = 0
      }
    } catch (error) {
      console.error('Failed to search renders:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    searchRenders(searchQuery)
    setSearchFocused(false)
  }

  const scrollGallery = (amount: number) => {
    if (galleryRef.current) {
      galleryRef.current.scrollLeft += amount
    }
  }

  const toggleAutoScroll = () => {
    setIsAutoScrolling(!isAutoScrolling)
  }

  const handleMouseEnter = () => {
    setIsAutoScrolling(false)
  }

  const handleMouseLeave = () => {
    setIsAutoScrolling(true)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white relative overflow-hidden">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-30 flex justify-between items-center p-6">
        <div className="text-xl font-bold">AI Gallery</div>

        {/* Search Box */}
        <div className={`transition-all duration-300 ${
          searchFocused ? 'fixed inset-0 bg-black/50 flex items-center justify-center z-50' : ''
        }`}>
          <form
            onSubmit={handleSearch}
            className={`transition-all duration-300 ${
              searchFocused
                ? 'w-96 bg-gray-800 p-8 rounded-lg shadow-2xl'
                : 'w-64'
            }`}
          >
            <div className="relative">
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                <SearchIcon />
              </div>
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setTimeout(() => setSearchFocused(false), 200)}
                placeholder="Search styles and models..."
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
              />
            </div>
            {searchFocused && (
              <div className="mt-4 text-sm text-gray-400">
                Try: "oil painting", "pixel art", "watercolor"
              </div>
            )}
          </form>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-4">
          <button
            onClick={toggleAutoScroll}
            className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
          >
            {isAutoScrolling ? <PauseIcon /> : <PlayIcon />}
          </button>
          <div className="text-sm bg-gray-800 px-3 py-1 rounded-full">
            0 credits • Buy more
          </div>
        </div>
      </header>

      {/* Main Gallery */}
      <div className="h-screen flex items-center">
        <div
          ref={galleryRef}
          className="w-full h-96 overflow-x-auto overflow-y-hidden scrollbar-hide"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          <div className="flex h-full" style={{ width: `${renders.length * 210}px` }}>
            {/* Row 1 */}
            <div className="flex flex-col h-full">
              <div className="flex h-48">
                {renders.slice(0, Math.ceil(renders.length / 2)).map((render, index) => (
                  <div
                    key={`top-${render.id}`}
                    className="w-48 h-48 m-1 bg-gray-800 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-blue-500 transition-all group"
                    onClick={() => setSelectedRender(render)}
                  >
                    <img
                      src={`${API_BASE}/images/${render.id}?thumb=true`}
                      alt={render.style_phrase}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="%23374151"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="white">${render.style_phrase}</text></svg>`
                      }}
                    />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-end p-3">
                      <div className="text-white text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="font-medium">{render.style_phrase}</div>
                        <div className="text-xs text-gray-300">{render.model_key}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Row 2 */}
              <div className="flex h-48">
                {renders.slice(Math.ceil(renders.length / 2)).map((render, index) => (
                  <div
                    key={`bottom-${render.id}`}
                    className="w-48 h-48 m-1 bg-gray-800 rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-blue-500 transition-all group relative"
                    onClick={() => setSelectedRender(render)}
                  >
                    <img
                      src={`${API_BASE}/images/${render.id}?thumb=true`}
                      alt={render.style_phrase}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="%23374151"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="white">${render.style_phrase}</text></svg>`
                      }}
                    />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-end p-3">
                      <div className="text-white text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="font-medium">{render.style_phrase}</div>
                        <div className="text-xs text-gray-300">{render.model_key}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="text-white">Loading...</div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedRender && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg max-w-4xl max-h-[90vh] overflow-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-bold">{selectedRender.style_phrase}</h2>
                  <p className="text-gray-400">{selectedRender.model_key}</p>
                </div>
                <button
                  onClick={() => setSelectedRender(null)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="mb-4">
                <img
                  src={`${API_BASE}/images/${selectedRender.id}`}
                  alt={selectedRender.style_phrase}
                  className="w-full max-w-2xl mx-auto rounded-lg"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement
                    target.src = `${API_BASE}/images/${selectedRender.id}?thumb=true`
                  }}
                />
              </div>

              <div className="text-sm text-gray-300 mb-4">
                <p><strong>Prompt:</strong> {selectedRender.base_prompt}</p>
              </div>

              <div className="flex space-x-4">
                <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors">
                  Apply this style
                </button>
                <button className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors">
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts Help */}
      <div className="absolute bottom-4 left-4 text-xs text-gray-500">
        Press / to search • Space to play/pause • ← → to scroll • ESC to close
      </div>

      <style jsx>{`
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  )
}