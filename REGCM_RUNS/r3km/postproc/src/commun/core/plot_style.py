import matplotlib.pyplot as plt
import matplotlib as mpl

def apply_publication_style():
    """
    Applies standard publication-quality Q1 matplotlib configurations.
    """
    # Typography
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']
    plt.rcParams['font.size'] = 10
    
    # Titles and Labels
    plt.rcParams['axes.titlesize'] = 11
    plt.rcParams['axes.labelsize'] = 9
    plt.rcParams['xtick.labelsize'] = 8
    plt.rcParams['ytick.labelsize'] = 8
    plt.rcParams['legend.fontsize'] = 9
    plt.rcParams['legend.title_fontsize'] = 10
    plt.rcParams['figure.titlesize'] = 12
    
    # Lines and markers
    plt.rcParams['lines.linewidth'] = 1.5
    plt.rcParams['lines.markersize'] = 4
    
    # Axes and Grid
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['grid.linewidth'] = 0.5
    plt.rcParams['grid.alpha'] = 0.5
    plt.rcParams['grid.color'] = '#b0b0b0'
    plt.rcParams['grid.linestyle'] = '--'
    
    # Savefig
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.rcParams['savefig.pad_inches'] = 0.1

def get_variable_units(var_name):
    """
    Returns the exact mathematical unit string for visualization.
    """
    if var_name == 'pr':
        return 'mm day$^{-1}$'
    elif var_name in ['tasmax', 'tasmin', 'tas']:
        return '°C'
    return ''

PLOT_LEVELS = {
    "pr": [0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0],
    "pr_bias": [-4.0, -3.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0, 4.0],
    "tasmin": [-5, 0, 5, 10, 15, 20, 25, 30, 35],
    "tasmax": [5, 10, 15, 20, 25, 30, 35, 40, 45],
    "tas_bias": [-8, -6, -4, -2, -1, 0, 1, 2, 4, 6, 8]
}

def get_norm_and_cmap_for_var(var_name, is_bias=False):
    """
    Returns (cmap, norm, extend) configured with discrete BoundaryNorm classes.
    """
    if var_name == 'pr':
        if is_bias:
            levels = PLOT_LEVELS["pr_bias"]
            cmap = plt.get_cmap("BrBG").copy()
            extend = "both"
        else:
            levels = PLOT_LEVELS["pr"]
            cmap = plt.get_cmap("YlGnBu").copy()
            extend = "max"
            
    elif var_name in ['tasmax', 'tasmin', 'tas']:
        if is_bias:
            levels = PLOT_LEVELS["tas_bias"]
            cmap = plt.get_cmap("RdBu_r").copy()
            extend = "both"
        else:
            levels = PLOT_LEVELS[var_name] if var_name in PLOT_LEVELS else PLOT_LEVELS["tasmax"]
            cmap = plt.get_cmap("RdYlBu_r").copy()
            extend = "both"
    else:
        levels = [-1, 0, 1]
        cmap = plt.get_cmap("viridis").copy()
        extend = "both"

    cmap.set_bad(get_nan_color())
    norm = mpl.colors.BoundaryNorm(levels, ncolors=cmap.N)
    
    return cmap, norm, extend, levels

def get_cmap_for_var(var_name, is_bias=False):
    """
    Legacy method - use get_norm_and_cmap_for_var instead.
    """

def get_nan_color():
    """Returns the standard color for missing observational coverage."""
    return '#E0E0E0'
