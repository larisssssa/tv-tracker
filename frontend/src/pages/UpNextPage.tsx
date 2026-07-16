import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Episode, MyShow } from "../types";

interface UpNextItem {
  show: MyShow;
  episode: Episode;
  aired: boolean;
}

function airstampMillis(episode: Episode): number {
  return episode.airstamp ? new Date(episode.airstamp).getTime() : Number.POSITIVE_INFINITY;
}

function toUpNextItem(show: MyShow): UpNextItem | null {
  if (show.next_episode) {
    return { show, episode: show.next_episode, aired: true };
  }
  if (show.next_unaired_episode) {
    return { show, episode: show.next_unaired_episode, aired: false };
  }
  return null;
}

export function UpNextPage() {
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

  async function handleMarkWatched(item: UpNextItem) {
    if (!item.aired) return;
    await api.markWatched(item.show.tvmaze_show_id, item.episode);
    await refresh();
  }

  if (loading) return <p>Loading...</p>;

  const upNext = shows
    .map(toUpNextItem)
    .filter((item): item is UpNextItem => item !== null)
    .sort((a, b) => airstampMillis(a.episode) - airstampMillis(b.episode));

  if (shows.length === 0) {
    return (
      <div className="empty-state">
        <p>You aren't tracking any shows yet.</p>
        <Link to="/search" className="btn btn-primary">
          Search for a show to add
        </Link>
      </div>
    );
  }

  if (upNext.length === 0) {
    return (
      <div className="up-next-page">
        <div className="page-header">
          <h2 className="page-title">Up Next</h2>
          <p className="page-subtitle">What to watch next, across every show you track.</p>
        </div>
        <div className="empty-state">
          <p>You're all caught up on every tracked show!</p>
          <Link to="/my-shows">View My Shows</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="up-next-page">
      <div className="page-header">
        <h2 className="page-title">Up Next</h2>
        <p className="page-subtitle">What to watch next, across every show you track.</p>
      </div>
      <ul className="show-list">
        {upNext.map((item) => (
          <li key={item.show.tvmaze_show_id} className="show-list-item">
            {item.show.image && <img src={item.show.image} alt={item.show.name} />}
            <div className="show-info">
              <div className="show-title-row">
                <Link
                  className="show-name"
                  to={`/shows/${item.show.tvmaze_show_id}`}
                >
                  {item.show.name}
                </Link>
                {item.show.status && (
                  <span
                    className={`status-badge status-${item.show.status.toLowerCase()}`}
                  >
                    {item.show.status}
                  </span>
                )}
                {!item.aired && (
                  <span className="status-badge status-upcoming">Upcoming</span>
                )}
              </div>
              <p className={item.aired ? "show-next-up" : "show-upcoming"}>
                S{item.episode.season}E{item.episode.number} &mdash;{" "}
                {item.episode.name}
              </p>
              {item.episode.airdate && (
                <p className="show-upcoming">
                  {item.aired ? "Aired" : "Airs"} {item.episode.airdate}
                </p>
              )}
            </div>
            <div className="actions">
              {item.aired ? (
                <button
                  className="btn btn-primary btn-small"
                  onClick={() => handleMarkWatched(item)}
                >
                  Mark watched
                </button>
              ) : (
                <span className="upcoming-note">Not aired yet</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
