# C Drive AI Cleaner Bot

Windows C drive cleanup assistant powered by Ollama.

Default model: `deepseek-v4-flash:cloud`

## Automatic Run

Run this file to start a scan immediately:

```bat
tools\c_drive_ai_cleaner\run_c_drive_ai_cleaner.bat
```

It does not ask questions. It runs scan-only mode, writes reports, and writes logs.

Output folders:

- Reports: `data\cleanup-reports`
- Logs: `data\cleanup-logs`

## Optional Safe Cleanup

This deletes only old files in allowlisted temp/cache folders:

```bat
tools\c_drive_ai_cleaner\run_c_drive_ai_cleaner_clean.bat
```

The bot never auto-deletes Downloads, Desktop, or arbitrary large folders.

## Schedule Daily Auto Scan

To register a Windows scheduled task that scans every day at 09:00:

```bat
tools\c_drive_ai_cleaner\install_c_drive_ai_cleaner_task.bat
```

To remove it:

```bat
tools\c_drive_ai_cleaner\uninstall_c_drive_ai_cleaner_task.bat
```

The scheduled task is scan-only. It does not delete files.

## Direct PowerShell Commands

```powershell
# Scan only
powershell -NoProfile -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1

# Scan with a specific Ollama model
powershell -NoProfile -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1 -Model deepseek-v4-flash:cloud

# Scan without Ollama advice
powershell -NoProfile -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1 -NoAi

# Safe cleanup
powershell -NoProfile -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1 -Clean

# Safe cleanup plus recycle bin and Windows component cleanup
powershell -NoProfile -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1 -Clean -Deep
```

## Notes

- Ollama should be running at `http://localhost:11434`.
- If `-Model` is omitted, the script uses `$env:OLLAMA_MODEL`, then falls back to `deepseek-v4-flash:cloud`.
- Markdown, JSON, and log files are timestamped for each run.
