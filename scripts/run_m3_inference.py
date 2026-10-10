#!/usr/bin/env python3
"""Synthetic M3 driver; scientific execution uses captured package source."""
from solar_flare_jepa.evaluation.inference_research.runner import main
from pathlib import Path

if __name__=="__main__":
    main(default_root=Path(__file__).resolve().parents[1])
