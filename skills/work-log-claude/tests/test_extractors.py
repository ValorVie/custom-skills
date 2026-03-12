# tests/test_extractors.py
from wl_parser.extractors import extract_commits


def test_extract_commits_simple_dash_m():
    """Simple -m "message" style."""
    record = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Bash", "id": "toolu_001", "input": {
                    "command": 'git commit -m "修正(checkout): 處理折扣為零"'
                }}
            ]
        }
    }
    commits = extract_commits(record)
    assert commits == ["修正(checkout): 處理折扣為零"]


def test_extract_commits_heredoc_escaped_newlines():
    """Heredoc style with \\n escape sequences (JSON serialized)."""
    record = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Bash", "id": "toolu_002", "input": {
                    "command": "git commit -m \"$(cat <<'EOF'\\n功能(api): 新增端點\\n\\nCo-Authored-By: Claude\\nEOF\\n)\""
                }}
            ]
        }
    }
    commits = extract_commits(record)
    assert len(commits) == 1
    assert "功能(api): 新增端點" in commits[0]


def test_extract_commits_heredoc_real_newlines():
    """Heredoc style with real newlines."""
    record = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Bash", "id": "toolu_003", "input": {
                    "command": "git commit -m \"$(cat <<'EOF'\n修正(db): 修正查詢\n\nDetails here\nEOF\n)\""
                }}
            ]
        }
    }
    commits = extract_commits(record)
    assert len(commits) == 1
    assert "修正(db): 修正查詢" in commits[0]


def test_extract_commits_no_commit():
    """Bash tool_use but not a git commit."""
    record = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Bash", "id": "toolu_004", "input": {
                    "command": "git status"
                }}
            ]
        }
    }
    commits = extract_commits(record)
    assert commits == []


def test_extract_commits_non_assistant_record():
    """Non-assistant records should return empty list."""
    record = {"type": "user", "message": {"content": "hello"}}
    commits = extract_commits(record)
    assert commits == []


def test_extract_commits_non_bash_tool():
    """tool_use with non-Bash tool should not be checked."""
    record = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Edit", "id": "toolu_005", "input": {
                    "command": "git commit -m 'fake'"
                }}
            ]
        }
    }
    commits = extract_commits(record)
    assert commits == []


def test_extract_commits_multiple_commits():
    """Multiple Bash tool_use with commits."""
    record = {
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Bash", "id": "toolu_006", "input": {
                    "command": 'git commit -m "第一個 commit"'
                }},
                {"type": "tool_use", "name": "Bash", "id": "toolu_007", "input": {
                    "command": 'git commit -m "第二個 commit"'
                }}
            ]
        }
    }
    commits = extract_commits(record)
    assert len(commits) == 2
    assert "第一個 commit" in commits
    assert "第二個 commit" in commits


from wl_parser.extractors import (
    extract_first_prompt,
    extract_files_changed,
    extract_tool_usage,
    extract_tokens,
    detect_session_status,
)

# --- extract_first_prompt ---

def test_extract_first_prompt_string_content():
    records = [
        {"type": "user", "message": {"content": "修正結帳頁面的折扣計算"}},
        {"type": "user", "message": {"content": "再看看其他地方"}},
    ]
    assert extract_first_prompt(records) == "修正結帳頁面的折扣計算"

def test_extract_first_prompt_skips_tool_result():
    records = [
        {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
        {"type": "user", "message": {"content": "真正的 prompt"}},
    ]
    assert extract_first_prompt(records) == "真正的 prompt"

def test_extract_first_prompt_empty():
    assert extract_first_prompt([]) is None

def test_extract_first_prompt_only_tool_results():
    records = [
        {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
    ]
    assert extract_first_prompt(records) is None

# --- extract_files_changed ---

def test_extract_files_changed():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/a/b.py"}},
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/a/c.py"}},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/a/d.py"}},
        ]}},
    ]
    files = extract_files_changed(records)
    assert set(files) == {"/a/b.py", "/a/c.py"}  # Read excluded

def test_extract_files_changed_empty():
    assert extract_files_changed([]) == []

def test_extract_files_changed_no_write_tools():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
        ]}},
    ]
    assert extract_files_changed(records) == []

# --- extract_tool_usage ---

def test_extract_tool_usage():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {}},
            {"type": "tool_use", "name": "Edit", "input": {}},
            {"type": "tool_use", "name": "Bash", "input": {}},
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {}},
        ]}},
    ]
    usage = extract_tool_usage(records)
    assert usage == {"Edit": 2, "Bash": 1, "Read": 1}

def test_extract_tool_usage_empty():
    assert extract_tool_usage([]) == {}

# --- extract_tokens ---

def test_extract_tokens():
    records = [
        {"type": "assistant", "message": {"usage": {
            "input_tokens": 100, "output_tokens": 50,
            "cache_creation_input_tokens": 200, "cache_read_input_tokens": 300,
        }}},
        {"type": "assistant", "message": {"usage": {
            "input_tokens": 150, "output_tokens": 75,
            "cache_creation_input_tokens": 0, "cache_read_input_tokens": 100,
        }}},
    ]
    tokens = extract_tokens(records)
    assert tokens == {"input": 250, "output": 125, "cache_creation": 200, "cache_read": 400}

def test_extract_tokens_missing_usage():
    records = [{"type": "assistant", "message": {}}]
    tokens = extract_tokens(records)
    assert tokens == {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}

def test_extract_tokens_skips_user_records():
    records = [
        {"type": "user", "message": {"usage": {"input_tokens": 9999}}},
        {"type": "assistant", "message": {"usage": {"input_tokens": 10, "output_tokens": 5,
            "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}},
    ]
    tokens = extract_tokens(records)
    assert tokens["input"] == 10  # user record ignored

# --- detect_session_status ---

def test_status_completed_with_commit():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": 'git commit -m "feat: done"'}}
        ]}},
    ]
    assert detect_session_status(records) == "completed"

def test_status_completed_with_keyword():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "已完成所有修改。"}
        ]}},
    ]
    assert detect_session_status(records) == "completed"

def test_status_completed_with_done_english():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "The task is done."}
        ]}},
    ]
    assert detect_session_status(records) == "completed"

def test_status_in_progress():
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "/a.py"}},
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "讓我繼續看下一個檔案。"}
        ]}},
    ]
    assert detect_session_status(records) == "in_progress"

def test_status_empty_records():
    assert detect_session_status([]) == "abandoned"


def test_status_abandoned_empty_records():
    """Empty records → abandoned."""
    assert detect_session_status([], duration_minutes=0) == "abandoned"


def test_status_abandoned_short_no_tools():
    """Short session with no tool_use → abandoned."""
    records = [
        {"type": "user", "message": {"content": "hello"}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Hi there!"}
        ]}},
    ]
    assert detect_session_status(records, duration_minutes=1) == "abandoned"


def test_status_completed_with_many_tools():
    """≥5 tool_use + last record is assistant → completed."""
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {}},
            {"type": "tool_use", "name": "Edit", "input": {}},
            {"type": "tool_use", "name": "Grep", "input": {}},
            {"type": "tool_use", "name": "Bash", "input": {}},
            {"type": "tool_use", "name": "Write", "input": {}},
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Here is my analysis."}
        ]}},
    ]
    assert detect_session_status(records, duration_minutes=30) == "completed"


def test_status_in_progress_few_tools():
    """<5 tool_use → in_progress (not completed by tool count)."""
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {}},
            {"type": "tool_use", "name": "Edit", "input": {}},
        ]}},
        {"type": "user", "message": {"content": "繼續"}},
    ]
    assert detect_session_status(records, duration_minutes=10) == "in_progress"


def test_status_in_progress_duration_over_2min():
    """No tools but duration > 2min → in_progress."""
    records = [
        {"type": "user", "message": {"content": "explain this"}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Let me explain..."}
        ]}},
    ]
    assert detect_session_status(records, duration_minutes=5) == "in_progress"


def test_status_completed_many_tools_last_not_assistant():
    """≥5 tool_use but last record is user → in_progress (not completed)."""
    records = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {}},
            {"type": "tool_use", "name": "Edit", "input": {}},
            {"type": "tool_use", "name": "Grep", "input": {}},
            {"type": "tool_use", "name": "Bash", "input": {}},
            {"type": "tool_use", "name": "Write", "input": {}},
        ]}},
        {"type": "user", "message": {"content": "wait, go back"}},
    ]
    assert detect_session_status(records, duration_minutes=30) == "in_progress"
