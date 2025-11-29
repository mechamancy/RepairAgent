import { useEffect, useState, useRef } from "react";
import {
  getConfig,
  saveConfig,
  getDefaultConfig,
  startRun,
  getRun,
  setApiKey,
  terminateRun,
} from "./api";

type Config = {
  budget_control: {
    name: string;
    params: { "#fixes": number };
  };
  repetition_handling: string;
  external_fix_strategy: number;
  commands_limit: number;
  [key: string]: any;
};

type RunData = {
  status: string;
  logs: string;
};

const MODEL_OPTIONS = [
  "gpt-4o-mini",
  "gpt-4.1",
  "gpt-4o",
  "gpt-4.1-mini",
  "gpt-4.1-nano",
];

function App() {
  const [config, setConfig] = useState<Config | null>(null);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [savingConfig, setSavingConfig] = useState(false);

  const [model, setModel] = useState<string>("gpt-4o-mini");
  const [bugListPath, setBugListPath] = useState<string>(
    "experimental_setups/bugs_list"
  );

  const [runId, setRunId] = useState<string | null>(null);
  const [runData, setRunData] = useState<RunData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [apiKeyInput, setApiKeyInput] = useState("");
  const [apiKeyStatus, setApiKeyStatus] = useState<string | null>(null);

  const logRef = useRef<HTMLPreElement | null>(null);

  // Load config on mount
  useEffect(() => {
    (async () => {
      try {
        const cfg = await getConfig();
        setConfig(cfg);
      } catch (e: any) {
        setError(e.message || "Failed to load config");
      } finally {
        setLoadingConfig(false);
      }
    })();
  }, []);

  // Poll run logs
  useEffect(() => {
    if (!runId) return;

    const interval = setInterval(async () => {
      try {
        const data = await getRun(runId);
        setRunData(data);
        if (
          data.status === "success" ||
          data.status === "error" ||
          data.status === "terminated"
        ) {
          clearInterval(interval);
        }
      } catch (e: any) {
        setError(e.message || "Failed to fetch run status");
        clearInterval(interval);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [runId]);

  // Auto-scroll logs
  useEffect(() => {
    if (logRef.current && runData) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [runData?.logs]);

  const handleSaveConfig = async () => {
    if (!config) return;
    setSavingConfig(true);
    setError(null);
    try {
      const saved = await saveConfig(config);
      setConfig(saved);
    } catch (e: any) {
      setError(e.message || "Failed to save config");
    } finally {
      setSavingConfig(false);
    }
  };

  const handleRevertDefaults = async () => {
    setError(null);
    try {
      const defaults = await getDefaultConfig();
      setConfig(defaults);
      await saveConfig(defaults);
    } catch (e: any) {
      setError(e.message || "Failed to revert to defaults");
    }
  };

  const handleStartRun = async () => {
    setError(null);
    setRunData(null);
    try {
      const payload: { modelName: string; bugListPath?: string } = {
        modelName: model,
      };
      if (bugListPath.trim() !== "") {
        payload.bugListPath = bugListPath.trim();
      }
      const res = await startRun(payload);
      setRunId(res.runId);
    } catch (e: any) {
      setError(e.message || "Failed to start run");
    }
  };

  const handleSetApiKey = async () => {
    setApiKeyStatus(null);
    setError(null);
    if (!apiKeyInput.trim()) {
      setError("API key cannot be empty.");
      return;
    }
    try {
      const res = await setApiKey(apiKeyInput.trim());
      setApiKeyStatus(res.message);
      setApiKeyInput("");
    } catch (e: any) {
      setError(e.message || "Failed to set API key");
    }
  };

  const handleTerminate = async () => {
    if (!runId) return;
    try {
      await terminateRun(runId);
      const data = await getRun(runId);
      setRunData(data);
    } catch (e: any) {
      setError(e.message || "Failed to terminate run");
    }
  };

  if (loadingConfig) return <div style={{ padding: 20 }}>Loading config…</div>;
  if (!config) return <div style={{ padding: 20 }}>No config found.</div>;

  return (
    <div
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: 20,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1 style={{ fontSize: 24, marginBottom: 10 }}>RepairAgent Control Panel</h1>
      <p style={{ fontSize: 14, color: "#555", marginBottom: 20 }}>
        Edit <code>hyperparams.json</code>, set your OpenAI API key, choose a model,
        optionally choose a bug list file, and run RepairAgent.
      </p>

      {error && (
        <div
          style={{
            marginBottom: 16,
            padding: 10,
            border: "1px solid #f00",
            borderRadius: 6,
            color: "#900",
          }}
        >
          {error}
        </div>
      )}

      {/* API KEY SECTION */}
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
          marginBottom: 20,
        }}
      >
        <h2 style={{ fontSize: 18, marginBottom: 10 }}>OpenAI API Key</h2>
        <p style={{ fontSize: 13, color: "#555", marginBottom: 8 }}>
          This calls <code>python3.10 set_api_key.py</code> inside{" "}
          <code>repair_agent</code>. The key is not stored in the UI.
        </p>
        <input
          type="password"
          placeholder="sk-..."
          value={apiKeyInput}
          onChange={(e) => setApiKeyInput(e.target.value)}
          style={{ width: "100%", marginBottom: 8 }}
        />
        <button onClick={handleSetApiKey}>Set API Key</button>
        {apiKeyStatus && (
          <div style={{ marginTop: 8, fontSize: 13, color: "green" }}>
            {apiKeyStatus}
          </div>
        )}
      </section>

      {/* CONFIG SECTION */}
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
          marginBottom: 20,
        }}
      >
        <h2 style={{ fontSize: 18, marginBottom: 10 }}>Configuration</h2>

        {/* Budget Strategy */}
        <div style={{ marginBottom: 10 }}>
          <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>
            Budget Strategy
          </label>
          <select
            value={config.budget_control.name}
            onChange={(e) =>
              setConfig({
                ...config,
                budget_control: {
                  ...config.budget_control,
                  name: e.target.value,
                },
              })
            }
          >
            <option value="FULL-TRACK">FULL-TRACK</option>
            <option value="NO-TRACK">NO-TRACK</option>
            <option value="FORCED">FORCED (⚠️ experimental)</option>
          </select>
          {config.budget_control.name === "FORCED" && (
            <p style={{ color: "red", fontSize: 12, marginTop: 4 }}>
              ⚠️ FORCED is experimental and known to cause unstable behavior. Use only
              for debugging.
            </p>
          )}
        </div>

        {/* #fixes */}
        <div style={{ marginBottom: 10 }}>
          <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>
            #fixes
          </label>
          <input
            type="number"
            value={config.budget_control.params["#fixes"]}
            onChange={(e) =>
              setConfig({
                ...config,
                budget_control: {
                  ...config.budget_control,
                  params: { "#fixes": Number(e.target.value) },
                },
              })
            }
          />
        </div>

        {/* Repetition Handling */}
        <div style={{ marginBottom: 10 }}>
          <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>
            Repetition Handling
          </label>
          <select
            value={config.repetition_handling}
            onChange={(e) =>
              setConfig({ ...config, repetition_handling: e.target.value })
            }
          >
            <option value="RESTRICT">RESTRICT</option>
          </select>
        </div>

        {/* Commands Limit */}
        <div style={{ marginBottom: 10 }}>
          <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>
            Commands Limit
          </label>
          <input
            type="number"
            value={config.commands_limit}
            onChange={(e) =>
              setConfig({ ...config, commands_limit: Number(e.target.value) })
            }
          />
        </div>

        {/* External Fix Strategy (read-only) */}
        <div style={{ marginBottom: 10 }}>
          <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>
            External Fix Strategy (read-only)
          </label>
          <input
            type="number"
            value={config.external_fix_strategy}
            readOnly
          />
        </div>

        <div style={{ marginTop: 12 }}>
          <button onClick={handleSaveConfig} disabled={savingConfig}>
            {savingConfig ? "Saving…" : "Save Config"}
          </button>
          <button
            style={{ marginLeft: 10 }}
            onClick={handleRevertDefaults}
          >
            Revert to Defaults
          </button>
        </div>
      </section>

      {/* RUN SECTION */}
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 16,
        }}
      >
        <h2 style={{ fontSize: 18, marginBottom: 10 }}>Run RepairAgent</h2>

        <div style={{ marginBottom: 10 }}>
          <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>
            Model
          </label>
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            {MODEL_OPTIONS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: 10 }}>
          <label style={{ display: "block", fontSize: 14, marginBottom: 4 }}>
            Bug List Path
          </label>
          <input
            type="text"
            value={bugListPath}
            onChange={(e) => setBugListPath(e.target.value)}
            style={{ width: "100%" }}
            placeholder="experimental_setups/bugs_list"
          />
          <p style={{ fontSize: 12, color: "#555", marginTop: 4 }}>
            Relative paths are resolved from <code>repair_agent</code>. Leave as{" "}
            <code>experimental_setups/bugs_list</code> for the default behavior.
          </p>
        </div>

        <button onClick={handleStartRun}>Run RepairAgent</button>

        {runData &&
          runData.status !== "success" &&
          runData.status !== "error" &&
          runData.status !== "terminated" && (
            <button
              style={{ marginLeft: 10 }}
              onClick={handleTerminate}
            >
              Terminate
            </button>
          )}

        {runData && (
          <div style={{ marginTop: 16 }}>
            <div style={{ marginBottom: 8 }}>
              <strong>Status: </strong>
              {runData.status.toUpperCase()}
            </div>
            <pre
              ref={logRef}
              style={{
                border: "1px solid #aaa",
                borderRadius: 4,
                padding: 10,
                height: 260,
                overflowY: "auto",
                background: "#111",
                color: "#0f0",
                fontSize: 12,
                whiteSpace: "pre-wrap",
              }}
            >
              {runData.logs || "No logs yet."}
            </pre>
          </div>
        )}
      </section>
    </div>
  );
}

export default App;
