#Attention: AI was involved!
# Anthropic Manifold Pipe (Improved)

Improved version of the [Anthropic Manifold Pipe](https://openwebui.com/f/justinrahb/anthropic) for [Open WebUI](https://github.com/open-webui/open-webui).

## What is this?

A Manifold Pipe for Open WebUI that connects to Anthropic's Claude API. Enables using Claude models directly within Open WebUI.

## Improvements over Original (v0.2.5 → v0.4.0)

### Bug Fixes
- **Stream Response**: Fixed `content_block_start` KeyError (field doesn't contain `text`)
- **Model Name Extraction**: More robust handling of various formats
- **Image URL Handling**: Added timeout and better error handling
- **API Compatibility**: Removed `top_p` and `top_k` (incompatible with `temperature`)

### Features
- **Configurable Valves**: API version, timeouts, defaults configurable via UI
- **Logging**: Proper `logger` instead of `print()` for better debugging
- **Validation**: API key check, detailed error messages
- **Type Hints**: Fully typed for better IDE support

### Optimizations
- Removed unnecessary `time.sleep(0.01)`
- Payload only includes set parameters
- Timeout-specific error handling

### Updated Models
- `claude-sonnet-4-5-20250929` (latest Sonnet)
- `claude-haiku-4-5-20251001` (latest Haiku)
- `claude-opus-4-5-20251101` (latest Opus)

## Installation

1. In Open WebUI: **Workspace** → **Functions** → **+** (New Function)
2. Copy and paste code from `anthropic_pipe.py`
3. Click **Save**
4. In **Valves**, enter your `ANTHROPIC_API_KEY`

Alternative via environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Configuration (Valves)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ANTHROPIC_API_KEY` | - | Anthropic API Key (required) |
| `ANTHROPIC_API_VERSION` | `2023-06-01` | API version header |
| `MAX_TOKENS` | `4096` | Default max tokens |
| `TEMPERATURE` | `1.0` | Default temperature (0.0-1.0) |
| `REQUEST_TIMEOUT` | `60` | Request timeout (seconds) |
| `CONNECTION_TIMEOUT` | `3.05` | Connection timeout (seconds) |

## Supported Models

- **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`) - Recommended for most tasks
- **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`) - Fast and cost-effective
- **Claude Opus 4.5** (`claude-opus-4-5-20251101`) - Highest performance for complex tasks

## Features

- ✅ Streaming and non-streaming responses
- ✅ Image support (base64 and URL)
- ✅ Image size validation (5MB per image, 100MB total)
- ✅ System message support
- ✅ Stop sequences
- ✅ Configurable timeouts
- ✅ Detailed error handling

## Requirements

- Open WebUI v0.3.17 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Usage Example

After installation, select a model in Open WebUI:
- `anthropic/claude-sonnet-4.5`
- `anthropic/claude-haiku-4.5`
- `anthropic/claude-opus-4.5`

## Troubleshooting

**Error: ANTHROPIC_API_KEY not configured**
- Set the API key in Valves or as environment variable

**HTTP 400: temperature and top_p cannot both be specified**
- This version fixes this issue by removing conflicting parameters

**Request timeout**
- Increase `REQUEST_TIMEOUT` in Valves for longer responses

## Credits

- **Original Authors**: [justinh-rahb](https://github.com/justinh-rahb) and christian-taillon
- **Original Source**: [OpenWebUI Community](https://openwebui.com/f/justinrahb/anthropic)
- **Improvements**: Based on v0.2.5, updated and improved

## License

MIT License

## Changelog

### v0.4.0 (2025-12-10)
- Fixed streaming response KeyError
- Added configurable valves
- Improved error handling and logging
- Updated to latest Claude models
- Removed incompatible parameters

### v0.3.0
- Removed Google tracking
- Initial model updates

### v0.2.5 (Original)
- Base implementation by justinh-rahb
