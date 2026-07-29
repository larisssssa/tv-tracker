import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { AddToListPicker } from "../components/AddToListPicker";
import { StarRating } from "../components/StarRating";
import type { Episode, ShowDetail, WatchedEpisode } from "../types";

export function ShowDetailPage() {
  const { showId } = useParams<{ showId: string }>();
  const [show, setShow] = useState<ShowDetail | null>(null);
  const [watchedMap, setWatchedMap] = useState<Map<number, WatchedEpisode>>(new Map());
  const [tracked, setTracked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [bulkMarking, setBulkMarking] = useState(false);
  const [expandedSeasons, setExpandedSeasons] = useState<Set<number>>(new Set());
  const [showPicker, setShowPicker] = useState(false);

  useEffect(() => {
    if (!showId) return;
    const id = Number(showId);

    async function load() {
      setLoading(true);
      try {
        const [detail, watchedEpisodes, myShows] = await Promise.all([
          api.getShow(id),
          api.watchedEpisodes(),
          api.myShows(),
        ]);
        setShow(detail);
        setWatchedMap(new Map(watchedEpisodes.map((w) => [w.tvmaze_episode_id, w])));
        setTracked(myShows.some((s) => s.tvmaze_show_id === id));

        const sortedEpisodes = [...detail.episodes].sort(
          (a, b) => a.season - b.season || a.number - b.number
        );
        const watchedIds = new Set(watchedEpisodes.map((w) => w.tvmaze_episode_id));
        const nextUnwatched = sortedEpisodes.find((ep) => !watchedIds.has(ep.id));
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
    if (watchedMap.has(episode.id)) {
      await api.unmarkWatched(episode.id);
      setWatchedMap((prev) => {
        const next = new Map(prev);
        next.delete(episode.id);
        return next;
      });
    } else {
      await api.markWatched(show.id, episode);
      setWatchedMap((prev) => {
        const next = new Map(prev);
        next.set(episode.id, {
          tvmaze_episode_id: episode.id,
          watched_at: new Date().toISOString(),
          rating: null,
        });
        return next;
      });
    }
  }

  async function rateEpisode(episode: Episode, rating: number) {
    const updated = await api.rateEpisode(episode.id, rating);
    setWatchedMap((prev) => new Map(prev).set(episode.id, updated));
  }

  async function handleTrack() {
    if (!show) return;
    await api.trackShow(show.id);
    setTracked(true);
  }

  async function markAllWatched(episodes: Episode[]) {
    if (!show) return;
    const unwatched = episodes.filter((ep) => !watchedMap.has(ep.id));
    if (unwatched.length === 0) return;

    setBulkMarking(true);
    try {
      await api.markManyWatched(show.id, unwatched);
      setWatchedMap((prev) => {
        const next = new Map(prev);
        for (const ep of unwatched) {
          next.set(ep.id, {
            tvmaze_episode_id: ep.id,
            watched_at: new Date().toISOString(),
            rating: null,
          });
        }
        return next;
      });
    } finally {
      setBulkMarking(false);
    }
  }

  async function unmarkAllWatched(episodes: Episode[]) {
    const alreadyWatched = episodes.filter((ep) => watchedMap.has(ep.id));
    if (alreadyWatched.length === 0) return;

    setBulkMarking(true);
    try {
      await api.unmarkManyWatched(alreadyWatched);
      setWatchedMap((prev) => {
        const next = new Map(prev);
        for (const ep of alreadyWatched) next.delete(ep.id);
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
            <button className="btn btn-ghost" onClick={() => setShowPicker(true)}>
              Add to list
            </button>
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
        const watchedCount = episodes.filter((ep) => watchedMap.has(ep.id)).length;

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
                {episodes.map((ep) => {
                  const watchedEpisode = watchedMap.get(ep.id);
                  return (
                    <li key={ep.id} className="episode-list-item">
                      <label>
                        <input
                          type="checkbox"
                          checked={watchedEpisode !== undefined}
                          onChange={() => toggleWatched(ep)}
                        />
                        E{ep.number} &mdash; {ep.name}
                        <span className="airdate">{ep.airdate}</span>
                      </label>
                      {watchedEpisode && (
                        <StarRating
                          value={watchedEpisode.rating}
                          onRate={(rating) => rateEpisode(ep, rating)}
                          size="small"
                        />
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        );
      })}

      {showPicker && (
        <AddToListPicker tvmazeShowId={show.id} onClose={() => setShowPicker(false)} />
      )}
    </div>
  );
}
