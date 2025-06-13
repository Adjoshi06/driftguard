"""
Documentation Drift Detector package.

This package exposes the high-level `run` function and CLI entrypoint
for analyzing code changes against documentation updates.
"""

from .drift_analysis import DriftDetector, DriftDetectorConfig
from .cli import run_cli

__all__ = ["DriftDetector", "DriftDetectorConfig", "run_cli"]

