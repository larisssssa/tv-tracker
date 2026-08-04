import { useEffect, useState } from "react";
import { Navigate, Route, Routes, Link, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { api } from "./api/client";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AuthPage } from "./pages/AuthPage";
import { SearchPage } from "./pages/SearchPage";
import { MyShowsPage } from "./pages/MyShowsPage";
import { ListsPage } from "./pages/ListsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ShowDetailPage } from "./pages/ShowDetailPage";
import { UpNextPage } from "./pages/UpNextPage";
import "./App.css";

function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function NavBar() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) return;

    let cancelled = false;
    async function refresh() {
      try {
        const notifications = await api.listNotifications();
        if (!cancelled) setUnreadCount(notifications.length);
      } catch {
        // navbar badge is best-effort; a failed fetch just leaves the count as-is
      }
    }
    refresh();
    const interval = setInterval(refresh, 60_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;

  return (
    <nav className="navbar">
      <Link to="/up-next" className="wordmark">
        <span className="wordmark-icon" aria-hidden="true" />
        TV Tracker
      </Link>
      <Link to="/up-next">
        Up Next
        {unreadCount > 0 && <span className="nav-badge">{unreadCount}</span>}
      </Link>
      <Link to="/my-shows">My Shows</Link>
      <Link to="/lists">Lists</Link>
      <Link to="/search">Search</Link>
      <Link to="/profile">Profile</Link>
      <button
        className="navbar-link"
        onClick={() => {
          logout();
          navigate("/login");
        }}
      >
        Log out
      </button>
    </nav>
  );
}

function AppRoutes() {
  return (
    <>
      <NavBar />
      <main className="content">
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route
            path="/up-next"
            element={
              <RequireAuth>
                <UpNextPage />
              </RequireAuth>
            }
          />
          <Route
            path="/my-shows"
            element={
              <RequireAuth>
                <MyShowsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/lists"
            element={
              <RequireAuth>
                <ListsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/search"
            element={
              <RequireAuth>
                <SearchPage />
              </RequireAuth>
            }
          />
          <Route
            path="/shows/:showId"
            element={
              <RequireAuth>
                <ShowDetailPage />
              </RequireAuth>
            }
          />
          <Route
            path="/profile"
            element={
              <RequireAuth>
                <ProfilePage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/up-next" replace />} />
        </Routes>
      </main>
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
