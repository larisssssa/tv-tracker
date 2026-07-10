import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { ShowSummary } from "../types";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ShowSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [addedIds, setAddedIds] = useState<Set<number>>(new Set());

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      setResults(await api.searchShows(query));
    } finally {
      setLoading(false);
    }
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
      <form className="search-form" onSubmit={handleSearch}>
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
