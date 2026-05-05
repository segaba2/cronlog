# cronlog

Lightweight wrapper that captures and stores cron job output with structured metadata for easy querying.

## Installation

```bash
pip install cronlog
```

## Usage

Wrap any cron command with `cronlog` to capture its output and metadata automatically.

**In your crontab:**

```
*/5 * * * * cronlog --job backup-db -- /usr/local/bin/backup.sh
```

**Query recent job runs:**

```python
from cronlog import LogStore

store = LogStore()

# Get the last 10 runs for a specific job
runs = store.query(job="backup-db", limit=10)

for run in runs:
    print(run.job, run.exit_code, run.started_at, run.duration)
```

**View logs from the CLI:**

```bash
cronlog list
cronlog show backup-db --last 5
cronlog show backup-db --failed
```

Logs are stored as structured JSON records (default: `~/.cronlog/logs.db`) and include:

- Job name and command
- Start time, end time, and duration
- Exit code
- Captured stdout and stderr

## Configuration

```bash
# Set a custom log directory
export CRONLOG_DIR=/var/log/cronlog
```

## License

MIT