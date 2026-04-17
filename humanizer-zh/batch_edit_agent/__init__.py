"""Safe batch text replacement workflow package."""

from .contracts import ChangeRequest, MatchItem, RunReport, ScopeFilter
from .workflow import run_workflow, write_report

__all__ = [
    "ChangeRequest",
    "MatchItem",
    "RunReport",
    "ScopeFilter",
    "run_workflow",
    "write_report",
]

__version__ = "0.1.0"

