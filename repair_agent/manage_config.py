import json
import argparse
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
HYPERPARAMS_PATH = HERE / "hyperparams.json"
DEFAULT_HYPERPARAMS_PATH = HERE / "terminalconfig_default_hyperparams.json"

# Defaults sourced from terminalconfig_default_hyperparams.json
DISPLAY_DEFAULTS = {
    "budget_control": {"name": "FULL-TRACK"},
    "commands_limit": 40,
    "external_fix_strategy": 0,
    "repetition_handling": "RESTRICT"
}

VALID_BUDGET_OPTIONS = {"FULL-TRACK", "NO-TRACK", "FORCED"}
VALID_REPETITION_OPTIONS = {"ALLOW", "RESTRICT"}

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} not found.")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def display_current_and_defaults():
    try:
        current = load_json(HYPERPARAMS_PATH)
    except FileNotFoundError:
        print(f"Could not find {HYPERPARAMS_PATH}.")
        return

    budget_name = current.get("budget_control", {}).get("name")
    commands_limit = current.get("commands_limit")
    external_fix = current.get("external_fix_strategy")
    repetition = current.get("repetition_handling", DISPLAY_DEFAULTS["repetition_handling"])

    print("\n=== RepairAgent hyperparams (current vs display-default) ===")
    print(f"Budget Control (budget_control.name):   current={budget_name}   default={DISPLAY_DEFAULTS['budget_control']['name']}")
    print(f"Commands Limit (commands_limit):        current={commands_limit}    default={DISPLAY_DEFAULTS['commands_limit']}")
    print(f"External Fix Strategy (external_fix_strategy): current={external_fix}    default={DISPLAY_DEFAULTS['external_fix_strategy']}")
    print(f"Repetition Handling (repetition_handling): current={repetition}    default={DISPLAY_DEFAULTS['repetition_handling']}")
    print("============================================================\n")

def apply_changes(args):
    # Load the existing hyperparams (so we preserve keys we aren't changing)
    data = load_json(HYPERPARAMS_PATH)

    # Budget control (stored as nested object)
    if args.strategy is not None:
        strat = args.strategy.upper()
        if strat not in VALID_BUDGET_OPTIONS:
            raise ValueError(f"budget_control must be one of {sorted(VALID_BUDGET_OPTIONS)}")
        # Ensure budget_control object exists
        if "budget_control" not in data or not isinstance(data["budget_control"], dict):
            data["budget_control"] = {}
        data["budget_control"]["name"] = strat

    # repetition_handling
    if args.repetition is not None:
        rep = args.repetition.upper()
        if rep not in VALID_REPETITION_OPTIONS:
            raise ValueError(f"repetition_handling must be one of {sorted(VALID_REPETITION_OPTIONS)}")
        data["repetition_handling"] = rep

    # commands_limit
    if args.commands is not None:
        # note: check for None explicitly so 0 would work if it were allowed (but here min is 1)
        if not (1 <= args.commands <= 100):
            raise ValueError("commands_limit must be between 1 and 100")
        data["commands_limit"] = args.commands

    # external_fix_strategy: min 0, max 3
    if args.external is not None:
        if not (0 <= args.external <= 3):
            raise ValueError("external_fix_strategy must be between 0 and 3 (inclusive)")
        data["external_fix_strategy"] = args.external

    save_json(HYPERPARAMS_PATH, data)

def reset_to_defaults():
    if not DEFAULT_HYPERPARAMS_PATH.exists():
        raise FileNotFoundError(f"terminalconfig_default_hyperparams.json not found at {DEFAULT_HYPERPARAMS_PATH}")
    # Overwrite hyperparams.json with terminalconfig_default_hyperparams.json
    shutil.copyfile(DEFAULT_HYPERPARAMS_PATH, HYPERPARAMS_PATH)
    print(f"Reset complete: {HYPERPARAMS_PATH} overwritten with {DEFAULT_HYPERPARAMS_PATH}")

def print_welcome_banner():
    """Call this at RepairAgent startup to notify about the config tool."""
    print("\n=== Welcome to RepairAgent ===")
    print("To change runtime hyperparameters run the config tool:")
    print("    python -m repair_agent.config.manage_config --help")
    print("\nDefault / display values (these are the program defaults shown at startup):")
    print(f"  Budget Control:          {DISPLAY_DEFAULTS['budget_control']['name']} (options: FULL-TRACK, NO-TRACK, FORCED)")
    print(f"  Repetition Handling:     {DISPLAY_DEFAULTS['repetition_handling']} (options: ALLOW, RESTRICT)")
    print(f"  Commands Limit:          {DISPLAY_DEFAULTS['commands_limit']} (range: 1-100)")
    print(f"  External Fix Strategy:   {DISPLAY_DEFAULTS['external_fix_strategy']} (range: 0-3)")
    print("===============================================\n")

def parse_args(argv):
    parser = argparse.ArgumentParser(description="Modify RepairAgent hyperparameters")

    parser.add_argument("--strategy", type=str,
                        help="Budget control strategy: FULL-TRACK, NO-TRACK, or FORCED")

    parser.add_argument("--repetition", type=str,
                        help="Repetition handling: ALLOW or RESTRICT")

    parser.add_argument("--commands", type=int,
                        help="commands_limit (integer 1-100)")

    # EXTERNAL must accept 0 — check for is not None in code
    parser.add_argument("--external", type=int,
                        help="external_fix_strategy (integer 0-3)")

    parser.add_argument("--show", action="store_true",
                        help="Show current and default values")

    parser.add_argument("--reset", action="store_true",
                        help="Reset hyperparams.json to default_hyperparams.json (overwrite)")

    return parser.parse_args(argv)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    if args.show:
        display_current_and_defaults()
        return

    if args.reset:
        reset_to_defaults()
        # show the current values after reset
        display_current_and_defaults()
        return

    # If no modifications requested, tell user how to use --show/--help
    if not any([args.strategy, args.repetition, args.commands is not None, args.external is not None]):
        print("No changes specified. Use --show to see current values or --help for usage.")
        return

    # Apply changes (validates and saves)
    try:
        apply_changes(args)
    except Exception as exc:
        print(f"Error applying changes: {exc}")
        return

    print("Configuration updated!\n")
    display_current_and_defaults()

if __name__ == "__main__":
    main()
