CREATE TABLE IF NOT EXISTS stories (
    story_id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    repository TEXT NOT NULL,
    intent TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    source_url TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL REFERENCES stories(story_id),
    role TEXT NOT NULL,
    model TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    outcome TEXT
);

CREATE TABLE IF NOT EXISTS session_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    summary TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_reviews_session_time
ON session_reviews(session_id, reviewed_at);

CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL REFERENCES stories(story_id),
    session_id TEXT REFERENCES sessions(session_id),
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    tool TEXT,
    category TEXT,
    success INTEGER NOT NULL CHECK (success IN (0, 1)),
    duration_ms INTEGER CHECK (duration_ms IS NULL OR duration_ms >= 0),
    error_code TEXT,
    failure_message TEXT,
    resolution TEXT,
    importance TEXT NOT NULL DEFAULT 'normal'
        CHECK (importance IN ('trivial', 'normal', 'important', 'decision')),
    meaningful_progress INTEGER
        CHECK (meaningful_progress IS NULL OR meaningful_progress IN (0, 1)),
    details_json TEXT,
    archived_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_story_time
    ON events(story_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_session_time
    ON events(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_failures
    ON events(story_id, success, event_type);

CREATE TRIGGER IF NOT EXISTS trg_events_session_story_insert
BEFORE INSERT ON events
WHEN NEW.session_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1 FROM sessions
      WHERE session_id = NEW.session_id
        AND story_id = NEW.story_id
 )
BEGIN
    SELECT RAISE(ABORT, 'event session does not belong to story');
END;

CREATE TRIGGER IF NOT EXISTS trg_events_session_story_update
BEFORE UPDATE OF story_id, session_id ON events
WHEN NEW.session_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1 FROM sessions
      WHERE session_id = NEW.session_id
        AND story_id = NEW.story_id
 )
BEGIN
    SELECT RAISE(ABORT, 'event session does not belong to story');
END;

CREATE TABLE IF NOT EXISTS decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL REFERENCES stories(story_id),
    session_id TEXT REFERENCES sessions(session_id),
    summary TEXT NOT NULL,
    rationale TEXT,
    created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS trg_decisions_session_story_insert
BEFORE INSERT ON decisions
WHEN NEW.session_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1 FROM sessions
      WHERE session_id = NEW.session_id
        AND story_id = NEW.story_id
 )
BEGIN
    SELECT RAISE(ABORT, 'decision session does not belong to story');
END;

CREATE TRIGGER IF NOT EXISTS trg_decisions_session_story_update
BEFORE UPDATE OF story_id, session_id ON decisions
WHEN NEW.session_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1 FROM sessions
      WHERE session_id = NEW.session_id
        AND story_id = NEW.story_id
 )
BEGIN
    SELECT RAISE(ABORT, 'decision session does not belong to story');
END;

CREATE TABLE IF NOT EXISTS resolutions (
    resolution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    failure_event_id INTEGER NOT NULL REFERENCES events(event_id),
    session_id TEXT REFERENCES sessions(session_id),
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_resolutions_failure
    ON resolutions(failure_event_id, created_at);

CREATE TRIGGER IF NOT EXISTS trg_resolutions_session_story_insert
BEFORE INSERT ON resolutions
WHEN NEW.session_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1
       FROM sessions s
       JOIN events e ON e.event_id = NEW.failure_event_id
      WHERE s.session_id = NEW.session_id
        AND s.story_id = e.story_id
 )
BEGIN
    SELECT RAISE(ABORT, 'resolution session does not belong to failure story');
END;

CREATE TRIGGER IF NOT EXISTS trg_resolutions_session_story_update
BEFORE UPDATE OF failure_event_id, session_id ON resolutions
WHEN NEW.session_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1
       FROM sessions s
       JOIN events e ON e.event_id = NEW.failure_event_id
      WHERE s.session_id = NEW.session_id
        AND s.story_id = e.story_id
 )
BEGIN
    SELECT RAISE(ABORT, 'resolution session does not belong to failure story');
END;

CREATE TABLE IF NOT EXISTS customization_versions (
    customization_id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,
    version TEXT NOT NULL,
    source_path TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    model TEXT,
    recorded_at TEXT NOT NULL,
    metadata_json TEXT,
    UNIQUE(component, version, content_sha256)
);

CREATE TABLE IF NOT EXISTS event_summaries (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL REFERENCES stories(story_id),
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    tool TEXT,
    category TEXT,
    event_count INTEGER NOT NULL,
    total_duration_ms INTEGER NOT NULL,
    first_timestamp TEXT,
    last_timestamp TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(story_id, event_date, event_type, tool, category)
);

CREATE TABLE IF NOT EXISTS scorecards (
    scorecard_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL REFERENCES stories(story_id),
    generated_at TEXT NOT NULL,
    outcome TEXT NOT NULL,
    runtime_verified INTEGER NOT NULL CHECK (runtime_verified IN (0, 1)),
    metrics_json TEXT NOT NULL,
    report_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_usage (
    workspace_path TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    last_used_at TEXT NOT NULL,
    use_count INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS gates (
    gate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL REFERENCES stories(story_id),
    session_id TEXT REFERENCES sessions(session_id),
    gate TEXT NOT NULL
        CHECK (gate IN ('analysis', 'implementation', 'review', 'customization', 'docs')),
    status TEXT NOT NULL
        CHECK (status IN ('passed', 'failed', 'waived')),
    artifact_path TEXT,
    artifact_sha256 TEXT,
    evidence TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    details_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_gates_story_gate
    ON gates(story_id, gate, recorded_at);

CREATE TRIGGER IF NOT EXISTS trg_gates_session_story_insert
BEFORE INSERT ON gates
WHEN NEW.session_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1 FROM sessions s
      WHERE s.session_id = NEW.session_id
        AND s.story_id = NEW.story_id
 )
BEGIN
    SELECT RAISE(ABORT, 'gate session does not belong to story');
END;
