import { useState, useEffect } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'

function App() {
  const [apiStatus, setApiStatus] = useState({
    online: false,
    modelLoaded: false,
    numUsers: '-',
    numItems: '-',
    checking: true
  })

  const [showRecommendations, setShowRecommendations] = useState(false)

  // Check API health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE}/health`)
        const data = await response.json()

        setApiStatus({
          online: true,
          modelLoaded: data.model_loaded,
          numUsers: data.num_users?.toLocaleString() || '-',
          numItems: data.num_items?.toLocaleString() || '-',
          checking: false
        })
      } catch (error) {
        setApiStatus({
          online: false,
          modelLoaded: false,
          numUsers: '-',
          numItems: '-',
          checking: false
        })
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const scrollToRecommendations = () => {
    setShowRecommendations(true)
    setTimeout(() => {
      document.getElementById('recommendations')?.scrollIntoView({ behavior: 'smooth' })
    }, 100)
  }

  return (
    <>
      <div className="bg-grid"></div>
      <div className="app">
        {/* Hero Section - Matches the image design */}
        <section className="hero-section">
          <div className="hero-line"></div>
          <p className="collection-label">Recommendation System</p>
          <h1 className="hero-title">Find Your<br />Perfect Match</h1>
          <p className="hero-description">
            Redefining the standard of product discovery with our AI-powered
            recommendation engine. Impeccable matching meets contemporary technology.
          </p>
          <button className="view-collection-btn" onClick={scrollToRecommendations}>
            View Recommendations <span className="arrow">→</span>
          </button>
        </section>

        {/* Recommendations Section */}
        {showRecommendations && (
          <section id="recommendations" className="recommendations-section">
            <div className="section-header">
              <h2 className="section-title">Test Console</h2>
              <p className="section-subtitle">
                Netflix-style ALS Collaborative Filtering
              </p>
            </div>

            {/* Status Bar */}
            <div className="status-bar">
              <div className="status-item">
                <div className={`status-dot ${apiStatus.modelLoaded ? 'online' : 'offline'}`}></div>
                <span>{apiStatus.checking ? 'Checking API...' : apiStatus.modelLoaded ? 'Model Ready' : 'Model Not Loaded'}</span>
              </div>
              <div className="status-item">
                <span>👥 Users: <strong>{apiStatus.numUsers}</strong></span>
              </div>
              <div className="status-item">
                <span>📦 Items: <strong>{apiStatus.numItems}</strong></span>
              </div>
            </div>

            <div className="cards-grid">
              <UserRecommendationsCard />
              <SimilarProductsCard />
              <OutfitMatchingCard />
            </div>

            <footer>
              <p>E-Commerce Recommendation API • <a href="/docs" target="_blank" rel="noopener noreferrer">API Docs</a></p>
            </footer>
          </section>
        )}
      </div>
    </>
  )
}

// User Recommendations Card
function UserRecommendationsCard() {
  const [userId, setUserId] = useState('')
  const [limit, setLimit] = useState(10)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const fetchRecommendations = async () => {
    if (!userId) {
      setError('Please enter a User ID')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await fetch(`${API_BASE}/recommendations/user/${userId}?limit=${limit}`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch recommendations')
      }

      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') fetchRecommendations()
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">👤</div>
        <div>
          <div className="card-title">User Recommendations</div>
          <div className="card-subtitle">Get personalized product suggestions</div>
        </div>
      </div>
      <div className="card-body">
        <div className="input-group">
          <div className="input-wrapper">
            <label>User ID</label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter user ID (e.g., 1, 10, 100)"
            />
          </div>
          <div className="input-wrapper" style={{ maxWidth: '100px' }}>
            <label>Limit</label>
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              min="1"
              max="100"
            />
          </div>
        </div>
        <button className="submit-btn" onClick={fetchRecommendations} disabled={loading}>
          <span>🔍</span> Get Recommendations
        </button>
        <ResultsDisplay loading={loading} error={error} results={results?.recommendations} message={results?.message} />
      </div>
    </div>
  )
}

// Similar Products Card
function SimilarProductsCard() {
  const [productId, setProductId] = useState('')
  const [limit, setLimit] = useState(10)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const fetchSimilar = async () => {
    if (!productId) {
      setError('Please enter a Product ID')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await fetch(`${API_BASE}/recommendations/product/${productId}?limit=${limit}`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch similar products')
      }

      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') fetchSimilar()
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">📦</div>
        <div>
          <div className="card-title">Similar Products</div>
          <div className="card-subtitle">Find products like this one</div>
        </div>
      </div>
      <div className="card-body">
        <div className="input-group">
          <div className="input-wrapper">
            <label>Product ID</label>
            <input
              type="text"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter product ID (e.g., 1, 10, 100)"
            />
          </div>
          <div className="input-wrapper" style={{ maxWidth: '100px' }}>
            <label>Limit</label>
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              min="1"
              max="100"
            />
          </div>
        </div>
        <button className="submit-btn" onClick={fetchSimilar} disabled={loading}>
          <span>🔍</span> Find Similar
        </button>
        <ResultsDisplay loading={loading} error={error} results={results?.similar_products} message={results?.message} />
      </div>
    </div>
  )
}

// Outfit Matching Card
function OutfitMatchingCard() {
  const [itemId, setItemId] = useState('')
  const [limitPerType, setLimitPerType] = useState(1)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const fetchOutfit = async () => {
    if (!itemId) {
      setError('Please enter an Item ID')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await fetch(`${API_BASE}/recommendations/outfit/${itemId}?limit=30&limit_per_type=${limitPerType}`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch outfit matches')
      }

      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') fetchOutfit()
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">👔</div>
        <div>
          <div className="card-title">Outfit Matching</div>
          <div className="card-subtitle">Find complementary items (jeans → shirt, shoes, jacket)</div>
        </div>
      </div>
      <div className="card-body">
        <div className="input-group">
          <div className="input-wrapper">
            <label>Base Item ID</label>
            <input
              type="text"
              value={itemId}
              onChange={(e) => setItemId(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter item ID (e.g., 1 for jeans)"
            />
          </div>
          <div className="input-wrapper" style={{ maxWidth: '120px' }}>
            <label>Per Category</label>
            <input
              type="number"
              value={limitPerType}
              onChange={(e) => setLimitPerType(e.target.value)}
              min="1"
              max="10"
            />
          </div>
        </div>
        <button className="submit-btn" onClick={fetchOutfit} disabled={loading}>
          <span>👗</span> Match Outfit
        </button>
        <OutfitResultsDisplay loading={loading} error={error} results={results} />
      </div>
    </div>
  )
}

// Results Display Component
function ResultsDisplay({ loading, error, results, message }) {
  if (loading) {
    return (
      <div className="results-container">
        <div className="loading">
          <div className="spinner"></div>
          <span>Fetching recommendations...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="results-container">
        <div className="message warning">⚠️ {error}</div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="results-container">
        <div className="empty-state">
          <div className="empty-state-icon">🎯</div>
          <p className="empty-state-text">Enter an ID to see recommendations</p>
        </div>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="results-container">
        <div className="message info">ℹ️ {message || 'No results found'}</div>
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <p className="empty-state-text">Try a different ID</p>
        </div>
      </div>
    )
  }

  return (
    <div className="results-container">
      <div className="results-header">
        <span className="results-title">Results</span>
        <span className="results-count">{results.length} items</span>
      </div>
      <div className="results-grid">
        {results.map((item, index) => (
          <div
            key={item.item_id}
            className="result-item"
            style={{ animationDelay: `${index * 0.05}s` }}
          >
            <div className="result-item-id">#{item.item_id}</div>
            <div className="result-item-score">{item.score.toFixed(4)}</div>
            <div className="result-item-label">Product ID</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Outfit Results Display Component
function OutfitResultsDisplay({ loading, error, results }) {
  if (loading) {
    return (
      <div className="results-container">
        <div className="loading">
          <div className="spinner"></div>
          <span>Finding complementary outfit items...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="results-container">
        <div className="message warning">⚠️ {error}</div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="results-container">
        <div className="empty-state">
          <div className="empty-state-icon">👔</div>
          <p className="empty-state-text">Enter an Item ID to find complementary outfit pieces</p>
        </div>
      </div>
    )
  }

  if (!results.outfit_items || results.outfit_items.length === 0) {
    return (
      <div className="results-container">
        <div className="message info">ℹ️ {results.message || 'No complementary items found'}</div>
        <div className="empty-state">
          <div className="empty-state-icon">👔</div>
          <p className="empty-state-text">Try a different Item ID (1-25)</p>
        </div>
      </div>
    )
  }

  return (
    <div className="results-container">
      {results.base_category && (
        <div className="base-category-badge">Base: {results.base_category}</div>
      )}
      <div className="results-header">
        <span className="results-title">Complementary Items</span>
        <span className="results-count">{results.outfit_items.length} items</span>
      </div>
      <div className="results-grid">
        {results.outfit_items.map((item, index) => (
          <div
            key={item.item_id}
            className="result-item"
            style={{ animationDelay: `${index * 0.05}s` }}
          >
            <div className="result-item-id">#{item.item_id}</div>
            <div className="result-item-score">{item.score.toFixed(4)}</div>
            <div className="result-item-category">{item.category}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
