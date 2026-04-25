# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

```bash
# Desktop GUI (primary entry point)
python dashboard_app.py
# or double-click START_DASHBOARD.bat

# CLI – single video
python main.py --topic "Napoleon Bonaparte" --dry-run
python main.py --channel kanal_hauptkanal --dry-run

# CLI – batch production
python scheduler.py --batch "Story A" "Story B" --dry-run

# List channels
python main.py --list-channels
```

There are no tests. `--dry-run` skips the YouTube upload and is the safe way to test the pipeline end-to-end.

## Architecture

**Pipeline pattern** — `main.py:run_pipeline()` is the single orchestrator. It calls each module in sequence and writes results to `output/{timestamp}/result.json`. Every module receives the full `settings` dict.

```
main.py:run_pipeline()
  → researcher.py:Researcher.find_trending_topic()
  → scriptwriter.py:ScriptWriter.create_script()
  → compliance.py:ComplianceChecker.check() / fix_script()
  → voiceover.py:Voiceover.create()          # dispatches to fish/openai/free
  → thumbnail.py:ThumbnailGenerator.create()
  → video_creator.py:VideoCreator.create()
  → uploader.py:YouTubeUploader.upload()
  → scheduler.py:VideoScheduler.add_to_history()
```

**Multi-channel**: `channel_manager.py:ChannelManager.build_settings_for_channel(folder_id)` merges `config/settings.json` with `channels/{id}/channel_config.json`. Pass the merged settings dict to `run_pipeline()`.

**Settings loading**: Always use `main.load_settings()` — it calls `load_dotenv()` and injects `OPENAI_API_KEY` / `FISH_AUDIO_API_KEY` from `.env` into `settings["api_keys"]`. Raw `json.load(settings.json)` will return empty key strings.

**Compliance rules** are in `config/legal_rules.json` (tracked in git). The `scriptwriter.py` pulls rules into the GPT prompt via `compliance.py:ComplianceChecker.get_rules_for_prompt()`. The compliance check runs after script generation and can auto-fix issues.

**Story Planer** (`planner.py:StoryPlanner`) is a higher-level workflow on top of `run_pipeline()`. It persists plans to `config/story_plan.json`.

**Dashboard** (`dashboard_app.py`, ~2900 lines) is a CustomTkinter app. All long-running operations run in `threading.Thread(daemon=True)`. UI updates from threads must go through `self.after(0, lambda: ...)`. Pages are built once in `_build_page_*()` and populated lazily in `_render_*()` when the tab is activated via `_switch_page()`.

## Key Invariants

- `config/settings.json` is gitignored — never commit it. Template is `.env.example`.
- `config/legal_rules.json` is the user-editable compliance config — changes apply on next run without code changes.
- History IDs are `uuid4` strings (not integers). Old entries in `video_history.json` may still have integer IDs.
- `scheduler.py:VideoScheduler` loads history at `__init__`. After calling `run_pipeline()` externally, reload with `self.history = self._load_history()` before reading `self.history[-1]`.
- The `active_disclaimers` list in `legal_rules.json` controls which disclaimer checks run. Keys must match the disclaimer handler names in `compliance.py:_check_disclaimers()`.
