import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Episode, ShowDetail } from "../types";

export function ShowDetailPage() {
  const { showId } = useParams<{ showId: string }>();
  const [show, setShow] = useState<ShowDetail | null>(null);
  const [watchedIds, setWatchedIds] = useState<Set<number>>(new Set());
  const [tracked, setTracked] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!showId) return;
    const id = Number(showId);

    async function load() {
      setLoading(true);
      try {
        const [detail, watched, myShows] = await Promise.all([
          api.getShow(id),
          api.watchedEpisodeIds(),
          api.myShows(),
        ]);
        setShow(detail);
        setWatchedIds(watched);
        setTracked(myShows.some((s) => s.tvmaze_show_id === id));
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [showId]);

  async function toggleWatched(episode: Episode) {
    if (!show) return;
    if (watchedIds.has(episode.id)) {
      await api.unmarkWatched(episode.id);
      setWatchedIds((prev) => {
        const next = new Set(prev);
        next.delete(episode.id);
        return next;
      });
    } else {
      await api.markWatched(show.id, episode);
      setWatchedIds((prev) => new Set(prev).add(episode.id));
    }
  }

  async function handleTrack() {
    if (!show) return;
    await api.trackShow(show.id);
    setTracked(true);
  }

  if (loading) return <p>Loading...</p>;
  if (!show) return <p>Show not found.</p>;

  const seasons = new Map<number, Episode[]>();
  for (const ep of show.episodes) {
    if (!seasons.has(ep.season)) seasons.set(ep.season, []);
    seasons.get(ep.season)!.push(ep);
  }

  return (
    <div className="show-detail-page">
      <div className="show-header">
        {show.image && <img src={show.image} alt={show.name} />}
        <div>
          <h2>{show.name}</h2>
          <p>{show.premiered?.slice(0, 4) ?? "unknown"} - {show.status}</p>
          {!tracked && <button onClick={handleTrack}>Add to My Shows</button>}
          {/* eslint-disable-next-line react/no-danger */}
          {show.summary && (
            <div dangerouslySetInnerHTML={{ __html: show.summary }} />
          )}
        </div>
      </div>

      {[...seasons.entries()].map(([seasonNumber, episodes]) => (
        <div key={seasonNumber} className="season">
          <h3>Season {seasonNumber}</h3>
          <ul className="episode-list">
            {episodes.map((ep) => (
              <li key={ep.id} className="episode-list-item">
                <label>
                  <input
                    type="checkbox"
                    checked={watchedIds.has(ep.id)}
                    onChange={() => toggleWatched(ep)}
                  />
                  E{ep.number} &mdash; {ep.name}{" "}
                  <span className="airdate">{ep.airdate}</span>
                </label>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
