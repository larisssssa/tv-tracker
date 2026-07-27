import type {
  Episode,
  MyShow,
  ShowDetail,
  ShowSummary,
  User,
  WatchedEpisode,
} from "../types";

const BASE_URL = "http://localhost:8000";

const TOKEN_KEY = "tv_tracker_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }

  const resp = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const data = await resp.json();
      detail = data.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new Error(detail);
  }

  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export const api = {
  async register(email: string, password: string): Promise<User> {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async login(email: string, password: string): Promise<{ access_token: string }> {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    return request("/auth/login", { method: "POST", body });
  },

  async searchShows(query: string): Promise<ShowSummary[]> {
    return request(`/shows/search?q=${encodeURIComponent(query)}`);
  },

  async getShow(showId: number): Promise<ShowDetail> {
    return request(`/shows/${showId}`);
  },

  async myShows(): Promise<MyShow[]> {
    return request("/tracking/shows");
  },

  async trackShow(tvmazeShowId: number): Promise<void> {
    await request("/tracking/shows", {
      method: "POST",
      body: JSON.stringify({ tvmaze_show_id: tvmazeShowId }),
    });
  },

  async untrackShow(tvmazeShowId: number): Promise<void> {
    await request(`/tracking/shows/${tvmazeShowId}`, { method: "DELETE" });
  },

  async watchedEpisodes(): Promise<WatchedEpisode[]> {
    return request("/tracking/episodes/watched");
  },

  async rateEpisode(episodeId: number, rating: number): Promise<WatchedEpisode> {
    return request(`/tracking/episodes/${episodeId}/rating`, {
      method: "PUT",
      body: JSON.stringify({ rating }),
    });
  },

  async rateShow(tvmazeShowId: number, rating: number): Promise<void> {
    await request(`/tracking/shows/${tvmazeShowId}/rating`, {
      method: "PUT",
      body: JSON.stringify({ rating }),
    });
  },

  async markWatched(tvmazeShowId: number, episode: Episode): Promise<void> {
    await request("/tracking/episodes", {
      method: "POST",
      body: JSON.stringify({
        tvmaze_show_id: tvmazeShowId,
        tvmaze_episode_id: episode.id,
      }),
    });
  },

  async unmarkWatched(episodeId: number): Promise<void> {
    await request(`/tracking/episodes/${episodeId}`, { method: "DELETE" });
  },

  async markManyWatched(tvmazeShowId: number, episodes: Episode[]): Promise<void> {
    if (episodes.length === 0) return;
    await request("/tracking/episodes/bulk", {
      method: "POST",
      body: JSON.stringify({
        tvmaze_show_id: tvmazeShowId,
        tvmaze_episode_ids: episodes.map((ep) => ep.id),
      }),
    });
  },

  async unmarkManyWatched(episodes: Episode[]): Promise<void> {
    if (episodes.length === 0) return;
    await request("/tracking/episodes/bulk-unmark", {
      method: "POST",
      body: JSON.stringify({
        tvmaze_episode_ids: episodes.map((ep) => ep.id),
      }),
    });
  },
};
