import json
import argparse
import os
from pathlib import Path

# Path to hyperparams.json in same directory
HYPERPARAMS_PATH = Path(__file__).resolve().parent / "hyperparams.json"

# Default values required by your spec
DEFAULTS = {
    "budget_control_strategy": "FULL-TRACK",
    "commands_limit": 40,
    "external_fix_strategy": 0
}

def load_hyperparams():
    with open(HYPERPARAMS_PATH, "r") as f:
        return json.load(f)

def save_hyperparams(data):
    with open(HYPERPARAMS_PATH, "w") as f:
        json.dump(data, f, indent=4)

def display_current_and_defaults():
    current = load_hyperparams()
    print("\n=== RepairAgent Quick Configuration ===")
    print(f"Budget Control Strategy:   current={current.get('budget_control.name')}  default={DEFAULTS['budget_control_strategy']}")
    print(f"Commands Limit:            current={current.get('commands_limit')}          default={DEFAULTS['commands_limit']}")
    print(f"External Fix Strategy:     current={current.get('external_fix_strategy')}    default={DEFAULTS['external_fix_strategy']}")
    print("=================================\n")

def apply_changes(args):
    data = load_hyperparams()

    if args.strategy:
        if args.strategy not in ["FULL-TRACK", "NO-TRACK"]:
            raise ValueError("budget_control must be FULL-TRACK or NO-TRACK")
        data["budget_control_strategy"] = args.strategy

    if args.commands is not None:
        if not (1 <= args.commands <= 100):
            raise ValueError("commands_limit must be between 1 and 100")
        data["commands_limit"] = args.commands

    if args.external is not None:
        if not (0 <= args.external <= 3):
            raise ValueError("external_fix_strategy must be between 0 and 3")
        data["external_fix_strategy"] = args.external

    save_hyperparams(data)

def print_welcome_banner():
    """Call this at startup of RepairAgent."""

    print("\n=== Welcome to RepairAgent ===")
    print("A configuration tool is available to adjust run settings.")
    print("Run it with:")
    print("    python -m repair_agent.config.manage_config --help")
    print("\nDefault Settings:")
    print(f"  Budget Control Strategy:  {DEFAULTS['budget_control_strategy']}")
    print(f"  Commands Limit:           {DEFAULTS['commands_limit']}")
    print(f"  External Fix Strategy:    {DEFAULTS['external_fix_strategy']}")
    print("=================================\n")

def main():
    parser = argparse.ArgumentParser(description="Modify RepairAgent hyperparameters")

    parser.add_argument("--strategy", help="FULL-TRACK or NO-TRACK")
    parser.add_argument("--commands", type=int, help="Command limit (1-100)")
    parser.add_argument("--external", type=int, help="External fix strategy (0-3)")
    parser.add_argument("--show", action="store_true", help="Show current & default values")

    args = parser.parse_args()

    if args.show:
        display_current_and_defaults()
        return

    if not any([args.strategy, args.commands, args.external]):
        print("No changes specified. Use --help for options.")
        return

    apply_changes(args)
    print("Configuration updated!\n")
    display_current_and_defaults()


if __name__ == "__main__":
    main()
