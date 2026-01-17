"""Plotting module for SSZ visualization."""
from .paper_plots import (
    plot_time_dilation_comparison,
    plot_xi_regimes,
    plot_power_law,
    plot_validation_summary,
    generate_all_paper_plots
)
from .theory_plots import (
    plot_xi_and_dilation,
    plot_gr_vs_ssz_comparison,
    plot_universal_intersection,
    plot_power_law as plot_power_law_interactive,
    plot_regime_zones,
    plot_experimental_validation,
    plot_neutron_star_predictions,
    get_all_theory_plots,
    PLOT_DESCRIPTIONS
)
