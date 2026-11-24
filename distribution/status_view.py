"""Compatibility adapter for the shared current-progress projection."""
if __package__:
    from .core import progress
else:
    from core import progress


def summarize(directory, plan, run, evaluation):
    return evaluation.get('progress') or progress.summarize(directory, plan, run, evaluation)


render = progress.render
