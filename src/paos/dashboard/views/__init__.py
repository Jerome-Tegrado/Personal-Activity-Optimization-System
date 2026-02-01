from __future__ import annotations

from typing import Callable, Dict

import streamlit as st

from .benchmarks import render_benchmarks
from .experiments import render_experiments
from .explore import render_explore
from .ml import render_machine_learning
from .overview import render_overview
from .pipeline import render_pipeline
from .reports import render_reports
from .settings import render_settings

ViewFn = Callable[..., None]

VIEWS: Dict[str, ViewFn] = {
    "Overview": render_overview,
    "Explore": render_explore,
    "Pipeline": render_pipeline,
    "Reports": render_reports,
    "Benchmarks": render_benchmarks,
    "Experiments": render_experiments,
    "Machine Learning": render_machine_learning,
    "Settings": render_settings,
}


def render_unknown_view(name: str) -> None:
    st.warning(f"Unknown view: {name}")
