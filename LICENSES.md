# Dependencies and model licenses

This repository is MIT licensed (see `LICENSE`). Dependency license compliance remains the deployer's responsibility.

| Component | Intended local use | License / verification status |
|---|---|---|
| Qwen2.5 Instruct weights | Ollama `qwen2.5:7b-instruct` | Apache-2.0, according to the Qwen repository/model card; retain its notice. |
| faster-whisper | ASR runtime | MIT. Whisper model weights have their own model-card terms; verify the exact downloaded model before redistribution. |
| Silero VAD | VAD option | MIT source; verify the pinned release/model artifact before shipping. |
| Piper runtime | TTS adapter | MIT runtime. **Voice weights are licensed separately.** |

## Arabic Piper voice decision

This project does not bundle an Arabic Piper voice because availability and the exact license of a high-quality Arabic voice can change. `PIPER_VOICE_PATH` accepts only a voice whose model card explicitly permits your intended distribution/use. Before use, archive the model card and license in `models/tts/` and record version/checksum. If no suitable Arabic Piper weight is available, leave TTS disabled: the UI still shows Arabic text. A future openly licensed adapter may be added only with pinned, documented voice-weight provenance. This avoids making an unsupported license claim.
