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
  context_snapshot?: string | null;
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

export interface WatchlistCategory {
  id: number;
  watchlist_id: number;
  category_id: number;
  category?: {
    id: number;
    name: string;
    slug: string;
  };
}

export interface WatchlistRepository {
  id: number;
  watchlist_id: number;
  repository_id: number;
  repository?: {
    id: number;
    name: string;
    full_name: string;
  };
}

export interface Watchlist {
  id: number;
  name: string;
  description?: string | null;
  is_active: number;
  created_at: string;
  category_items: WatchlistCategory[];
  repository_items: WatchlistRepository[];
}

export interface Alert {
  id: number;
  watchlist_id: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  alert_type: string;
  category_id?: number | null;
  repository_id?: number | null;
  title: string;
  message: string;
  previous_value?: number | null;
  current_value?: number | null;
  change_percent?: number | null;
  is_read: number;
  created_at: string;
  category_slug?: string | null;
  repository_name?: string | null;
}

export interface FactorScores {
  founder_difficulty: number;
  revenue_potential: number;
  market_timing: number;
  competition_density: number;
  growth_velocity: number;
  vc_attractiveness: number;
}

export interface OpportunityV2 {
  category: string;
  category_slug: string;
  category_id: number;
  success_probability: number;
  demand_score: number;
  competition_score: number;
  opportunity_score_v1: number;
  factors: FactorScores;
  reasoning: string;
  strongest_signals: string[];
  risk_factors: string[];
}

export interface StartupBriefV2 {
  startup_name: string;
  category: string;
  category_slug: string;
  category_id: number;
  problem_statement: string;
  target_customer: string;
  mvp_features: string[];
  pricing_model: string;
  revenue_potential: string;
  competitive_advantage: string;
  go_to_market: string;
  build_difficulty: string;
  estimated_time_to_mvp: string;
  success_probability: number;
  factors?: FactorScores;
  why?: string;
  strongest_signals?: string[];
  risk_factors?: string[];
}

export interface PredictionDetail {
  category: string;
  category_slug: string;
  category_id: number;
  growth_probability: number;
  confidence: number;
  slope: number;
  horizon_days: number;
}

export interface AlertSummaryOut {
  total: number;
  unread: number;
  severity_breakdown: Record<string, number>;
  recent_alerts: Alert[];
}

export interface FounderRecommendation {
  category: string;
  category_slug: string;
  rec_type: "conviction" | "entry" | "venture" | "timing";
  text: string;
  metric: string;
}

export interface AISummaryResult {
  executive_summary: string;
  market_risk_summary: string;
  model_used: string;
  fallback_mode: boolean;
}

export interface ExecutiveDashboardResponse {
  generated_at: string;
  top_opportunities: OpportunityV2[];
  top_startup_ideas: StartupBriefV2[];
  fastest_growing_categories: TrendSummary[];
  highest_confidence_predictions: PredictionDetail[];
  watchlist_alerts_summary: AlertSummaryOut;
  founder_recommendations: FounderRecommendation[];
  ai_summary: AISummaryResult;
}

export interface CompareResponse {
  winner: string;
  total_compared: number;
  repositories: ComparedRepository[];
}

export interface ComparedRepository {
  rank: number;
  full_name: string;
  name: string;
  url: string;
  description?: string | null;
  language?: string | null;
  category: string;
  stars: number;
  forks: number;
  star_growth_30d: number;
  momentum_score: number;
  snapshot_history: { stars: number; recorded_at: string }[];
}

export interface AnalysisResponse {
  category: string;
  momentum_score: number;
  growth_rate: number;
  star_growth_30d: number;
  top_repositories: {
    name: string;
    full_name: string;
    url: string;
    description?: string;
    stars: number;
    forks: number;
    language?: string;
  }[];
  top_signals: string[];
  analysis: string;
  risks: string[];
  opportunities: string[];
  confidence: number;
}


