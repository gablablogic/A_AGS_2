#!/usr/bin/env python3
"""
json_to_autogen_py.py  —  Convert an AutoGen Studio (v0.4.x) JSON spec into a runnable Python file.

WHAT THIS DOES
--------------
- Reads the JSON that AutoGen Studio exports (your "team" or "agent" configuration).
- Generates a *stand-alone* Python file that:
  1) imports the correct classes (based on the "provider" fields in your JSON),
  2) reconstructs the object graph using the official `.load_component(config_dict)` method,
  3) and runs your Team/Agent with a demo task so you can verify it works.

WHY `.load_component(...)`?
---------------------------
In AutoGen 0.4.x, components (Teams, Agents, Tools, ModelClients, etc.) are designed
to round-trip via config dictionaries. The canonical, future-proof API is:
    MyClass.load_component(config_dict)
It hides constructor details that might change version to version, and it works for
*all* component types consistently. The generated file is still pure Python — no JSON
at runtime — but remains stable across updates.

ADVANCED (optional): "True constructors"
----------------------------------------
If you prefer hand-written constructors like `AssistantAgent(name="...")`, you can
extend the `EXPLICIT_CTORS` mapping below. For a small set of well-known classes,
you can translate the JSON subset you care about to real constructor calls.
For everything else, the generator will fall back to `.load_component(...)`.

USAGE
-----
$ python json_to_autogen_py.py team-config.json -o run_team_generated.py
$ python run_team_generated.py

SECURITY NOTE
-------------
Only convert JSON you trust. A malicious "provider" could point to a dangerous class
path. This generator *does not execute* the JSON, it just *imports* classes for code
generation — but you should still treat the input as untrusted and review output.
"""

import argparse
import json
import textwrap
from pathlib import Path
from typing import Dict, Any, Set, Tuple

# -----------------------------------------------------------------------------
# Helper 1: split a "provider" dotted path into (module, class)
# Example: "autogen_agentchat.teams.RoundRobinGroupChat" ->
#          ("autogen_agentchat.teams", "RoundRobinGroupChat")
# -----------------------------------------------------------------------------
def split_provider(provider: str) -> Tuple[str, str]:
    mod, cls = provider.rsplit(".", 1)
    return mod, cls


# -----------------------------------------------------------------------------
# Helper 2: turn a Python dict (parsed from JSON) into a pretty Python literal.
# We use pprint to generate a legible, deterministic representation.
# IMPORTANT: The output is Python code, not JSON (quotes, True/False/None, etc.).
# -----------------------------------------------------------------------------
def dict_to_python_literal(d: Any) -> str:
    import pprint
    return pprint.pformat(d, width=88, indent=2, compact=False, sort_dicts=True)


# -----------------------------------------------------------------------------
# Helper 3: Walk the spec to collect all "provider" strings.
# We use these to generate import lines at the top of the output file.
# Note: We collect *every* provider we find, not just the top-level team.
# -----------------------------------------------------------------------------
def collect_providers(spec: Any, bag: Set[str] | None = None) -> Set[str]:
    if bag is None:
        bag = set()
    if isinstance(spec, dict):
        prov = spec.get("provider")
        if isinstance(prov, str):
            bag.add(prov)
        for v in spec.values():
            collect_providers(v, bag)
    elif isinstance(spec, list):
        for v in spec:
            collect_providers(v, bag)
    return bag


# -----------------------------------------------------------------------------
# OPTIONAL: explicit constructor templates for specific classes.
# HOW TO USE:
#  - Key = fully-qualified provider string (module.ClassName)
#  - Value = a Python f-string template that assigns to a variable named {var}
#  - The template receives the *entire* config dictionary via {cfg!r},
#    so you can cherry-pick fields (e.g., cfg["config"]["name"]) to call the
#    class constructor explicitly.
#
# If no template exists for a provider, we fall back to `.load_component(cfg)`.
#
# Example template (commented for safety, adapt if needed):
# EXPLICIT_CTORS["autogen_agentchat.agents.AssistantAgent"] = (
#     "{var} = AssistantAgent("
#     "name={cfg['config'].get('name')!r}, "
#     "system_message={cfg['config'].get('system_message')!r}"
#     ")"
# )
# -----------------------------------------------------------------------------
EXPLICIT_CTORS: Dict[str, str] = {
    # Add explicit templates here if you want true constructors for specific classes.
}


# -----------------------------------------------------------------------------
# Core code emitter: build Python code that reconstructs the top-level component.
# Strategy:
#  - If a provider has an explicit template in EXPLICIT_CTORS, render it.
#  - Otherwise, fall back to {Class}.load_component(<dict literal>).
# The function returns both the code string and a set of (module, class) imports.
# -----------------------------------------------------------------------------
def emit_builder(spec: Dict[str, Any], var: str = "team",
                 imports: Set[Tuple[str, str]] | None = None) -> tuple[str, Set[Tuple[str, str]]]:
    if imports is None:
        imports = set()

    if not isinstance(spec, dict) or "provider" not in spec:
        raise ValueError("Top-level spec must be a dict with a 'provider' key.")

    provider = spec["provider"]
    module, cls_name = split_provider(provider)
    imports.add((module, cls_name))

    # If the user has provided an explicit constructor template for this provider, use it.
    template = EXPLICIT_CTORS.get(provider)
    if template:
        # The template can reference:
        #   - {var}: variable name to assign the built object to
        #   - {cfg!r}: the full config dict (repr form) for flexible extraction
        code = template.format(var=var, cfg=spec)
        return code, imports

    # Default path: use .load_component(...) which works for *all* components.
    cfg_literal = dict_to_python_literal(spec)
    code = f"{var} = {cls_name}.load_component({cfg_literal})"
    return code, imports


# -----------------------------------------------------------------------------
# Code-generation entry point:
#  - reads JSON,
#  - creates import lines,
#  - emits the builder code,
#  - adds a simple async main() that runs the team/agent.
# -----------------------------------------------------------------------------
def generate_python_from_json(json_path: Path, out_path: Path) -> None:
    # 1) Load JSON as Python data.
    spec = json.loads(json_path.read_text(encoding='utf-8'))

    # 2) Collect every provider path inside the spec tree (for imports).
    _ = sorted(collect_providers(spec))  # currently not used, but kept for clarity

    # 3) Emit the builder for the *top-level* component (usually a Team or Agent).
    body_code, import_set = emit_builder(spec, var="team", imports=set())

    # 4) Build consolidated import lines:
    #    group classes by module -> "from module import ClassA, ClassB"
    by_module: Dict[str, Set[str]] = {}
    for mod, cls in import_set:
        by_module.setdefault(mod, set()).add(cls)

    import_lines = [f"from {mod} import {', '.join(sorted(classes))}" for mod, classes in sorted(by_module.items())]

    # 5) Create a minimal runner that calls team.run(...).
    run_block = textwrap.dedent(
        """
        import asyncio

        async def main():
            # 'team' is constructed above. Provide any task you want to run:
            result = await team.run(task="Say hello (generated code).")
            print(result)

        if __name__ == "__main__":
            asyncio.run(main())
        """
    ).strip()

    # 6) Compose the final file.
    header = textwrap.dedent(
        f"""\
        # This file was generated from: {json_path.name}
        # It reconstructs your AutoGen 0.4.x configuration in pure Python.
        # You can now edit it freely (no JSON needed at runtime).
        """
    ).rstrip()

    content = "\n\n".join([header, *import_lines, "", body_code, "", run_block, ""])

    # 7) Write output.
    out_path.write_text(content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(
        description="Generate a runnable Python file from an AutoGen Studio (0.4.x) JSON spec."
    )
    parser.add_argument("json_path", help="Path to the Studio JSON file (e.g., team-config.json)")
    parser.add_argument("-o", "--out", default="run_team_generated.py",
                        help="Output Python file (default: run_team_generated.py)")
    args = parser.parse_args()

    json_path = Path(args.json_path)
    out_path = Path(args.out)

    if not json_path.exists():
        raise SystemExit(f"Input JSON not found: {json_path}")

    generate_python_from_json(json_path, out_path)
    print(f"✔ Generated: {out_path}")


if __name__ == "__main__":
    main()
