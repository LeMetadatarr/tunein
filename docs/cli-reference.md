# CLI Reference

Entry point: `tunein` → `tunein.cli:main`

`Cli` — `tunein/cli.py:7`

## Commands

### `tunein search <query>`

`Search` — `tunein/subcommands/search.py:36`

Search TuneIn for stations matching `<query>`. Results are sorted by
fuzzy match score then bitrate (both descending).

```
tunein search "Radio Paradise"
tunein search "BBC Radio 4" --format json
```

**Arguments:**

| Argument | Description |
|---|---|
| `station` | Search query string |
| `-f / --format` | Output format: `table` (default) or `json` |

**Table output** columns: `title`, `bit_rate`, `media_type`, `artist`,
`description`. The `title` column is rendered as an OSC-8 hyperlink to the
stream URL (clickable in supported terminals). Column widths adapt to
terminal width; `description` is clipped to fill remaining space.

**JSON output** prints the full `station.dict` list as pretty-printed JSON.

**Exit code 1** when no stations are found.

`Search.run` — `tunein/subcommands/search.py:43`

## Help

```
tunein --help
tunein search --help
```
