"use client";

import { useEffect, useState, useCallback } from "react";
import StarHistoryChart from "../../component/StarHistoryChart";
import {
  Activity,
  Search,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Star,
  GitFork,
  X,
  Scale,
  Trash2,
  Award,
  Crown,
  TrendingUp,
  CheckCircle
} from "lucide-react";
import type { PaginatedRepositories, Repository, RepositoryHistory, TrendSummary, CompareResponse } from "../../types/api";

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [categories, setCategories] = useState<TrendSummary[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);

  // Search & Filter State
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("");
  const [sortBy, setSortBy] = useState("stars");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Growth History Modal State
  const [activeHistoryRepo, setActiveHistoryRepo] = useState<Repository | null>(null);
  const [repoHistoryData, setRepoHistoryData] = useState<RepositoryHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  // V3 Repository Comparison state
  const [selectedReposToCompare, setSelectedReposToCompare] = useState<Repository[]>([]);
  const [compareResponse, setCompareResponse] = useState<CompareResponse | null>(null);
  const [compareModalOpen, setCompareModalOpen] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);

  // Fetch metadata
  useEffect(() => {
    // Categories
    fetch("http://localhost:8000/trends")
      .then((res) => res.json())
      .then((data: TrendSummary[] | unknown) => setCategories(Array.isArray(data) ? data : []));

    // Languages
    fetch("http://localhost:8000/repositories/languages")
      .then((res) => res.json())
      .then((data: string[] | unknown) => setLanguages(Array.isArray(data) ? data : []));
  }, []);

  // Fetch repos list
  const fetchRepos = useCallback(() => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: "15",
      sort_by: sortBy,
      order: "desc",
    });

    if (search) params.append("search", search);
    if (selectedCategory) params.append("category_id", selectedCategory);
    if (selectedLanguage) params.append("language", selectedLanguage);

    fetch(`http://localhost:8000/repositories?${params.toString()}`)
      .then((res) => res.json())
      .then((data: PaginatedRepositories) => {
        setRepos(data.items || []);
        setTotalPages(data.pages || 1);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Repos Fetch Error:", err);
        setLoading(false);
      });
  }, [page, search, selectedCategory, selectedLanguage, sortBy]);

  useEffect(() => {
    fetchRepos();
  }, [fetchRepos]);

  // Handle opening Growth History Modal
  const openHistoryModal = async (repo: Repository) => {
    setActiveHistoryRepo(repo);
    setHistoryLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/repositories/${repo.id}/history`);
      const data: RepositoryHistory[] | unknown = await res.json();
      setRepoHistoryData(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("History Modal Error:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const closeHistoryModal = () => {
    setActiveHistoryRepo(null);
    setRepoHistoryData([]);
  };

  // ---------------------------------------------------------------------------
  // V3 Comparison Logic
  // ---------------------------------------------------------------------------
  const handleToggleRepoSelect = (repo: Repository) => {
    const idx = selectedReposToCompare.findIndex((r) => r.id === repo.id);
    if (idx !== -1) {
      // Remove
      setSelectedReposToCompare(selectedReposToCompare.filter((r) => r.id !== repo.id));
    } else {
      // Add (Guard limit of 10)
      if (selectedReposToCompare.length >= 10) {
        alert("Maximum 10 repositories may be compared at once.");
        return;
      }
      setSelectedReposToCompare([...selectedReposToCompare, repo]);
    }
  };

  const handleRunComparison = async () => {
    if (selectedReposToCompare.length < 2) {
      alert("Please select at least 2 repositories to compare.");
      return;
    }
    setCompareLoading(true);
    setCompareModalOpen(true);
    setCompareResponse(null);

    const fullNamesParam = selectedReposToCompare.map((r) => r.full_name).join(",");
    try {
      const res = await fetch(`http://localhost:8000/compare?repos=${encodeURIComponent(fullNamesParam)}`);
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || "Comparison query failed");
      }
      const data = await res.json();
      setCompareResponse(data);
    } catch (err: any) {
      console.error("Comparison Query Error:", err);
      alert(`Comparison error: ${err.message}`);
      setCompareModalOpen(false);
    } finally {
      setCompareLoading(false);
    }
  };

  const handleClearCompareBench = () => {
    setSelectedReposToCompare([]);
  };

  // Helper to map category name from ID
  const getCategoryName = (catId: number) => {
    const found = categories.find((c) => c.category_id === catId);
    return found ? found.name : "Unclassified";
  };

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen relative">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50 flex items-center space-x-2">
          <Scale className="h-8 w-8 text-indigo-500" />
          <span>GitHub Repositories</span>
        </h1>
        <p className="text-zinc-400 text-sm mt-2">
          Comprehensive database browser of AI repositories showing stars velocity and historical growth comparison logs.
        </p>
      </div>

      {/* Filter Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-zinc-900/40 p-4 border border-zinc-800 rounded-xl">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-3.5 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Search repositories..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-indigo-500/50"
          />
        </div>

        {/* Category Filter */}
        <select
          value={selectedCategory}
          onChange={(e) => {
            setSelectedCategory(e.target.value);
            setPage(1);
          }}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 px-4 text-sm text-zinc-300 focus:outline-none focus:border-indigo-500/50"
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c.category_id} value={c.category_id}>
              {c.name}
            </option>
          ))}
        </select>

        {/* Language Filter */}
        <select
          value={selectedLanguage}
          onChange={(e) => {
            setSelectedLanguage(e.target.value);
            setPage(1);
          }}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 px-4 text-sm text-zinc-300 focus:outline-none focus:border-indigo-500/50"
        >
          <option value="">All Languages</option>
          {languages.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>

        {/* Sort by */}
        <select
          value={sortBy}
          onChange={(e) => {
            setSortBy(e.target.value);
            setPage(1);
          }}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 px-4 text-sm text-zinc-300 focus:outline-none focus:border-indigo-500/50"
        >
          <option value="stars">Sort by Stars</option>
          <option value="forks">Sort by Forks</option>
          <option value="name">Sort by Name</option>
        </select>
      </div>

      {/* Table view */}
      <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl shadow-xl overflow-hidden mb-24">
        {loading ? (
          <div className="py-20 text-center space-y-4">
            <Activity className="h-8 w-8 text-indigo-500 animate-spin mx-auto" />
            <span className="text-zinc-500 text-sm">Querying database catalog...</span>
          </div>
        ) : repos.length === 0 ? (
          <div className="py-20 text-center text-zinc-500 text-sm">
            No repositories found matching your query criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500 font-bold text-xs uppercase tracking-wider bg-zinc-950/45">
                  <th className="py-4 px-6 w-12 text-center">Compare</th>
                  <th className="py-4 px-6">Repository Name</th>
                  <th className="py-4 px-4">Category</th>
                  <th className="py-4 px-4">Language</th>
                  <th className="py-4 px-4 text-right">Stars</th>
                  <th className="py-4 px-4 text-right">Forks</th>
                  <th className="py-4 px-6 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/80 text-sm">
                {repos.map((repo) => {
                  const isChecked = selectedReposToCompare.some((r) => r.id === repo.id);
                  return (
                    <tr key={repo.id} className="hover:bg-zinc-900/20 transition">
                      {/* Checkbox column */}
                      <td className="py-4 px-6 text-center">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleRepoSelect(repo)}
                          className="h-4 w-4 rounded border-zinc-800 text-indigo-600 focus:ring-indigo-500 bg-zinc-950 cursor-pointer"
                        />
                      </td>

                      {/* Repository and link */}
                      <td className="py-4 px-6 max-w-sm">
                        <div className="font-bold text-zinc-200">{repo.name}</div>
                        <div className="text-zinc-400 text-xs truncate mt-0.5 max-w-[300px]">
                          {repo.description}
                        </div>
                      </td>

                      {/* Category */}
                      <td className="py-4 px-4 text-zinc-300 font-medium">{getCategoryName(repo.category_id)}</td>

                      {/* Language */}
                      <td className="py-4 px-4">
                        <span className="bg-zinc-800 border border-zinc-700/50 px-2 py-0.5 rounded text-xs text-zinc-400">
                          {repo.language || "Other"}
                        </span>
                      </td>

                      {/* Stars */}
                      <td className="py-4 px-4 text-right font-bold text-zinc-200">
                        <div className="flex items-center justify-end space-x-1.5">
                          <span>{repo.stars.toLocaleString()}</span>
                          <Star className="h-3.5 w-3.5 text-zinc-500" />
                        </div>
                      </td>

                      {/* Forks */}
                      <td className="py-4 px-4 text-right font-bold text-zinc-200">
                        <div className="flex items-center justify-end space-x-1.5">
                          <span>{repo.forks.toLocaleString()}</span>
                          <GitFork className="h-3.5 w-3.5 text-zinc-500" />
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="py-4 px-6 text-center">
                        <div className="flex items-center justify-center space-x-3">
                          <button
                            onClick={() => openHistoryModal(repo)}
                            className="px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-indigo-500 text-xs font-semibold text-zinc-300 hover:text-indigo-400 transition cursor-pointer"
                          >
                            Growth History
                          </button>
                          <a
                            href={repo.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-zinc-500 hover:text-zinc-300 transition"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-zinc-800 flex items-center justify-between bg-zinc-950/20">
            <span className="text-xs text-zinc-500 font-semibold">
              Page {page} of {totalPages}
            </span>
            <div className="flex space-x-2">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                className="p-2 rounded-lg border border-zinc-800 disabled:opacity-30 hover:bg-zinc-900 text-zinc-400 transition"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                disabled={page === totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="p-2 rounded-lg border border-zinc-800 disabled:opacity-30 hover:bg-zinc-900 text-zinc-400 transition"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Persistent Bottom Comparison Dock */}
      {selectedReposToCompare.length > 0 && (
        <div className="fixed bottom-0 left-64 right-0 bg-zinc-900 border-t border-indigo-500/20 px-8 py-4 flex items-center justify-between shadow-2xl z-40 backdrop-blur-md bg-zinc-900/90 animate-slide-up">
          <div className="flex items-center space-x-4">
            <div className="bg-indigo-600/20 p-2 rounded-lg text-indigo-400">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-zinc-100">Competitive Comparison Bench</h4>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                {selectedReposToCompare.length} of 10 selected. Review relative developer momentum.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Selected Pills */}
            <div className="hidden lg:flex items-center space-x-2 max-w-[400px] overflow-x-auto">
              {selectedReposToCompare.map((r) => (
                <span key={r.id} className="text-[10px] bg-zinc-950 border border-zinc-800 text-zinc-300 px-2 py-0.5 rounded flex items-center space-x-1 shrink-0">
                  <span className="truncate max-w-[80px]">{r.name}</span>
                  <button onClick={() => handleToggleRepoSelect(r)} className="text-zinc-500 hover:text-rose-400 shrink-0">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>

            <button
              onClick={handleClearCompareBench}
              className="text-xs font-semibold text-zinc-400 hover:text-zinc-200 flex items-center space-x-1 transition cursor-pointer"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear</span>
            </button>

            <button
              onClick={handleRunComparison}
              disabled={selectedReposToCompare.length < 2}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-zinc-50 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer shadow-[0_0_15px_rgba(99,102,241,0.2)]"
            >
              <Award className="h-4 w-4" />
              <span>Compare Momentum</span>
            </button>
          </div>
        </div>
      )}

      {/* Momentum Comparison Modal */}
      {compareModalOpen && (
        <div className="fixed inset-0 bg-zinc-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-zinc-900 border border-zinc-800 w-full max-w-4xl rounded-xl p-6 relative shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
            <button
              onClick={() => setCompareModalOpen(false)}
              className="absolute top-4 right-4 text-zinc-500 hover:text-zinc-300 cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="text-lg font-bold text-zinc-100 flex items-center space-x-2 border-b border-zinc-800 pb-3 mb-4">
              <Scale className="h-5 w-5 text-indigo-400" />
              <span>Competitive Momentum Matrix</span>
            </h3>

            {compareLoading ? (
              <div className="h-60 flex flex-col items-center justify-center space-y-4">
                <Activity className="h-10 w-10 text-indigo-500 animate-spin" />
                <span className="text-zinc-500 text-xs font-semibold">Running comparison formulas...</span>
              </div>
            ) : compareResponse ? (
              <div className="space-y-6 overflow-y-auto flex-1 pr-1">
                {/* Winner Declaration banner */}
                <div className="bg-indigo-950/20 border border-indigo-500/25 p-5 rounded-xl flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="bg-indigo-600/25 p-3 rounded-xl border border-indigo-500/30 text-indigo-400">
                      <Crown className="h-6 w-6 text-indigo-400" />
                    </div>
                    <div>
                      <span className="text-[9px] font-bold uppercase tracking-wider text-indigo-400">Momentum Winner</span>
                      <h4 className="text-base font-extrabold text-zinc-100 mt-0.5">{compareResponse.winner}</h4>
                    </div>
                  </div>
                  <div className="text-right hidden sm:block">
                    <p className="text-[10px] text-zinc-500 font-bold uppercase">Growth Rank Leader</p>
                    <span className="text-emerald-400 text-xs font-extrabold flex items-center space-x-0.5 justify-end">
                      <CheckCircle className="h-4 w-4 shrink-0" />
                      <span>Declared Winner</span>
                    </span>
                  </div>
                </div>

                {/* Compare Grid */}
                <div className="grid grid-cols-1 gap-4">
                  {compareResponse.repositories.map((repo) => {
                    const isWinner = repo.full_name === compareResponse.winner;
                    return (
                      <div
                        key={repo.full_name}
                        className={`p-5 rounded-xl border flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition ${
                          isWinner
                            ? "border-indigo-500/40 bg-indigo-950/10"
                            : "border-zinc-800 bg-zinc-950/30 hover:border-zinc-700"
                        }`}
                      >
                        {/* Name and Rank */}
                        <div className="flex items-center space-x-4">
                          <div className={`p-3 rounded-lg text-sm font-black w-10 h-10 flex items-center justify-center border ${
                            repo.rank === 1
                              ? "bg-amber-600/10 border-amber-500/30 text-amber-400"
                              : "bg-zinc-850 border-zinc-800 text-zinc-400"
                          }`}>
                            #{repo.rank}
                          </div>
                          <div>
                            <div className="font-extrabold text-zinc-200 flex items-center space-x-2">
                              <span>{repo.full_name}</span>
                              {isWinner && (
                                <span className="text-[8px] font-extrabold uppercase bg-emerald-950/40 border border-emerald-500/20 text-emerald-400 px-1.5 py-0.2 rounded">
                                  Winner
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-zinc-400 mt-1 max-w-md line-clamp-1">{repo.description}</p>
                          </div>
                        </div>

                        {/* Comparative stats */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-left shrink-0 w-full md:w-auto">
                          {/* Momentum Score */}
                          <div>
                            <div className="text-[9px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                              <Award className="h-3 w-3 text-indigo-400" />
                              <span>Momentum</span>
                            </div>
                            <div className="text-sm font-extrabold text-indigo-400 mt-0.5">
                              {repo.momentum_score.toFixed(1)}
                            </div>
                          </div>

                          {/* 30d Growth */}
                          <div>
                            <div className="text-[9px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                              <TrendingUp className="h-3 w-3 text-emerald-400" />
                              <span>30d Growth</span>
                            </div>
                            <div className="text-sm font-extrabold text-emerald-400 mt-0.5">
                              +{repo.star_growth_30d.toLocaleString()}
                            </div>
                          </div>

                          {/* Total Stars */}
                          <div>
                            <div className="text-[9px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                              <Star className="h-3 w-3 text-zinc-500" />
                              <span>Stars</span>
                            </div>
                            <div className="text-sm font-bold text-zinc-200 mt-0.5">
                              {repo.stars.toLocaleString()}
                            </div>
                          </div>

                          {/* Language */}
                          <div>
                            <div className="text-[9px] uppercase font-bold text-zinc-500">Language</div>
                            <span className="inline-block mt-0.5 bg-zinc-800 px-2 py-0.5 rounded text-[10px] text-zinc-400">
                              {repo.language || "Other"}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="h-60 flex items-center justify-center text-zinc-500 text-xs">
                No comparison results found.
              </div>
            )}

            <div className="mt-6 pt-4 border-t border-zinc-800 flex justify-end space-x-3 shrink-0">
              <button
                onClick={() => setCompareModalOpen(false)}
                className="px-4 py-2 bg-zinc-850 hover:bg-zinc-800 text-zinc-300 font-semibold rounded-lg text-xs transition cursor-pointer"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Star Growth History Modal overlay */}
      {activeHistoryRepo && (
        <div className="fixed inset-0 bg-zinc-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-zinc-900 border border-zinc-800 w-full max-w-xl rounded-xl p-6 relative shadow-2xl">
            <button
              onClick={closeHistoryModal}
              className="absolute top-4 right-4 text-zinc-500 hover:text-zinc-300 cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="text-lg font-bold text-zinc-100 flex items-center space-x-2">
              <Star className="h-5 w-5 text-indigo-400" />
              <span>{activeHistoryRepo.name} Growth Velocity</span>
            </h3>
            <p className="text-xs text-zinc-400 mt-1 uppercase font-semibold tracking-wider">
              Chronological Star telemetry chart
            </p>

            <div className="mt-8">
              {historyLoading ? (
                <div className="h-40 flex items-center justify-center text-zinc-500 text-xs">
                  Loading star telemetry history...
                </div>
              ) : repoHistoryData.length === 0 ? (
                <div className="h-40 flex items-center justify-center text-zinc-500 text-xs">
                  No historical snapshots available.
                </div>
              ) : (
                <StarHistoryChart data={repoHistoryData} />
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-zinc-800 flex justify-end">
              <button
                onClick={closeHistoryModal}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-semibold rounded-lg text-xs transition cursor-pointer"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
