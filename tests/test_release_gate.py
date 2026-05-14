import importlib.util
import sys
from pathlib import Path


def _release_gate_module():
    path = Path(__file__).resolve().parents[1] / "ops" / "scripts" / "release_gate.py"
    spec = importlib.util.spec_from_file_location("release_gate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_safe_command_redacts_sensitive_flag_values():
    release_gate = _release_gate_module()

    command = [
        "python",
        "ops/scripts/smoke_check.py",
        "--email",
        "admin@example.com",
        "--password",
        "local-password",
        "--mongo-url",
        "mongodb://user:" + "pass@localhost:27017/db",
    ]

    assert release_gate.safe_command(command) == [
        "python",
        "ops/scripts/smoke_check.py",
        "--email",
        "<redacted>",
        "--password",
        "<redacted>",
        "--mongo-url",
        "<redacted>",
    ]


def test_load_env_file_parses_simple_key_values(tmp_path):
    release_gate = _release_gate_module()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "# comment",
            "MONGO_URL='mongodb://localhost:27017'",
            'DB_NAME="pltu_tenayan"',
            "EMPTY=",
        ]),
        encoding="utf-8",
    )

    assert release_gate.load_env_file(env_file) == {
        "MONGO_URL": "mongodb://localhost:27017",
        "DB_NAME": "pltu_tenayan",
        "EMPTY": "",
    }
