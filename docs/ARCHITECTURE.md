# Architecture

## Overview
This bot is composed of:
- Telegram interface layer
- Strategy layer
- Execution / trade layer
- Backtest engine
- Data layer (price download, cache)

## Folder responsibilities
- `main.py`: bootstraps config, starts components
- `config/`: env, settings, secrets templates
- `telegram/`: commands, handlers
- `strategies/`: each file = one strategy
- `backtests/`: runs backtest single/multi, metrics
- `data/`: downloaders + cache
- `tests/`: regression & unit tests
- `reports/`: AI-generated reports (dated)
- `artifacts/`: zip exports, logs, results

## Strategy contract
Each strategy must expose:
- `name`
- `generate_signals(df) -> df/signals`
- `params_schema`
- Must not print emojis in core loops (see BUG_LOG constraints)
