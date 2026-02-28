#!/bin/bash
# Initialize the instinct-learning environment
# Creates necessary directories and default configuration

set -e

# Plugin-specific data directory (can override with INSTINCT_LEARNING_DATA_DIR)
DATA_DIR="${INSTINCT_LEARNING_DATA_DIR:-$HOME/.claude/instinct-learning}"

echo "Initializing instinct-learning environment..."
echo "Data directory: $DATA_DIR"

# Create directory structure
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/instincts/personal"
mkdir -p "$DATA_DIR/instincts/shared"
mkdir -p "$DATA_DIR/evolved/skills"
mkdir -p "$DATA_DIR/evolved/commands"
mkdir -p "$DATA_DIR/evolved/agents"
mkdir -p "$DATA_DIR/observations.archive"

# Create default configuration if not exists
CONFIG_FILE="$DATA_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
{
  "version": "1.0",
  "observation": {
    "enabled": true,
    "capture_tools": ["Edit", "Write", "Bash", "Read", "Grep", "Glob"],
    "ignore_tools": ["TodoWrite", "TaskCreate", "TaskUpdate", "TaskList", "AskUserQuestion"],
    "max_prompt_length": 500,
    "max_response_length": 1000,
    "max_file_size_mb": 10,
    "archive_after_days": 7
  },
  "instincts": {
    "min_confidence": 0.3,
    "auto_approve_threshold": 0.7,
    "confidence_decay_rate": 0.02,
    "max_instincts_per_domain": 20
  },
  "observer": {
    "enabled": true,
    "model": "haiku",
    "run_interval_minutes": 5,
    "patterns_to_detect": ["repeated_sequences", "error_fix", "user_preferences", "domain_patterns"]
  },
  "evolution": {
    "cluster_threshold": 3,
    "min_avg_confidence": 0.7
  },
  "session": {
    "track_sessions": true,
    "memory_enabled": true
  }
}
EOF
    echo "Created default configuration: $CONFIG_FILE"
else
    echo "Configuration already exists: $CONFIG_FILE"
fi

# Create empty observations file if not exists
OBS_FILE="$DATA_DIR/observations.jsonl"
if [ ! -f "$OBS_FILE" ]; then
    touch "$OBS_FILE"
    echo "Created observations file: $OBS_FILE"
fi

# Create session file if not exists
SESSION_FILE="$DATA_DIR/session.json"
if [ ! -f "$SESSION_FILE" ]; then
    echo '{"count": 0, "last_session": null}' > "$SESSION_FILE"
    echo "Created session file: $SESSION_FILE"
fi

echo ""
echo "✓ Environment initialized successfully!"
echo ""
echo "Directory structure:"
echo "  $DATA_DIR/"
echo "  ├── config.json         # Plugin configuration"
echo "  ├── observations.jsonl  # Session observations"
echo "  ├── session.json        # Session tracking"
echo "  ├── instincts/"
echo "  │   ├── personal/       # Auto-learned instincts"
echo "  │   └── shared/         # Imported instincts"
echo "  ├── evolved/"
echo "  │   ├── skills/         # Evolved skills"
echo "  │   ├── commands/       # Evolved commands"
echo "  │   └── agents/         # Evolved agents"
echo "  └── observations.archive/  # Archived observations"
echo ""
echo "Next steps:"
echo "  1. Use /instinct:status to check current instincts"
echo "  2. Work normally - hooks will capture observations"
echo "  3. Use /instinct:evolve to cluster instincts into capabilities"
