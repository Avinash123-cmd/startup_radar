export interface TrendSummary {
  category_id: number;
  name: string;
  slug: string;
  description?: string | null;
  star_count: number;
  star_growth_30d: number;
  growth_rate: number;
  news_volume: number;
  momentum_score: number;
  recorded_at: string;
}

export interface QuickInsight {
  leader: string;
  score: number;
  insight: string;
}

export interface CategoryPrediction {
  category: string;
  growth_probability: number;
}

export interface Opportunity {
  id: number;
  title: string;
  description: string;
  niche: string;
  demand_score: number;
  competition_score: number;
  opportunity_score: number;
  potential_ideas?: string | null;
  created_at: string;
  parsed_ideas: string[];
}

export interface Repository {
  id: number;
  name: string;
  full_name: string;
  url: string;
  description?: string | null;
  stars: number;
  forks: number;
  language?: string | null;
  category_id: number;
  created_at: string;
  updated_at: string;
}

export interface RepositoryHistory {
  id: number;
  repository_id: number;
  stars: number;
  forks: number;
  recorded_at: string;
}

export interface PaginatedRepositories {
  items: Repository[];
  total: number;
  page: number;
  pages: number;
}

export interface WeeklyReport {
  id: number;
  title: string;
  slug: string;
  summary?: string | null;
  content: string;
  published_at: string;
  created_at: string;
}

export interface SettingsConfig {
  mock_mode: boolean;
  github_token: string;
  openai_key: string;
  ollama_endpoint: string;
  collectors_limit: number;
}
