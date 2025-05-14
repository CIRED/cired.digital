#!/usr/bin/env python3
"""
CLI tool to manage RAG engines across development and production environments.

Features:
- Discover available RAG engines based on directory structure.
- Discover available commands based on scripts present in the engine directory.
- Supports development and production environments.
- Load environment variables from per-engine configuration files.
- Execute corresponding shell scripts for various engine lifecycle commands.
- Includes validation, error handling, and optional debug output.

Available Commands:
  install                 Install/setup the RAG engine.
  start                   Start the RAG engine.
  validate                Validate that the engine is running correctly.
  stop                    Stop the RAG engine.
  clean                   Revert the directory to its clean state.
  push-index              Push the local index data to production.

Integration:
Within each engine directory:
- Commands must be implemented as shell scripts.
- Environment files must be named env_dev.cfg and env_prod.cfg.

This CLI is meant to be used locally in the development environment, and on the VPS in the production environment.
It uses only the standard Python library.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Configure logging for operational/debug logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


class EngineError(Exception):
    """Raised when an engine is missing or invalid."""


class EnvironmentFileError(Exception):
    """Raised when there is a problem with the environment file."""


class ScriptExecutionError(Exception):
    """Raised when a shell script fails to execute properly."""


def discover_engines() -> list[str]:
    """
    Discover available RAG engines based on subdirectories.

    Returns
    -------
        A sorted list of engine names.

    """
    engines = []
    for entry in BASE_DIR.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("_"):
            continue
        if not (entry / "start.sh").exists():
            continue
        engines.append(entry.name)
    return sorted(engines)


def discover_commands(engine: str) -> list[str]:
    """
    Discover available commands for a given engine based on shell scripts present.

    Args:
    ----
        engine: The name of the engine.

    Returns:
    -------
        A list of available command names.

    """
    engine_dir = BASE_DIR / engine
    if not engine_dir.is_dir():
        return []
    return sorted(f.stem.replace("_", "-") for f in engine_dir.glob("*.sh"))


def load_env(engine: str, env: str) -> None:
    """
    Load environment variables from a per-engine config file.

    Args:
    ----
        engine: The name of the engine.
        env: The environment to load variables for ("dev" or "prod").

    Raises:
    ------
        EnvironmentFileError: If an invalid line is found in the environment file.

    """
    env_file = BASE_DIR / engine / f"env_{env}.cfg"
    if not env_file.is_file():
        logger.warning(
            'Environment file %s not found for engine "%s".', env_file, engine
        )
        return

    logger.info("Loading environment variables from %s", env_file)
    env_text = env_file.read_text(encoding="utf-8")
    for line_number, line in enumerate(env_text.splitlines(), start=1):
        line = line.strip()
        if line and not line.startswith("#"):
            if "=" not in line:
                raise EnvironmentFileError(
                    f"Invalid line {line_number} in {env_file}: {line}"
                )
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in os.environ:
                logger.warning(
                    "Overriding existing environment variable: %s (expected if reloading configs)",
                    key,
                )
            os.environ[key] = value


def get_engine_dir(engine: str) -> Path:
    """
    Get the filesystem path for a given engine.

    Args:
    ----
        engine: The name of the engine.

    Returns:
    -------
        The Path object to the engine directory.

    Raises:
    ------
        EngineError: If the engine directory does not exist.

    """
    engine_dir = BASE_DIR / engine
    if not engine_dir.is_dir():
        raise EngineError(f'Engine "{engine}" not found under {BASE_DIR}/')
    return engine_dir


def run_script(engine: str, command: str, env: str, debug: bool) -> None:
    """
    Execute the corresponding shell script for an engine and command.

    Args:
    ----
        engine: The name of the engine.
        command: The lifecycle command to execute.
        env: The target environment ("dev" or "prod").
        debug: Whether to show full stdout/stderr output.

    Raises:
    ------
        EngineError: If the script is not found.
        ScriptExecutionError: If the script execution fails.

    """
    engine_dir = get_engine_dir(engine)
    script_name = f"{command.replace('-', '_')}.sh"
    script_path = engine_dir / script_name

    if not script_path.is_file():
        available_scripts = [f.name for f in engine_dir.glob("*.sh")]
        raise EngineError(
            f'Script "{script_name}" not found for engine "{engine}". '
            f"Available scripts: {available_scripts}"
        )

    load_env(engine, env)

    logger.info("Running %s for %s in %s environment...", script_name, engine, env)
    try:
        result = subprocess.run(
            ["bash", str(script_path), env], check=True, capture_output=True, text=True
        )
        if debug:
            logger.debug("STDOUT:\n%s", result.stdout)
            logger.debug("STDERR:\n%s", result.stderr)
    except subprocess.CalledProcessError as e:
        raise ScriptExecutionError(
            f'Script "{script_name}" failed with exit code {e.returncode}\n'
            f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        )


def list_available_engines_and_commands(available_engines: list[str]) -> None:
    """
    List available engines and their commands.

    Args:
    ----
        available_engines: List of detected engine names.

    Raises:
    ------
        EngineError: If no engines are detected.

    """
    if not available_engines:
        raise EngineError("No engines detected.")

    print("Available engines and their commands:")
    for engine in available_engines:
        print(f"\nEngine: {engine}")
        commands = discover_commands(engine)
        if commands:
            for cmd in commands:
                print(f"  - {cmd}")
        else:
            print("  (No commands found)")


def main() -> None:
    """
    Entry point of the CLI tool.

    Discover available engines, parse arguments, and dispatch lifecycle commands.

    Raises
    ------
        SystemExit: If an error occurs during CLI execution.

    """
    try:
        available_engines = discover_engines()

        parser = argparse.ArgumentParser(
            description="Manage RAG engines across development and production environments.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument(
            "command",
            nargs="?",
            help="Action to perform on the RAG engine (start, stop, etc.).",
        )
        parser.add_argument(
            "--engine",
            help="Name of the engine (must match a detected engine folder).",
        )
        parser.add_argument(
            "--env",
            default="dev",
            choices=["dev", "prod"],
            help="Target environment to operate on (default: dev).",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging level and show script output.",
        )
        parser.add_argument(
            "--list-commands",
            action="store_true",
            help="List available commands for the specified engine (for all engines if none is given).",
        )

        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)

        args = parser.parse_args()

        # Set debug level based on arguments or environment variable
        if args.debug or os.environ.get("RAGCTL_DEBUG") == "1":
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")

        if args.list_commands:
            if args.engine:
                cmds = discover_commands(args.engine)
                print(f"Commands for {args.engine}: {cmds or '(none)'}")
            else:
                list_available_engines_and_commands(available_engines)
            sys.exit(0)

        if not args.command or not args.engine:
            parser.print_help(sys.stderr)
            sys.exit(1)

        if args.engine not in available_engines:
            raise EngineError(f"Unknown engine: {args.engine}")

        run_script(args.engine, args.command, args.env, args.debug)

    except (EngineError, EnvironmentFileError, ScriptExecutionError) as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
