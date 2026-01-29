import { useState, useEffect, useCallback } from 'react'
import './App.css'

function App() {
    const [jobs, setJobs] = useState([])
    const [loading, setLoading] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [suggestions, setSuggestions] = useState([])
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [experience, setExperience] = useState('')
    const [dateFilter, setDateFilter] = useState('')
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [stats, setStats] = useState({ total: 0, sources: {} })

    const API_URL = 'http://localhost:5000/api'

    // Fetch jobs
    const fetchJobs = useCallback(async () => {
        setLoading(true)
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: '20',
                ...(searchTerm && { role: searchTerm }),
                ...(experience && { experience }),
                ...(dateFilter && { date: dateFilter })
            })

            const res = await fetch(`${API_URL}/jobs?${params}`)
            const data = await res.json()
            setJobs(data.jobs || [])
            setTotalPages(data.pages || 1)
        } catch (err) {
            console.error('Error fetching jobs:', err)
        } finally {
            setLoading(false)
        }
    }, [page, searchTerm, experience, dateFilter])

    // Fetch stats
    const fetchStats = async () => {
        try {
            const res = await fetch(`${API_URL}/stats`)
            const data = await res.json()
            setStats(data)
        } catch (err) {
            console.error('Error fetching stats:', err)
        }
    }

    // Fetch role suggestions
    const fetchSuggestions = async (query) => {
        if (query.length < 2) {
            setSuggestions([])
            return
        }
        try {
            const res = await fetch(`${API_URL}/roles?q=${encodeURIComponent(query)}`)
            const data = await res.json()
            setSuggestions(data)
        } catch (err) {
            console.error('Error fetching suggestions:', err)
        }
    }

    useEffect(() => {
        fetchJobs()
    }, [page, searchTerm, experience, dateFilter])

    useEffect(() => {
        fetchStats()
    }, [])

    // Debounce search input
    useEffect(() => {
        const timer = setTimeout(() => {
            if (searchTerm) {
                fetchSuggestions(searchTerm)
            }
        }, 300)
        return () => clearTimeout(timer)
    }, [searchTerm])

    const handleSearch = (e) => {
        e.preventDefault()
        setPage(1)
        setShowSuggestions(false)
        fetchJobs()
    }

    const selectSuggestion = (role) => {
        setSearchTerm(role)
        setShowSuggestions(false)
        setPage(1)
    }

    const formatDate = (dateStr) => {
        if (!dateStr) return 'Unknown'
        const date = new Date(dateStr)
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    }

    return (
        <div className="app">
            <header className="header">
                <h1>🔍 Job Discovery</h1>
                <p className="subtitle">{stats.total.toLocaleString()} jobs from {Object.keys(stats.sources || {}).length} sources</p>
            </header>

            <main className="main">
                {/* Search & Filters */}
                <section className="filters-section">
                    <form onSubmit={handleSearch} className="search-form">
                        <div className="search-input-wrapper">
                            <input
                                type="text"
                                placeholder="Search roles (e.g., Backend Engineer, DevOps...)"
                                value={searchTerm}
                                onChange={(e) => {
                                    setSearchTerm(e.target.value)
                                    setShowSuggestions(true)
                                }}
                                onFocus={() => setShowSuggestions(true)}
                                className="search-input"
                            />
                            {showSuggestions && suggestions.length > 0 && (
                                <ul className="suggestions">
                                    {suggestions.map((role, idx) => (
                                        <li key={idx} onClick={() => selectSuggestion(role)}>
                                            {role}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                        <button type="submit" className="search-btn">Search</button>
                    </form>

                    <div className="filter-row">
                        <select
                            value={experience}
                            onChange={(e) => { setExperience(e.target.value); setPage(1); }}
                            className="filter-select"
                        >
                            <option value="">All Experience</option>
                            <option value="entry">Entry Level</option>
                            <option value="mid">Mid Level</option>
                            <option value="senior">Senior Level</option>
                        </select>

                        <select
                            value={dateFilter}
                            onChange={(e) => { setDateFilter(e.target.value); setPage(1); }}
                            className="filter-select"
                        >
                            <option value="">All Time</option>
                            <option value="7">Last 7 Days</option>
                            <option value="30">Last 30 Days</option>
                            <option value="90">Last 90 Days</option>
                        </select>
                    </div>
                </section>

                {/* Loading */}
                {loading && <div className="loading">Loading jobs...</div>}

                {/* Job Cards */}
                <section className="jobs-grid">
                    {jobs.map((job, idx) => (
                        <article key={job._id || idx} className="job-card">
                            <div className="job-header">
                                <h3 className="job-title">{job.title || 'Untitled'}</h3>
                                <span className="job-source">{job.source || 'Unknown'}</span>
                            </div>
                            <p className="job-company">{job.company || 'Company not specified'}</p>
                            <p className="job-location">📍 {job.location || 'Remote'}</p>
                            {job.experience && <p className="job-experience">💼 {job.experience}</p>}
                            <div className="job-footer">
                                <span className="job-date">{formatDate(job.scraped_at)}</span>
                                {job.url && (
                                    <a href={job.url} target="_blank" rel="noopener noreferrer" className="apply-btn">
                                        Apply →
                                    </a>
                                )}
                            </div>
                        </article>
                    ))}
                </section>

                {/* Empty State */}
                {!loading && jobs.length === 0 && (
                    <div className="empty-state">
                        <p>No jobs found. Try adjusting your filters.</p>
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="pagination">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="page-btn"
                        >
                            ← Prev
                        </button>
                        <span className="page-info">Page {page} of {totalPages}</span>
                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            className="page-btn"
                        >
                            Next →
                        </button>
                    </div>
                )}
            </main>

            <footer className="footer">
                <p>Built with ❤️ using Python Scraper</p>
            </footer>
        </div>
    )
}

export default App
