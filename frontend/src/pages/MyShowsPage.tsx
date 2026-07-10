import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { MyShow } from "../types";

export function MyShowsPage() {
  const [shows, setShows] = useState<MyShow[]>([]);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      setShows(await api.myShows());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleMarkWatched(show: MyShow) {
    if (!show.next_episode) return;
    await api.markWatched(show.tvmaze_show_id, show.next_episode);
    await refresh();
  }

  async function handleRemove(showId: number) {
    await api.untrackShow(showId);
    await refresh();
  }

  if (loading) return <p>Loading...</p>;

  if (shows.length === 0) {
    return (
      <div className="empty-state">
        <p>You aren't tracking any shows yet.</p>
        <Link to="/search">Search for a show to add</Link>
      </div>
    );
  }

  return (
    <div className="my-shows-page">
      <div className="page-header">
        <h2 className="page-title">My Shows</h2>
        <p className="page-subtitle">Track what you've watched and what's next.</p>
      </div>
      <ul className="show-list">
        {shows.map((show) => (
          <li key={show.tvmaze_show_id} className="show-list-item">
            {show.image && <img src={show.image} alt={show.name} />}
            <div className="show-info">
              <Link className="show-name" to={`/shows/${show.tvmaze_show_id}`}>
                {show.name}
              </Link>
              <p className="show-progress">
                {show.watched_count} / {show.total_aired_count} watched
              </p>
              {show.next_episode ? (
                <p className="show-next-up">
                  Next up: S{show.next_episode.season}E{show.next_episode.number}{" "}
                  &mdash; {show.next_episode.name}
                </p>
              ) : (
                <p className="show-next-up">All caught up!</p>
              )}
            </div>
            <div className="actions">
              {show.next_episode && (
                <button
                  className="btn btn-primary btn-small"
                  onClick={() => handleMarkWatched(show)}
                >
                  Mark next episode watched
                </button>
              )}
              <button
                className="btn btn-ghost btn-small"
                onClick={() => handleRemove(show.tvmaze_show_id)}
              >
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
