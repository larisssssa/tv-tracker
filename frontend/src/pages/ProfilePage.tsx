import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { ShowCard } from "../components/ShowCard";
import type { MyShow, ShowListDetail, User, UserStats } from "../types";

const RECENT_COUNT = 5;

export function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [myShows, setMyShows] = useState<MyShow[]>([]);
  const [lists, setLists] = useState<ShowListDetail[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [me, myStats, shows, myLists] = await Promise.all([
          api.me(),
          api.myStats(),
          api.myShows(),
          api.listLists(),
        ]);
        setUser(me);
        setStats(myStats);
        setMyShows(shows);
        const details = await Promise.all(myLists.map((l) => api.getList(l.id)));
        setLists(details);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <p>Loading...</p>;
  if (!user || !stats) return <p>Could not load profile.</p>;

  const memberSince = new Date(stats.member_since).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const recentShows = [...myShows]
    .sort((a, b) => new Date(b.added_at).getTime() - new Date(a.added_at).getTime())
    .slice(0, RECENT_COUNT);

  return (
    <div className="profile-page">
      <div className="page-header">
        <h2 className="page-title">Profile</h2>
        <p className="page-subtitle">{user.email}</p>
      </div>

      <p className="profile-member-since">Member since {memberSince}</p>

      <div className="stat-card-row">
        <div className="stat-card card">
          <p className="stat-card-value">{stats.shows_tracked}</p>
          <p className="stat-card-label">Shows tracked</p>
        </div>
        <div className="stat-card card">
          <p className="stat-card-value">{stats.episodes_watched}</p>
          <p className="stat-card-label">Episodes watched</p>
        </div>
      </div>

      <div className="profile-lists">
        <h3 className="profile-lists-title">My Shows</h3>
        {recentShows.length === 0 ? (
          <div className="empty-state">
            <p>You aren't tracking any shows yet.</p>
            <Link to="/search" className="btn btn-primary">
              Search for a show to add
            </Link>
          </div>
        ) : (
          <>
            <div className="show-card-row">
              {recentShows.map((show) => (
                <ShowCard
                  key={show.tvmaze_show_id}
                  tvmazeShowId={show.tvmaze_show_id}
                  name={show.name}
                  image={show.image}
                  rating={show.rating}
                />
              ))}
            </div>
            <div className="profile-section-footer">
              <Link to="/my-shows" className="link-button">
                View all my shows &rarr;
              </Link>
            </div>
          </>
        )}
      </div>

      <div className="profile-lists">
        <h3 className="profile-lists-title">Your Lists</h3>
        {lists.length === 0 ? (
          <div className="empty-state">
            <p>You haven't created any lists yet.</p>
            <Link to="/lists" className="btn btn-primary">
              Create a list
            </Link>
          </div>
        ) : (
          lists.map((list) => {
            const recentListShows = [...list.shows]
              .sort(
                (a, b) => new Date(b.added_at).getTime() - new Date(a.added_at).getTime()
              )
              .slice(0, RECENT_COUNT);

            return (
              <div key={list.id} className="profile-list-section">
                <div className="profile-list-header">
                  <span className="show-name">{list.name}</span>
                  <span className="profile-list-count">
                    {list.shows.length} show{list.shows.length === 1 ? "" : "s"}
                  </span>
                </div>
                {recentListShows.length === 0 ? (
                  <p className="profile-list-empty">No shows in this list yet.</p>
                ) : (
                  <div className="show-card-row">
                    {recentListShows.map((show) => (
                      <ShowCard
                        key={show.tvmaze_show_id}
                        tvmazeShowId={show.tvmaze_show_id}
                        name={show.name}
                        image={show.image}
                        rating={null}
                      />
                    ))}
                  </div>
                )}
                <div className="profile-section-footer">
                  <Link to="/lists" className="link-button">
                    View list &rarr;
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
