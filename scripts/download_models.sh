#!/usr/bin/env bash
set -euo pipefail
mkdir -p models/tts
echo "Pulling the openly licensed Qwen2.5 model into local Ollama storage..."
ollama pull qwen2.5:7b-instruct
echo "Whisper weights download automatically on first local use."
echo "Piper Arabic voice availability and license must be verified before downloading. See LICENSES.md."
