from scripts.check_repo_hygiene import classify_entries, parse_status


def test_classify_entries_allows_documented_local_only_worktree_changes():
    entries = parse_status(
        "\n".join([
            " M backend/.env",
            " M frontend/.env",
        ])
    )

    allowed, blocking = classify_entries(entries)

    assert [entry.path for entry in allowed] == [
        "backend/.env",
        "frontend/.env",
    ]
    assert blocking == []


def test_classify_entries_blocks_source_changes_and_staged_local_only_files():
    entries = parse_status(
        "\n".join([
            " M backend/server.py",
            "M  backend/.env",
            "?? scratch.txt",
        ])
    )

    allowed, blocking = classify_entries(entries)

    assert allowed == []
    assert [entry.path for entry in blocking] == [
        "backend/server.py",
        "backend/.env",
        "scratch.txt",
    ]
