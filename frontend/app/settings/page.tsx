"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { 
  Activity, 
  Save, 
  RefreshCw, 
  Trash2, 
  Key, 
  Settings as SettingsIcon,
  Check,
  AlertTriangle 
} from "lucide-react";
import type { SettingsConfig } from "../../types/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsConfig>({
    mock_mode: true,
    github_token: "",
    openai_key: "",
    ollama_endpoint: "",
    collectors_limit: 20
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [syncMessage, setSyncMessage] = useState("");
  
  // Load configuration
  useEffect(() => {
    fetch("http://localhost:8000/settings")
      .then(res => res.json())
      .then(data => {
        setSettings(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Settings Load Error:", err);
        setLoading(false);
      });
  }, []);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setSettings((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : name === "collectors_limit" ? Number(value) : value
    }));
  };

  // Save Settings
  const handleSave = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await fetch("http://localhost:8000/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      const data = await res.json();
      setSettings(data);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Save Settings Error:", err);
    } finally {
      setSaving(false);
    }
  };

  // Trigger manual sync pipeline
  const handleSync = async () => {
    setSyncing(true);
    setSyncMessage("Queueing ingestion pipelines...");
    try {
      const res = await fetch("http://localhost:8000/settings/sync", { method: "POST" });
      const data = await res.json();
      setSyncMessage(data.message || "Sync pipeline queued successfully!");
      setTimeout(() => setSyncMessage(""), 5000);
    } catch (err) {
      console.error("Manual Sync Error:", err);
      setSyncMessage("Sync trigger failed. Check backend logs.");
    } finally {
      setSyncing(false);
    }
  };

  // Clear and reset DB
  const handleReset = async () => {
    if (!confirm("Are you absolutely sure you want to clear all data and reset the SQLite database? This triggers a re-ingestion cycle in the background.")) {
      return;
    }
    setResetting(true);
    try {
      const res = await fetch("http://localhost:8000/settings/reset", { method: "POST" });
      const data = await res.json();
      alert(data.message || "Database successfully reset.");
    } catch (err) {
      console.error("Database Reset Error:", err);
    } finally {
      setResetting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-10 bg-zinc-950">
        <div className="text-center space-y-4">
          <Activity className="h-10 w-10 text-indigo-500 animate-spin mx-auto" />
          <h2 className="text-lg font-bold text-zinc-100">Loading Configuration Profiles...</h2>
        </div>
      </div>
    );
  }

  return (
    <main className="p-8 max-w-4xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50">
          Platform <span className="gradient-text">Settings</span>
        </h1>
        <p className="text-zinc-400 text-sm mt-2">
          Configure API credentials, toggle mock testing mode, and trigger data collection workflows.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* API Settings Form */}
        <form onSubmit={handleSave} className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-8 shadow-xl space-y-6">
          <h3 className="text-lg font-bold text-zinc-100 flex items-center space-x-2 border-b border-zinc-800 pb-4">
            <Key className="h-5 w-5 text-indigo-400" />
            <span>Credentials & Operations</span>
          </h3>
          
          <div className="space-y-4">
            {/* Toggle Mock Mode */}
            <div className="flex items-center justify-between p-4 bg-zinc-950/40 border border-zinc-800 rounded-lg">
              <div>
                <label className="text-sm font-bold text-zinc-200">Ingest Mock Data (Dynamic Sandbox)</label>
                <p className="text-xs text-zinc-500 mt-0.5">Toggles high-fidelity synthetic data. Essential for testing without API keys.</p>
              </div>
              <input
                type="checkbox"
                name="mock_mode"
                checked={settings.mock_mode}
                onChange={handleChange}
                className="h-5 w-5 rounded border-zinc-800 text-indigo-600 focus:ring-indigo-500 bg-zinc-950 cursor-pointer"
              />
            </div>

            {/* GitHub Token */}
            <div className="flex flex-col space-y-1.5">
              <label className="text-xs font-bold text-zinc-400 uppercase">GitHub Personal Access Token (PAT)</label>
              <input
                type="password"
                name="github_token"
                value={settings.github_token}
                onChange={handleChange}
                placeholder={settings.mock_mode ? "Not required in Mock Sandbox" : "ghp_xxxxxxxxxxxxxxxx"}
                disabled={settings.mock_mode}
                className="bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 px-4 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-indigo-500/50 disabled:opacity-40"
              />
              <p className="text-[10px] text-zinc-500">Improves API rate-limit threshold for repository collection searches.</p>
            </div>

            {/* OpenAI API Key */}
            <div className="flex flex-col space-y-1.5">
              <label className="text-xs font-bold text-zinc-400 uppercase">OpenAI API Key</label>
              <input
                type="password"
                name="openai_key"
                value={settings.openai_key}
                onChange={handleChange}
                placeholder={settings.mock_mode ? "Not required in Mock Sandbox" : "sk-proj-xxxxxxxxxxxxxxxx"}
                disabled={settings.mock_mode}
                className="bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 px-4 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-indigo-500/50 disabled:opacity-40"
              />
              <p className="text-[10px] text-zinc-500">Used for compiling dynamic weekly intelligence reports and summarizing trends (GPT-4o-mini).</p>
            </div>

            {/* Ollama Endpoint */}
            <div className="flex flex-col space-y-1.5">
              <label className="text-xs font-bold text-zinc-400 uppercase">Ollama Local API Endpoint</label>
              <input
                type="text"
                name="ollama_endpoint"
                value={settings.ollama_endpoint}
                onChange={handleChange}
                placeholder="http://localhost:11434"
                disabled={settings.mock_mode}
                className="bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 px-4 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-indigo-500/50 disabled:opacity-40"
              />
              <p className="text-[10px] text-zinc-500">Fallback local server model generating markdown insights locally (e.g. llama3).</p>
            </div>

            {/* Ingestion limits */}
            <div className="flex flex-col space-y-1.5">
              <label className="text-xs font-bold text-zinc-400 uppercase">Collectors Max Result Limits</label>
              <input
                type="number"
                name="collectors_limit"
                value={settings.collectors_limit}
                onChange={handleChange}
                className="bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 px-4 text-sm text-zinc-200 focus:outline-none focus:border-indigo-500/50"
              />
              <p className="text-[10px] text-zinc-500">Max hits scraped per query on GitHub, Reddit, HN, and arXiv API runs.</p>
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-zinc-50 rounded-lg font-bold text-xs flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
            >
              {saveSuccess ? (
                <>
                  <Check className="h-4 w-4" />
                  <span>Config Saved!</span>
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  <span>{saving ? "Saving..." : "Save Settings"}</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Trigger operations */}
        <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-8 shadow-xl space-y-6">
          <h3 className="text-lg font-bold text-zinc-100 flex items-center space-x-2 border-b border-zinc-800 pb-4">
            <SettingsIcon className="h-5 w-5 text-indigo-400" />
            <span>Manual Trigger Actions</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Sync trigger */}
            <div className="p-5 border border-zinc-800 bg-zinc-950/20 rounded-lg flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-bold text-zinc-200">Force Data Ingestion Sync</h4>
                <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                  Triggers scrapers, updates trends scores, calculates opportunities, and compiles weekly intelligence briefings.
                </p>
              </div>
              <div className="mt-6">
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="w-full px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-xs font-bold text-zinc-300 flex items-center justify-center space-x-1.5 cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
                  <span>{syncing ? "Ingesting..." : "Sync Pipeline Now"}</span>
                </button>
                {syncMessage && (
                  <div className="text-[10px] font-bold text-indigo-400 mt-2 text-center">
                    {syncMessage}
                  </div>
                )}
              </div>
            </div>

            {/* Reset DB */}
            <div className="p-5 border border-zinc-800 bg-zinc-950/20 rounded-lg flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-bold text-zinc-200 text-rose-400 flex items-center space-x-1">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Factory Database Reset</span>
                </h4>
                <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                  Clears sqlite database, drops table structures, seeds standard niche categories, and initiates a clean data pull.
                </p>
              </div>
              <div className="mt-6">
                <button
                  onClick={handleReset}
                  disabled={resetting}
                  className="w-full px-4 py-2.5 bg-rose-950/30 hover:bg-rose-950/50 border border-rose-800/40 rounded-lg text-xs font-bold text-rose-400 flex items-center justify-center space-x-1.5 cursor-pointer disabled:opacity-50"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>{resetting ? "Resetting..." : "Clear & Reset DB"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
