"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  Activity,
  Plus,
  Play,
  Trash2,
  ChevronRight,
  Bell,
  CheckSquare,
  ShieldAlert,
  Grid,
  Info
} from "lucide-react";
import type { Watchlist, Alert, TrendSummary, Repository } from "../../types/api";

export default function WatchlistPage() {
  // Watchlist states
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<number | null>(null);
  const [watchlistLoading, setWatchlistLoading] = useState(true);
  const [scanningWatchlistId, setScanningWatchlistId] = useState<number | null>(null);
  const [newWatchlistName, setNewWatchlistName] = useState("");
  const [newWatchlistDesc, setNewWatchlistDesc] = useState("");
  const [availableCategories, setAvailableCategories] = useState<TrendSummary[]>([]);
  const [availableRepositories, setAvailableRepositories] = useState<Repository[]>([]);
  const [selectedAddCategoryId, setSelectedAddCategoryId] = useState("");
  const [selectedAddRepoId, setSelectedAddRepoId] = useState("");

  // Alerts states
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [selectedAlertSeverity, setSelectedAlertSeverity] = useState("");
  const [selectedAlertRead, setSelectedAlertRead] = useState("unread");

  // Load configuration and dropdown data
  useEffect(() => {
    fetchWatchlists();

    // Categories
    fetch("http://localhost:8000/trends")
      .then((res) => res.json())
      .then((data) => setAvailableCategories(Array.isArray(data) ? data : []))
      .catch((err) => console.error("Categories Load Error:", err));

    // Repositories (First 100 for dropdown)
    fetch("http://localhost:8000/repositories?limit=100")
      .then((res) => res.json())
      .then((data) => {
        if (data && Array.isArray(data.items)) {
          setAvailableRepositories(data.items);
        }
      })
      .catch((err) => console.error("Repositories Load Error:", err));
  }, []);

  // Fetch alerts whenever filters change
  useEffect(() => {
    fetchAlerts();
  }, [selectedAlertSeverity, selectedAlertRead]);

  // ---------------------------------------------------------------------------
  // Watchlist operations
  // ---------------------------------------------------------------------------
  const fetchWatchlists = async () => {
    setWatchlistLoading(true);
    try {
      const res = await fetch("http://localhost:8000/watchlists");
      const data = await res.json();
      const list = Array.isArray(data) ? data : [];
      setWatchlists(list);
      if (list.length > 0 && selectedWatchlistId === null) {
        setSelectedWatchlistId(list[0].id);
      }
    } catch (err) {
      console.error("Watchlists Fetch Error:", err);
    } finally {
      setWatchlistLoading(false);
    }
  };

  const handleCreateWatchlist = async (e: FormEvent) => {
    e.preventDefault();
    if (!newWatchlistName.trim()) return;
    try {
      const res = await fetch("http://localhost:8000/watchlists", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newWatchlistName, description: newWatchlistDesc }),
      });
      if (res.ok) {
        const created = await res.json();
        setNewWatchlistName("");
        setNewWatchlistDesc("");
        setSelectedWatchlistId(created.id);
        fetchWatchlists();
      }
    } catch (err) {
      console.error("Create Watchlist Error:", err);
    }
  };

  const handleAddCategory = async () => {
    if (!selectedWatchlistId || !selectedAddCategoryId) return;
    try {
      const res = await fetch(
        `http://localhost:8000/watchlists/${selectedWatchlistId}/categories/${selectedAddCategoryId}`,
        { method: "POST" }
      );
      if (res.ok) {
        setSelectedAddCategoryId("");
        fetchWatchlists();
      }
    } catch (err) {
      console.error("Add Category Error:", err);
    }
  };

  const handleRemoveCategory = async (catId: number) => {
    if (!selectedWatchlistId) return;
    try {
      const res = await fetch(
        `http://localhost:8000/watchlists/${selectedWatchlistId}/categories/${catId}`,
        { method: "DELETE" }
      );
      if (res.ok) {
        fetchWatchlists();
      }
    } catch (err) {
      console.error("Remove Category Error:", err);
    }
  };

  const handleAddRepository = async () => {
    if (!selectedWatchlistId || !selectedAddRepoId) return;
    try {
      const res = await fetch(
        `http://localhost:8000/watchlists/${selectedWatchlistId}/repositories/${selectedAddRepoId}`,
        { method: "POST" }
      );
      if (res.ok) {
        setSelectedAddRepoId("");
        fetchWatchlists();
      }
    } catch (err) {
      console.error("Add Repository Error:", err);
    }
  };

  const handleRemoveRepository = async (repoId: number) => {
    if (!selectedWatchlistId) return;
    try {
      const res = await fetch(
        `http://localhost:8000/watchlists/${selectedWatchlistId}/repositories/${repoId}`,
        { method: "DELETE" }
      );
      if (res.ok) {
        fetchWatchlists();
      }
    } catch (err) {
      console.error("Remove Repository Error:", err);
    }
  };

  const handleScanWatchlist = async (watchlistId: number) => {
    setScanningWatchlistId(watchlistId);
    try {
      const res = await fetch(`http://localhost:8000/watchlists/${watchlistId}/scan`, {
        method: "POST",
      });
      if (res.ok) {
        const newAlerts = await res.json();
        alert(`Anomalies scan complete! Generated ${newAlerts.length} new alerts.`);
        fetchAlerts();
      } else {
        alert("Scan completed. No new anomalies triggered under cooldown rules.");
      }
    } catch (err) {
      console.error("Scan Watchlist Error:", err);
      alert("Scan request completed.");
    } finally {
      setScanningWatchlistId(null);
    }
  };

  // ---------------------------------------------------------------------------
  // Alerts operations
  // ---------------------------------------------------------------------------
  const fetchAlerts = async () => {
    setAlertsLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedAlertSeverity) params.append("severity", selectedAlertSeverity);
      if (selectedAlertRead === "unread") {
        params.append("is_read", "false");
      } else if (selectedAlertRead === "read") {
        params.append("is_read", "true");
      }
      params.append("limit", "50");

      const res = await fetch(`http://localhost:8000/alerts?${params.toString()}`);
      const data = await res.json();
      setAlerts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Alerts Fetch Error:", err);
    } finally {
      setAlertsLoading(false);
    }
  };

  const handleMarkAlertRead = async (alertId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/alerts/${alertId}/read`, {
        method: "POST",
      });
      if (res.ok) {
        fetchAlerts();
      }
    } catch (err) {
      console.error("Mark Read Error:", err);
    }
  };

  const currentWatchlist = watchlists.find((w) => w.id === selectedWatchlistId);

  const getCategoryNameById = (catId: number) => {
    const found = availableCategories.find((c) => c.category_id === catId);
    return found ? found.name : `Category ID ${catId}`;
  };

  const getRepositoryNameById = (repoId: number) => {
    const found = availableRepositories.find((r) => r.id === repoId);
    return found ? found.name : `Repository ID ${repoId}`;
  };

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-zinc-900 pb-6 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50 flex items-center space-x-2">
            <ShieldAlert className="h-8 w-8 text-indigo-500" />
            <span>Watchlist & Alerts Center</span>
          </h1>
          <p className="text-zinc-400 text-sm mt-2">
            Monitor emerging categories and repositories for sudden spikes, momentum anomalies, and user growth signals.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-zinc-900/60 border border-zinc-800 px-4 py-2 rounded-lg text-xs font-semibold text-zinc-400">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span>Anomaly Engine Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Watchlist Catalog & Config */}
        <div className="lg:col-span-1 space-y-8">
          {/* Watchlists Catalog */}
          <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl space-y-6">
            <h3 className="text-sm uppercase font-bold text-zinc-400 tracking-wider flex items-center space-x-2">
              <Grid className="h-4 w-4" />
              <span>Watchlists Catalog</span>
            </h3>

            {/* Create Watchlist Form */}
            <form onSubmit={handleCreateWatchlist} className="space-y-3 p-4 bg-zinc-950/40 border border-zinc-800 rounded-lg">
              <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Create Watchlist</div>
              <input
                type="text"
                placeholder="Name (e.g., Core AI Frameworks)"
                value={newWatchlistName}
                onChange={(e) => setNewWatchlistName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2 px-3 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500/50"
              />
              <input
                type="text"
                placeholder="Brief description"
                value={newWatchlistDesc}
                onChange={(e) => setNewWatchlistDesc(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2 px-3 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500/50"
              />
              <button
                type="submit"
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-zinc-50 rounded-lg font-bold text-[10px] flex items-center justify-center space-x-1 cursor-pointer transition-all duration-200"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Create Watchlist</span>
              </button>
            </form>

            {/* Watchlist Buttons List */}
            {watchlistLoading ? (
              <div className="py-10 text-center text-xs text-zinc-500">Querying watchlists...</div>
            ) : watchlists.length === 0 ? (
              <div className="py-10 text-center text-xs text-zinc-500">No watchlists configured.</div>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {watchlists.map((w) => (
                  <button
                    key={w.id}
                    onClick={() => setSelectedWatchlistId(w.id)}
                    className={`w-full flex items-center justify-between p-4 rounded-lg border text-left text-xs font-medium transition ${
                      selectedWatchlistId === w.id
                        ? "bg-indigo-600/10 border-indigo-500/50 text-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.05)]"
                        : "bg-zinc-950/20 border-zinc-800/80 text-zinc-400 hover:bg-zinc-900/40 hover:text-zinc-200"
                    }`}
                  >
                    <div>
                      <div className="font-bold text-zinc-200">{w.name}</div>
                      <div className="text-[10px] text-zinc-500 truncate max-w-[180px] mt-1">{w.description}</div>
                    </div>
                    <ChevronRight className="h-4 w-4 opacity-50" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Current Watchlist Details Monitor */}
          {currentWatchlist && (
            <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl space-y-6">
              <div className="flex justify-between items-start border-b border-zinc-800 pb-4">
                <div>
                  <h4 className="text-base font-bold text-zinc-200">{currentWatchlist.name}</h4>
                  <p className="text-xs text-zinc-500 mt-1">{currentWatchlist.description}</p>
                </div>
                <button
                  onClick={() => handleScanWatchlist(currentWatchlist.id)}
                  disabled={scanningWatchlistId === currentWatchlist.id}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-zinc-50 rounded-lg font-bold text-xs flex items-center space-x-1.5 cursor-pointer disabled:opacity-50 transition"
                >
                  <Play className={`h-3.5 w-3.5 ${scanningWatchlistId === currentWatchlist.id ? "animate-pulse" : ""}`} />
                  <span>{scanningWatchlistId === currentWatchlist.id ? "Detecting..." : "Scan"}</span>
                </button>
              </div>

              {/* Categories */}
              <div className="space-y-3">
                <h5 className="text-[10px] uppercase font-bold text-zinc-400 tracking-wider">Tracked Categories</h5>
                <div className="flex space-x-2">
                  <select
                    value={selectedAddCategoryId}
                    onChange={(e) => setSelectedAddCategoryId(e.target.value)}
                    className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg py-1.5 px-3 text-xs text-zinc-300 focus:outline-none"
                  >
                    <option value="">Select Category...</option>
                    {availableCategories
                      .filter((cat) => !(currentWatchlist?.category_items || []).some((ci) => ci.category_id === cat.category_id))
                      .map((cat) => (
                        <option key={cat.category_id} value={cat.category_id}>
                          {cat.name}
                        </option>
                      ))}
                  </select>
                  <button
                    onClick={handleAddCategory}
                    className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-zinc-300 text-xs font-bold transition cursor-pointer"
                  >
                    Add
                  </button>
                </div>

                <div className="space-y-1.5 max-h-[200px] overflow-y-auto pr-1">
                  {!currentWatchlist.category_items || currentWatchlist.category_items.length === 0 ? (
                    <div className="text-[10px] p-3 text-zinc-600 border border-dashed border-zinc-800 rounded-lg text-center">
                      No categories tracked
                    </div>
                  ) : (
                    currentWatchlist.category_items.map((ci) => (
                      <div
                        key={ci.id}
                        className="flex justify-between items-center p-2.5 bg-zinc-950/40 border border-zinc-800/80 rounded-lg text-xs text-zinc-300"
                      >
                        <span className="font-semibold">{getCategoryNameById(ci.category_id)}</span>
                        <button onClick={() => handleRemoveCategory(ci.category_id)} className="text-zinc-500 hover:text-rose-400 transition cursor-pointer">
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Repositories */}
              <div className="space-y-3 pt-2">
                <h5 className="text-[10px] uppercase font-bold text-zinc-400 tracking-wider">Tracked Repositories</h5>
                <div className="flex space-x-2">
                  <select
                    value={selectedAddRepoId}
                    onChange={(e) => setSelectedAddRepoId(e.target.value)}
                    className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg py-1.5 px-3 text-xs text-zinc-300 focus:outline-none"
                  >
                    <option value="">Select Repository...</option>
                    {availableRepositories
                      .filter((repo) => !(currentWatchlist?.repository_items || []).some((ri) => ri.repository_id === repo.id))
                      .map((repo) => (
                        <option key={repo.id} value={repo.id}>
                          {repo.name}
                        </option>
                      ))}
                  </select>
                  <button
                    onClick={handleAddRepository}
                    className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-zinc-300 text-xs font-bold transition cursor-pointer"
                  >
                    Add
                  </button>
                </div>

                <div className="space-y-1.5 max-h-[200px] overflow-y-auto pr-1">
                  {!currentWatchlist.repository_items || currentWatchlist.repository_items.length === 0 ? (
                    <div className="text-[10px] p-3 text-zinc-600 border border-dashed border-zinc-800 rounded-lg text-center">
                      No repositories tracked
                    </div>
                  ) : (
                    currentWatchlist.repository_items.map((ri) => (
                      <div
                        key={ri.id}
                        className="flex justify-between items-center p-2.5 bg-zinc-950/40 border border-zinc-800/80 rounded-lg text-xs text-zinc-300"
                      >
                        <span className="font-semibold truncate max-w-[180px]">
                          {getRepositoryNameById(ri.repository_id)}
                        </span>
                        <button onClick={() => handleRemoveRepository(ri.repository_id)} className="text-zinc-500 hover:text-rose-400 transition cursor-pointer">
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Alerts Inbox (Anomalies Feed) */}
        <div className="lg:col-span-2 border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-8 shadow-xl space-y-6">
          {/* Section Title & Filters */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-zinc-800 pb-4 gap-4">
            <h3 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <Bell className="h-5 w-5 text-indigo-400" />
              <span>Anomalies Notification Inbox</span>
            </h3>

            <div className="flex space-x-2">
              {/* Read Filter */}
              <select
                value={selectedAlertRead}
                onChange={(e) => setSelectedAlertRead(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 rounded-lg py-1.5 px-3 text-xs text-zinc-300 focus:outline-none"
              >
                <option value="unread">Unread Only</option>
                <option value="read">Read Only</option>
                <option value="all">All Alerts</option>
              </select>

              {/* Severity Filter */}
              <select
                value={selectedAlertSeverity}
                onChange={(e) => setSelectedAlertSeverity(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 rounded-lg py-1.5 px-3 text-xs text-zinc-300 focus:outline-none"
              >
                <option value="">All Severities</option>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
          </div>

          {/* Alerts Feed */}
          {alertsLoading ? (
            <div className="py-20 text-center space-y-4">
              <Activity className="h-8 w-8 text-indigo-500 animate-spin mx-auto" />
              <span className="text-zinc-500 text-sm">Syncing alerts inbox...</span>
            </div>
          ) : alerts.length === 0 ? (
            <div className="py-20 text-center text-zinc-500 text-sm flex flex-col items-center space-y-2">
              <CheckSquare className="h-10 w-10 text-zinc-600" />
              <span>Inbox clear. No anomaly warnings found.</span>
            </div>
          ) : (
            <div className="space-y-4 max-h-[700px] overflow-y-auto pr-1">
              {alerts.map((a) => {
                let alertClass = "";
                let textClass = "";
                switch (a.severity.toUpperCase()) {
                  case "CRITICAL":
                    alertClass = "border-l-4 border-rose-500 bg-rose-950/15";
                    textClass = "text-rose-400";
                    break;
                  case "HIGH":
                    alertClass = "border-l-4 border-amber-500 bg-amber-950/15";
                    textClass = "text-amber-400";
                    break;
                  case "MEDIUM":
                    alertClass = "border-l-4 border-yellow-500 bg-yellow-950/15";
                    textClass = "text-yellow-400";
                    break;
                  default:
                    alertClass = "border-l-4 border-blue-500 bg-blue-950/15";
                    textClass = "text-blue-400";
                    break;
                }

                return (
                  <div
                    key={a.id}
                    className={`flex flex-col md:flex-row md:items-center justify-between p-5 border border-zinc-800/80 rounded-xl transition-all duration-200 ${alertClass}`}
                  >
                    <div className="space-y-2 md:max-w-xl">
                      {/* Badges row */}
                      <div className="flex flex-wrap gap-2 items-center">
                        <span className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded border border-current ${textClass}`}>
                          {a.severity}
                        </span>
                        <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider bg-zinc-950/60 border border-zinc-800 px-2 py-0.5 rounded">
                          {a.alert_type.replace(/_/g, " ")}
                        </span>
                        {a.category_slug && (
                          <span className="text-[10px] text-indigo-400 font-semibold bg-indigo-950/30 px-1.5 py-0.5 rounded">
                            Category: {a.category_slug}
                          </span>
                        )}
                        {a.repository_name && (
                          <span className="text-[10px] text-cyan-400 font-semibold bg-cyan-950/30 px-1.5 py-0.5 rounded">
                            Repo: {a.repository_name}
                          </span>
                        )}
                      </div>

                      {/* Header details */}
                      <h4 className="text-sm font-extrabold text-zinc-100">{a.title}</h4>
                      <p className="text-xs text-zinc-400 leading-relaxed">{a.message}</p>

                      {/* Metric trace values */}
                      {a.previous_value !== null && a.current_value !== null && (
                        <div className="text-[10px] text-zinc-500 font-medium flex items-center space-x-1">
                          <Info className="h-3 w-3" />
                          <span>
                            Delta trace: <strong className="text-zinc-400">{a.previous_value}</strong> &rarr;{" "}
                            <strong className="text-zinc-300">{a.current_value}</strong>
                            {a.change_percent !== null && a.change_percent !== undefined && (
                              <span className="ml-1 text-emerald-400 font-bold">
                                ({a.change_percent > 0 ? "+" : ""}{a.change_percent.toFixed(1)}%)
                              </span>
                            )}
                          </span>
                        </div>
                      )}

                      <div className="text-[9px] text-zinc-500">
                        Logged: {new Date(a.created_at).toLocaleString()}
                      </div>
                    </div>

                    {/* Action button */}
                    {a.is_read === 0 && (
                      <div className="mt-4 md:mt-0 md:ml-4 flex-shrink-0">
                        <button
                          onClick={() => handleMarkAlertRead(a.id)}
                          className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-500 text-zinc-300 rounded-lg text-xs font-bold flex items-center space-x-1 transition cursor-pointer"
                        >
                          <CheckSquare className="h-3.5 w-3.5" />
                          <span>Mark Read</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
