# Oh My Claude Code

A collection of Claude Code plugins for enhanced productivity and workflow automation.

## Marketplace

This is a plugin marketplace containing multiple plugins:

| Plugin | Description | Version |
|--------|-------------|---------|
| [instinct-learning](./plugins/instinct-learning/) | Observes sessions, learns patterns, evolves behaviors into skills/commands/agents | 1.0.0 |

## Installation

### Install from Marketplace

```bash
# Install a specific plugin
claude plugin install oh-my-claude-code/instinct-learning
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/zhengyuli/oh-my-claude-code.git

# Copy a plugin to your Claude plugins directory
cp -r oh-my-claude-code/plugins/<plugin-name> ~/.claude/plugins/<plugin-name>
```

## Development

### Project Structure

```
oh-my-claude-code/
├── .claude-plugin/
│   └── marketplace.json    # Marketplace manifest
├── plugins/
│   ├── instinct-learning/  # Plugin: Instinct-based learning
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json # Plugin manifest
│   │   ├── agents/         # Agent definitions
│   │   ├── commands/       # User commands
│   │   ├── skills/         # Auto-triggered skills
│   │   ├── hooks/          # Hook scripts
│   │   ├── lib/            # Python libraries
│   │   ├── scripts/        # CLI tools
│   │   └── tests/          # Test suites
│   └── <other-plugins>/    # Additional plugins
└── README.md
```

### Adding a New Plugin

1. Create a new directory under `plugins/<plugin-name>/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add plugin content (agents, commands, skills, hooks, etc.)
4. Update `marketplace.json` to include the new plugin
5. Add a `README.md` in the plugin directory

### Plugin Manifest Format

Each plugin has a `.claude-plugin/plugin.json`:

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": "author-name",
  "license": "MIT",
  "commands": [
    {"name": "command:name", "source": "commands/file.md"}
  ],
  "skills": [
    {"name": "skill-name", "source": "skills/file.md"}
  ],
  "agents": [
    {"name": "agent-name", "source": "agents/file.md"}
  ],
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## License

MIT License - see LICENSE file for details.
