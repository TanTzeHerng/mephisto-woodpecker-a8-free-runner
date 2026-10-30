# Woodpecker A8 spoiler-free off-PC experiment

The historical Mephisto I ROM and emulator core are **not in this public repository**. GitHub Actions obtains them using encrypted repository secrets. The workflow uses standard GitHub-hosted Linux runners, not the user's PC. It posts only solved/failed/technical aggregates and per-exercise status, not engine moves or puzzle answers.

The 29 October baseline is a historical aggregate without every original per-exercise result available. New individual results are kept in `results.json`. The original ROM controls the end of each search; the runner imposes no chess-search stopping rule. Hosting infrastructure can interrupt a job before a result exists, and these searches must be retried. The workflow has no automatic schedule while validation is in progress.
