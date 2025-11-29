import uuid
import json
import asyncio
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


#Path configurations
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
AGENT_DIR = PROJECT_ROOT / "repair_agent"

HYPERPARAMS_PATH = AGENT_DIR / "hyperparams.json"
DEFAULT_PATH = BASE_DIR / "default_hyperparams.json"

RUN_SCRIPT = AGENT_DIR / "run_on_defects4j.sh"
DEFAULT_BUG_LIST = AGENT_DIR / "experimental_setups" / "bugs_list"
SET_API_KEY_SCRIPT = AGENT_DIR / "set_api_key.py"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS: dict[str, dict] = {}
PROCESSES: dict[str, asyncio.subprocess.Process] = {}


class RunRequest(BaseModel):
    modelName: str
    bugListPath: str | None = None


class ApiKeyRequest(BaseModel):
    apiKey: str

# Get configuration
@app.get("/api/config")
def get_config():
    if not HYPERPARAMS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"hyperparams.json not found at: {HYPERPARAMS_PATH}",
        )
    with open(HYPERPARAMS_PATH, "r") as f:
        return json.load(f)

# Save configuration
@app.put("/api/config")
def save_config(cfg: dict):
    with open(HYPERPARAMS_PATH, "w") as f:
        json.dump(cfg, f, indent=4)
    return cfg

# Get default configuration
@app.get("/api/default-config")
def default_config():
    if not DEFAULT_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"default_hyperparams.json not found at: {DEFAULT_PATH}",
        )
    with open(DEFAULT_PATH, "r") as f:
        return json.load(f)

# Set API Key
@app.post("/api/set-api-key")
def set_api_key(req: ApiKeyRequest):

    if not SET_API_KEY_SCRIPT.exists():
        raise HTTPException(
            status_code=500,
            detail=f"set_api_key.py not found at: {SET_API_KEY_SCRIPT}",
        )

    try:
        proc = subprocess.Popen(
            ["python", str(SET_API_KEY_SCRIPT)],
            cwd=str(AGENT_DIR),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, stderr = proc.communicate(req.apiKey + "\n", timeout=20)

        if proc.returncode != 0:
            raise HTTPException(
              status_code=500,
              detail=f"Failed to set API key. stderr: {stderr.strip()}"
            )

        return {"status": "ok", "message": "API key set successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running set_api_key.py: {e}",
        )


# Start a new run
@app.post("/api/run")
async def start_run(req: RunRequest):
    if not RUN_SCRIPT.exists():
        raise HTTPException(
            status_code=500,
            detail=f"run_on_defects4j.sh not found at: {RUN_SCRIPT}",
        )

    if req.bugListPath:
        candidate = Path(req.bugListPath)
        if not candidate.is_absolute():
            candidate = AGENT_DIR / req.bugListPath
        bug_list_path = candidate
    else:
        bug_list_path = DEFAULT_BUG_LIST

    if not bug_list_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Bug list file not found at: {bug_list_path}",
        )

    run_id = str(uuid.uuid4())
    RUNS[run_id] = {"status": "running", "logs": ""}

    async def run_agent():
        cmd = [
            "bash",
            str(RUN_SCRIPT),
            str(bug_list_path),
            "hyperparams.json",
            req.modelName,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(AGENT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        PROCESSES[run_id] = process

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decoded = line.decode(errors="replace")
            RUNS[run_id]["logs"] += decoded

        await process.wait()
        RUNS[run_id]["status"] = (
            "success" if process.returncode == 0 else "error"
        )

        PROCESSES.pop(run_id, None)

    asyncio.create_task(run_agent())
    return {"runId": run_id}

# Get run status and logs
@app.get("/api/run/{run_id}")
def get_run(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    return RUNS[run_id]

# Terminate a run
@app.post("/api/run/{run_id}/terminate")
async def terminate_run(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found")

    proc = PROCESSES.get(run_id)
    if proc is None:
        RUNS[run_id]["status"] = "terminated"
        RUNS[run_id]["logs"] += "\n[UI] Terminate requested, but process was not running."
        return {"status": "terminated"}

    try:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

        RUNS[run_id]["status"] = "terminated"
        RUNS[run_id]["logs"] += "\n[UI] Run terminated by user."
    finally:
        PROCESSES.pop(run_id, None)

    return {"status": "terminated"}
