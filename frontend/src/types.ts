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
  next_episode: Episode | null;
  watched_count: number;
  total_aired_count: number;
}

export interface User {
  id: number;
  email: string;
}
