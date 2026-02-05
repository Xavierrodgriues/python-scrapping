Command to run cron scheduler:
$env:PYTHONPATH='.'; .venv\Scripts\python cron_scheduler.py

Command to run all scrapper manually:
$env:PYTHONPATH='.'; .venv\Scripts\python -m src.main

Command to run specific scrapper manually:
$env:PYTHONPATH='.'; .venv\Scripts\python -m src.main --scrapers SkipTheDriveScraper

