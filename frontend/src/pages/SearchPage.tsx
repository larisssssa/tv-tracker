import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { ShowSummary } from "../types";

const DEBOUNCE_MS = 300;

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ShowSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [addedIds, setAddedIds] = useState<Set<number>>(new Set());
  const latestRequestId = useRef(0);

  async function runSearch(searchQuery: string) {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setResults([]);
      setLoading(false);
      return;
    }

    const requestId = ++latestRequestId.current;
    setLoading(true);
    try {
      const shows = await api.searchShows(trimmed);
      // Ignore stale responses: a faster later request may have already resolved.
      if (requestId !== latestRequestId.current) return;
      setResults(shows);
    } finally {
      if (requestId === latestRequestId.current) setLoading(false);
    }
  }

  useEffect(() => {
    const timeout = setTimeout(() => runSearch(query), DEBOUNCE_MS);
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    runSearch(query);
  }

  async function handleAdd(showId: number) {
    await api.trackShow(showId);
    setAddedIds((prev) => new Set(prev).add(showId));
  }

  return (
    <div className="search-page">
      <div className="page-header">
        <h2 className="page-title">Search Shows</h2>
        <p className="page-subtitle">Find a show and add it to your list.</p>
      </div>
      <form className="search-form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="text"
          placeholder="Search for a show..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      <ul className="show-list">
        {results.map((show) => (
          <li key={show.id} className="show-list-item">
            {show.image && <img src={show.image} alt={show.name} />}
            <div className="show-info">
              <Link className="show-name" to={`/shows/${show.id}`}>
                {show.name}
              </Link>
              <p className="show-meta">
                {show.premiered?.slice(0, 4) ?? "unknown"} &middot; {show.status}
              </p>
            </div>
            <div className="actions">
              <button
                className="btn btn-primary btn-small"
                onClick={() => handleAdd(show.id)}
                disabled={addedIds.has(show.id)}
              >
                {addedIds.has(show.id) ? "Added" : "Add to My Shows"}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
