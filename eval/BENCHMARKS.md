# Benchmark results

No latency or ASR-quality numbers are fabricated in this repository. Run `make eval` after `make setup` to generate the deterministic workflow task-completion report at `eval/results.json`.

For a real benchmark, record the hardware (CPU/GPU, RAM, model quantization, batch/concurrency), run at least 30 representative Arabic turns, and report p50/p95 for STT, first LLM token, tools, TTS, and total response. Add a consented/licensed labeled Arabic set before calculating WER and CER. The `/api/metrics` endpoint is process-local and intended for this local benchmark, not distributed observability.
