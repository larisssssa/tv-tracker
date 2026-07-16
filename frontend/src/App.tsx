import { Navigate, Route, Routes, Link, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AuthPage } from "./pages/AuthPage";
import { SearchPage } from "./pages/SearchPage";
import { MyShowsPage } from "./pages/MyShowsPage";
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

  if (!isAuthenticated) return null;

  return (
    <nav className="navbar">
      <Link to="/up-next" className="wordmark">
        <span className="wordmark-icon" aria-hidden="true" />
        TV Tracker
      </Link>
      <Link to="/up-next">Up Next</Link>
      <Link to="/my-shows">My Shows</Link>
      <Link to="/search">Search</Link>
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
