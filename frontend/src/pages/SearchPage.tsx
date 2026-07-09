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
      <h2>Search Shows</h2>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search for a show..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      <ul className="show-list">
        {results.map((show) => (
          <li key={show.id} className="show-list-item">
            {show.image && <img src={show.image} alt={show.name} />}
            <div>
              <Link to={`/shows/${show.id}`}>{show.name}</Link>
              <p>{show.premiered?.slice(0, 4) ?? "unknown"} - {show.status}</p>
            </div>
            <button
              onClick={() => handleAdd(show.id)}
              disabled={addedIds.has(show.id)}
            >
              {addedIds.has(show.id) ? "Added" : "Add to My Shows"}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
