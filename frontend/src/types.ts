export interface ShowSummary {
  id: number;
  name: string;
  premiered: string | null;
  status: string | null;
  image: string | null;
  summary: string | null;
}

export interface Episode {
  id: number;
  season: number;
  number: number;
  name: string;
  airdate: string | null;
  airstamp: string | null;
  image: string | null;
}

export interface ShowDetail extends ShowSummary {
  episodes: Episode[];
}

export interface MyShow {
  tvmaze_show_id: number;
  name: string;
  image: string | null;
  status: string | null;
  next_episode: Episode | null;
  next_unaired_episode: Episode | null;
  watched_count: number;
  total_aired_count: number;
  rating: number | null;
  added_at: string;
}

export interface WatchedEpisode {
  tvmaze_episode_id: number;
  watched_at: string;
  rating: number | null;
}

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface UserStats {
  shows_tracked: number;
  episodes_watched: number;
  member_since: string;
}

export interface ShowList {
  id: number;
  name: string;
  created_at: string;
  is_public: boolean;
}

export interface ListedShow {
  tvmaze_show_id: number;
  name: string;
  image: string | null;
  status: string | null;
  added_at: string;
}

export interface ShowListDetail extends ShowList {
  shows: ListedShow[];
}
