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
  const [bulkMarking, setBulkMarking] = useState(false);
  const [expandedSeasons, setExpandedSeasons] = useState<Set<number>>(new Set());

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

        const sortedEpisodes = [...detail.episodes].sort(
          (a, b) => a.season - b.season || a.number - b.number
        );
        const nextUnwatched = sortedEpisodes.find((ep) => !watched.has(ep.id));
        const defaultSeason =
          nextUnwatched?.season ?? sortedEpisodes.at(-1)?.season;
        if (defaultSeason !== undefined) {
          setExpandedSeasons(new Set([defaultSeason]));
        }
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [showId]);

  function toggleSeasonExpanded(seasonNumber: number) {
    setExpandedSeasons((prev) => {
      const next = new Set(prev);
      if (next.has(seasonNumber)) {
        next.delete(seasonNumber);
      } else {
        next.add(seasonNumber);
      }
      return next;
    });
  }

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

  async function markAllWatched(episodes: Episode[]) {
    if (!show) return;
    const unwatched = episodes.filter((ep) => !watchedIds.has(ep.id));
    if (unwatched.length === 0) return;

    setBulkMarking(true);
    try {
      await api.markManyWatched(show.id, unwatched);
      setWatchedIds((prev) => {
        const next = new Set(prev);
        for (const ep of unwatched) next.add(ep.id);
        return next;
      });
    } finally {
      setBulkMarking(false);
    }
  }

  async function unmarkAllWatched(episodes: Episode[]) {
    const watched = episodes.filter((ep) => watchedIds.has(ep.id));
    if (watched.length === 0) return;

    setBulkMarking(true);
    try {
      await api.unmarkManyWatched(watched);
      setWatchedIds((prev) => {
        const next = new Set(prev);
        for (const ep of watched) next.delete(ep.id);
        return next;
      });
    } finally {
      setBulkMarking(false);
    }
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
        <div className="show-header-info">
          <h2 className="show-header-title">{show.name}</h2>
          <p className="show-header-meta">
            {show.premiered?.slice(0, 4) ?? "unknown"} &middot; {show.status}
          </p>
          <div className="actions">
            {!tracked && (
              <button className="btn btn-primary" onClick={handleTrack}>
                Add to My Shows
              </button>
            )}
            <button
              className="btn btn-primary"
              onClick={() => markAllWatched(show.episodes)}
              disabled={bulkMarking}
            >
              Mark all episodes watched
            </button>
            <button
              className="btn btn-ghost"
              onClick={() => unmarkAllWatched(show.episodes)}
              disabled={bulkMarking}
            >
              Undo (unmark all)
            </button>
          </div>
          {/* eslint-disable-next-line react/no-danger */}
          {show.summary && (
            <div
              className="show-summary"
              dangerouslySetInnerHTML={{ __html: show.summary }}
            />
          )}
        </div>
      </div>

      {[...seasons.entries()].map(([seasonNumber, episodes]) => {
        const isExpanded = expandedSeasons.has(seasonNumber);
        const watchedCount = episodes.filter((ep) => watchedIds.has(ep.id)).length;

        return (
          <div key={seasonNumber} className="season">
            <div className="season-header">
              <button
                className="season-toggle"
                onClick={() => toggleSeasonExpanded(seasonNumber)}
                aria-expanded={isExpanded}
              >
                <span
                  className={`season-toggle-arrow${isExpanded ? " expanded" : ""}`}
                  aria-hidden="true"
                >
                  &#9656;
                </span>
                <h3>Season {seasonNumber}</h3>
                <span className="season-progress">
                  {watchedCount} / {episodes.length}
                </span>
              </button>
              <div className="season-actions">
                <button
                  className="btn btn-primary btn-small"
                  onClick={() => markAllWatched(episodes)}
                  disabled={bulkMarking}
                >
                  Mark season watched
                </button>
                <button
                  className="btn btn-ghost btn-small"
                  onClick={() => unmarkAllWatched(episodes)}
                  disabled={bulkMarking}
                >
                  Undo
                </button>
              </div>
            </div>
            {isExpanded && (
              <ul className="episode-list">
                {episodes.map((ep) => (
                  <li key={ep.id} className="episode-list-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={watchedIds.has(ep.id)}
                        onChange={() => toggleWatched(ep)}
                      />
                      E{ep.number} &mdash; {ep.name}
                      <span className="airdate">{ep.airdate}</span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}
