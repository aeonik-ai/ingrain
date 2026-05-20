"""Command line interface for Aeonik Ingrain."""

from __future__ import annotations

import argparse
import json
import os
import sys
from importlib import resources
from pathlib import Path

from aeonik_ingrain import PRODUCT_NAME, TAGLINE, __version__
from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore, MIND_EVENT_TYPES
from aeonik_ingrain.demo import DEMO_EVENTS, run_demo
from aeonik_ingrain.evals.les_hard import format_les_hard, run_les_hard, write_les_hard_artifacts
from aeonik_ingrain.evals.live_openviking import (
    OpenVikingLiveError,
    format_live_openviking_comparison,
    run_live_openviking_comparison,
    write_live_openviking_artifacts,
)
from aeonik_ingrain.evals.live_les import format_live_les, format_live_les_markdown, run_live_les
from aeonik_ingrain.evals.runner import format_eval, run_eval
from aeonik_ingrain.ingest.hermes import hermes_home, ingest_hermes
from aeonik_ingrain.practice import write_practice_artifacts
from aeonik_ingrain.report import build_report
from aeonik_ingrain.security import has_likely_secret
from aeonik_ingrain.skills import AGENTS, install_skill, render_skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingrain", description=f"{PRODUCT_NAME}: {TAGLINE}")
    parser.add_argument("--home", help="Ingrain home directory. Defaults to ./.ingrain or INGRAIN_HOME.")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize local .ingrain storage.")

    remember = sub.add_parser("remember", help="Record a correction, decision, lesson, project fact, or outcome.")
    remember.add_argument("text", nargs="+", help="Text to remember.")
    remember.add_argument("--type", default="lesson", choices=["correction", "decision", "lesson", "project_fact", "track_record", "risk", "status"])

    record = sub.add_parser("record", help=argparse.SUPPRESS)
    record.add_argument("text", nargs="+", help="Raw event text.")
    record.add_argument("--source", default="manual")
    record.add_argument("--runner", default="generic")
    record.add_argument("--event-type", default="observation", choices=sorted(MIND_EVENT_TYPES))
    record.add_argument("--actor", default="user")
    record.add_argument("--session-id")
    record.add_argument("--project-id")
    record.add_argument("--thread-id")
    record.add_argument("--meta-json", default="{}")

    ingest = sub.add_parser("ingest", help="Ingest runner history.")
    ingest_sub = ingest.add_subparsers(dest="ingest_target")
    hermes = ingest_sub.add_parser("hermes", help="Ingest Hermes state and built-in memory.")
    hermes.add_argument("--hermes-home", help="Hermes home directory. Defaults to HERMES_HOME or ~/.hermes.")
    hermes.add_argument("--limit", type=int, default=250, help="Max rows per candidate Hermes table.")

    sub.add_parser("compile", help="Compile ledger events into learned experience.")

    hyd = sub.add_parser("hydrate", help="Print compact learned-experience context.")
    hyd.add_argument("--query", default="", help="What the agent is about to do.")
    hyd.add_argument("--limit", type=int, default=12)
    hyd.add_argument("--max-chars", type=int, default=6000)
    hyd.add_argument("--level", choices=["brief", "cards", "evidence"], default="cards", help="Hydration detail level.")

    practice = sub.add_parser("practice", help="Write PRACTICE.md and source-linked practice cards.")
    practice.add_argument("--output", help="Output path. Defaults to ./PRACTICE.md.")

    skill = sub.add_parser("skill", help="Install or print agent skill instructions.")
    skill_sub = skill.add_subparsers(dest="skill_command")
    skill_install = skill_sub.add_parser("install", help="Install an Ingrain skill for an agent.")
    skill_install.add_argument("agent", nargs="?", default="generic", choices=AGENTS)
    skill_install.add_argument("--target-dir", help="Directory to write the skill into. Defaults to the agent's conventional location.")
    skill_show = skill_sub.add_parser("show", help="Print an Ingrain skill template.")
    skill_show.add_argument("agent", nargs="?", default="generic", choices=AGENTS)

    attach = sub.add_parser("attach", help="Initialize, compile PRACTICE.md, and install an agent skill.")
    attach.add_argument("--agent", default="generic", choices=AGENTS)
    attach.add_argument("--target-dir", help="Directory to write the skill into.")
    attach.add_argument("--practice-path", help="PRACTICE.md output path. Defaults to ./PRACTICE.md.")
    attach.add_argument("--no-skill", action="store_true", help="Only initialize and write PRACTICE.md.")

    eval_parser = sub.add_parser("eval", help="Run deterministic LES-Core (Learned Experience Score) smoke eval.")
    eval_parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")

    compare = sub.add_parser("compare", help="Run a real live OpenViking resource-retrieval eval.")
    compare.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    compare.add_argument("--openviking-endpoint", default=os.environ.get("OPENVIKING_ENDPOINT", "http://127.0.0.1:1933"))
    compare.add_argument("--openviking-account", default=os.environ.get("OPENVIKING_ACCOUNT", "default"))
    compare.add_argument("--openviking-user", default=os.environ.get("OPENVIKING_USER", "default"))
    compare.add_argument("--openviking-agent", default=os.environ.get("OPENVIKING_AGENT", "hermes"))
    compare.add_argument("--openviking-timeout", type=int, default=90)
    compare.add_argument("--output-dir", help="Directory for real OpenViking raw output, JSON, CSV, and report.")

    les_hard = sub.add_parser("les-hard", help="Run LES-Hard v0 Ingrain self-eval.")
    les_hard.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    les_hard.add_argument("--output-dir", default="docs/evidence/les-hard-v0", help="Directory for raw outputs, JSON, CSV, and report.")
    les_hard.add_argument("--report", default="docs/les-hard-report.md", help="Markdown report path to update.")

    live_eval = sub.add_parser("live-eval", help="Run live LES-Core provider smoke eval against installed Hermes provider APIs.")
    live_eval.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    live_eval.add_argument("--output-dir", default="docs/evidence/live-les-first-loop", help="Directory for raw outputs, command logs, JSON, CSV, and report.")
    live_eval.add_argument("--report", default="docs/live-eval-report.md", help="Markdown report path to update.")
    live_eval.add_argument("--provider", action="append", help="Provider to run. Repeat or comma-separate. Defaults to hermes-default, ingrain, hindsight, openviking.")
    live_eval.add_argument("--hermes-root", help="Hermes source/runtime root. Defaults to ~/.hermes/hermes-agent.")
    live_eval.add_argument("--hermes-python", help="Hermes venv Python. Defaults to <hermes-root>/venv/bin/python.")
    live_eval.add_argument("--openviking-endpoint", default=os.environ.get("OPENVIKING_ENDPOINT"))
    live_eval.add_argument("--timeout", type=int, default=90)

    demo = sub.add_parser("demo", help="Run a deterministic launch demo.")
    demo.add_argument("name", nargs="?", default="correction", choices=sorted(DEMO_EVENTS))
    demo.add_argument("--persist", action="store_true", help="Write demo events into --home instead of a temp store.")

    sub.add_parser("report", help="Print learned-experience report.")
    sub.add_parser("doctor", help="Check local setup.")

    install = sub.add_parser("install", help="Install runner integrations.")
    install_sub = install.add_subparsers(dest="install_target")
    install_hermes = install_sub.add_parser("hermes", help="Install Hermes memory provider plugin.")
    install_hermes.add_argument("--hermes-home", help="Hermes home directory. Defaults to HERMES_HOME or ~/.hermes.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if not args.command:
        parser.print_help()
        return 0

    store = IngrainStore(args.home)

    if args.command == "init":
        store.initialize()
        print(f"Initialized Aeonik Ingrain at {store.home}")
        return 0

    if args.command == "remember":
        store.initialize()
        text = " ".join(args.text)
        event_type = "decision" if args.type == "decision" else "observation"
        ref = store.add_event(
            source="manual",
            runner="generic",
            event_type=event_type,
            actor="user",
            text=text,
            meta={"remember_type": args.type},
        )
        print(f"Recorded {args.type}: {ref.id}")
        if has_likely_secret(text):
            print("Warning: input looked like it may contain a secret; stored text was redacted.")
        return 0

    if args.command == "record":
        store.initialize()
        try:
            meta = json.loads(args.meta_json or "{}")
        except json.JSONDecodeError as exc:
            print(f"Invalid --meta-json: {exc}", file=sys.stderr)
            return 2
        ref = store.add_event(
            source=args.source,
            runner=args.runner,
            event_type=args.event_type,
            actor=args.actor,
            text=" ".join(args.text),
            session_id=args.session_id,
            project_id=args.project_id,
            thread_id=args.thread_id,
            meta=meta,
        )
        print(f"Recorded event: {ref.id}")
        return 0

    if args.command == "ingest":
        if args.ingest_target == "hermes":
            result = ingest_hermes(store, hermes_home_path=args.hermes_home, limit=args.limit)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        print("Specify an ingest target, e.g. `ingrain ingest hermes`", file=sys.stderr)
        return 2

    if args.command == "compile":
        result = compile_store(store)
        print(f"Compiled {result['promotions']} learned items from {result['events']} events into {store.compiled_dir}")
        return 0

    if args.command == "hydrate":
        output = hydrate(store, query=args.query, limit=args.limit, max_chars=args.max_chars, level=args.level)
        print(output or "No learned experience found. Run `ingrain remember ...` or `ingrain ingest hermes` first.")
        return 0

    if args.command == "practice":
        compile_store(store)
        result = write_practice_artifacts(store, output_path=args.output)
        print(f"Wrote {result['practice_path']}")
        print(f"Wrote {result['card_count']} practice cards into {store.practice_cards_dir}")
        return 0

    if args.command == "skill":
        if args.skill_command == "install":
            target = install_skill(args.agent, target_dir=args.target_dir)
            print(f"Installed Ingrain {args.agent} skill to {target}")
            return 0
        if args.skill_command == "show":
            print(render_skill(args.agent))
            return 0
        print("Specify a skill command, e.g. `ingrain skill install codex`", file=sys.stderr)
        return 2

    if args.command == "attach":
        store.initialize()
        compile_store(store)
        practice_result = write_practice_artifacts(store, output_path=args.practice_path)
        print(f"Wrote {practice_result['practice_path']}")
        print(f"Wrote {practice_result['card_count']} practice cards into {store.practice_cards_dir}")
        if not args.no_skill:
            target = install_skill(args.agent, target_dir=args.target_dir)
            print(f"Installed Ingrain {args.agent} skill to {target}")
        return 0

    if args.command == "eval":
        result = run_eval(output_home=store.home)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(format_eval(result))
            print(f"\nWrote {store.evals_dir / 'latest.json'}")
        return 0

    if args.command == "compare":
        try:
            result = run_live_openviking_comparison(
                endpoint=args.openviking_endpoint,
                account=args.openviking_account,
                user=args.openviking_user,
                agent=args.openviking_agent,
                timeout=args.openviking_timeout,
            )
        except OpenVikingLiveError as exc:
            print(f"OpenViking live comparison failed: {exc}", file=sys.stderr)
            return 1
        formatter = format_live_openviking_comparison
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(formatter(result))
            if args.output_dir:
                artifacts = write_live_openviking_artifacts(result, args.output_dir)
                print(f"\nWrote {artifacts['report']}")
        if args.json and args.output_dir:
            write_live_openviking_artifacts(result, args.output_dir)
        return 0

    if args.command == "les-hard":
        result = run_les_hard()
        artifacts = write_les_hard_artifacts(result, args.output_dir)
        if args.report:
            report_path = Path(args.report).expanduser()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(Path(artifacts["report"]).read_text(encoding="utf-8"), encoding="utf-8")
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(format_les_hard(result))
            print(f"\nWrote {artifacts['report']}")
            if args.report:
                print(f"Wrote {args.report}")
        return 0

    if args.command == "live-eval":
        result = run_live_les(
            output_dir=args.output_dir,
            providers=args.provider,
            hermes_root=args.hermes_root,
            hermes_python=args.hermes_python,
            openviking_endpoint=args.openviking_endpoint,
            timeout=args.timeout,
        )
        report_text = format_live_les_markdown(result)
        if args.report:
            report_path = Path(args.report).expanduser()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_text, encoding="utf-8")
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(format_live_les(result))
            if args.report:
                print(f"\nWrote {args.report}")
        return 0

    if args.command == "demo":
        demo_home = store.home if args.persist else None
        print(run_demo(args.name, home=demo_home))
        return 0

    if args.command == "report":
        print(build_report(store))
        return 0

    if args.command == "doctor":
        return _doctor(store)

    if args.command == "install":
        if args.install_target == "hermes":
            target = install_hermes_provider(args.hermes_home)
            print(f"Installed Hermes provider to {target}")
            print("Enable with: hermes config set memory.provider ingrain")
            print("Note: Hermes currently supports one external memory.provider at a time.")
            return 0
        print("Specify an install target, e.g. `ingrain install hermes`", file=sys.stderr)
        return 2

    parser.print_help()
    return 0


def _doctor(store: IngrainStore) -> int:
    lines = ["Aeonik Ingrain Doctor", ""]
    lines.append(f"Python: {sys.version.split()[0]}")
    lines.append(f"Ingrain home: {store.home}")
    lines.append(f"Database exists: {store.db_path.exists()}")
    lines.append(f"Compiled dir exists: {store.compiled_dir.exists()}")
    lines.append(f"Practice cards dir exists: {store.practice_cards_dir.exists()}")
    h_home = hermes_home(None)
    lines.append(f"Hermes home: {h_home}")
    lines.append(f"Hermes state.db exists: {(h_home / 'state.db').exists()}")
    lines.append(f"Hermes plugins dir exists: {(h_home / 'plugins').exists()}")
    print("\n".join(lines))
    return 0


def install_hermes_provider(hermes_home_arg: str | None = None) -> Path:
    h_home = hermes_home(hermes_home_arg)
    target_dir = h_home / "plugins" / "ingrain"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "__init__.py"
    source = resources.files("aeonik_ingrain").joinpath("hermes_provider.py")
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    plugin_yaml = target_dir / "plugin.yaml"
    plugin_yaml.write_text(
        "name: ingrain\n"
        "description: Aeonik Ingrain learned experience provider for Hermes.\n",
        encoding="utf-8",
    )
    return target


if __name__ == "__main__":
    raise SystemExit(main())
