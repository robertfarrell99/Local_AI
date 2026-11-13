# Local_AI

Spike: Open WebUI as an in-house assistant front end, in front of local open models (Ollama) and Claude for comparison. The plan and findings table are in [docs/spike-plan.md](docs/spike-plan.md).

## Phase 1 setup (one Mac)

1. **Docker Desktop** running. Set its memory limit to about 4 GB (Settings → Resources) so the model keeps the rest.
2. **Ollama** installed as the native Mac app from ollama.com (not in Docker, so it can use the GPU).
3. Start Open WebUI:

   ```bash
   docker compose up -d
   ```

   Then open http://localhost:3000. There is no login screen in Phase 1.

4. Pull the models, one at a time:

   ```bash
   ollama pull qwen3.8:27b
   ```

   ```bash
   ollama pull mistral-small:24b
   ```

5. In Open WebUI, raise each model's context length to about 32K (Admin Panel → Settings → Models → the model → Advanced Params → `num_ctx` = 32768). Ollama's default silently drops the start of a long transcript.
6. Add Claude: Admin Panel → Settings → Connections → OpenAI → add a connection with URL `https://api.anthropic.com/v1` (no trailing slash) and an Anthropic API key. If that does not list models, use an Anthropic pipe function instead.

## Folders

- `docs/` — spike plan and findings.
- `transcripts/` — test transcripts. Ignored by Git; nothing real or sensitive goes here in Phase 1.
- `tools/` — custom Open WebUI tools (Word and Excel export), added in step 6.
