import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { User, UserStats } from "../types";

export function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [me, myStats] = await Promise.all([api.me(), api.myStats()]);
        setUser(me);
        setStats(myStats);
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
    </div>
  );
}
