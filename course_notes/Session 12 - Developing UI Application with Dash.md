### Introduce Dash including 4 screenshots of the app (10 mins)

### Explain Dash Application Directory Structure

### Create Directory (5 mins)
- src/app_ui
  - assets
  - components
  - pages
  - __init__.py
  - app.py
  - utils.py
- Insert `__init__.py` to each directory under `app_ui`
- Under the `conf/base`, create `config_ui.yml`

### Add to uv
```bash
uv add dash
uv add dash-bootstrap-components
```

### Under assets, add `custom.css`
```css
/*
 * Custom CSS for Dash app
 * Modern dark sidebar with light content theme
 */

/* Body styling - App background */
body {
    background-color: #F4F7FE;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    color: #4B5563;
}

/* Page content area */
#page-content {
    background-color: #F4F7FE;
    min-height: 100vh;
}

/* Card styling - White cards with rounded corners */
.dbc-container .dbc-row .dbc-col > div,
.dbc-container > div {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E3E8EF;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.10);
}

/* Headings - Better contrast */
h1, h2, h3, h4, h5, h6 {
    color: #1B1D23;
    font-weight: 600;
    line-height: 1.3;
}

h1 {
    color: #1B1D23;
    font-weight: 700;
}

h2 {
    color: #1B1D23;
    font-weight: 600;
}

h3, h4, h5, h6 {
    color: #1B1D23;
    font-weight: 600;
}

/* Input styling */
input[type="number"],
input[type="text"],
select {
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 8px 12px;
    transition: all 0.2s ease;
}

input[type="number"]:focus,
input[type="text"]:focus,
select:focus {
    border-color: #2563eb;
    outline: none;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Buttons - Match sidebar active color style */
.btn-primary,
.dbc-button[color="primary"] {
    background-color: #2563eb;
    border-color: #2563eb;
    border-width: 2px;
    border-radius: 8px;
    font-weight: 600;
    color: #ffffff;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
}

.btn-primary:hover,
.dbc-button[color="primary"]:hover {
    background-color: #1e40af;
    border-color: #1e40af;
    color: #ffffff;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(37, 99, 235, 0.4);
}

.btn-primary:active,
.dbc-button[color="primary"]:active {
    background-color: #1e3a8a;
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(30, 64, 175, 0.3);
}

/* Secondary buttons */
.btn-secondary,
.dbc-button[color="secondary"] {
    background-color: #6b7280;
    border-color: #6b7280;
    border-width: 2px;
    border-radius: 8px;
    font-weight: 600;
    color: #ffffff;
    transition: all 0.2s ease;
}

.btn-secondary:hover,
.dbc-button[color="secondary"]:hover {
    background-color: #4b5563;
    border-color: #4b5563;
    color: #ffffff;
}

/* Success buttons */
.btn-success,
.dbc-button[color="success"] {
    background-color: #16A34A;
    border-color: #16A34A;
    border-width: 2px;
    border-radius: 8px;
    font-weight: 600;
    color: #ffffff;
    transition: all 0.2s ease;
}

.btn-success:hover,
.dbc-button[color="success"]:hover {
    background-color: #15803d;
    border-color: #15803d;
    color: #ffffff;
}

/* Links */
a {
    color: #2563eb;
    text-decoration: none;
    transition: color 0.2s ease;
}

a:hover {
    color: #3b82f6;
    text-decoration: underline;
}

/* Dropdown */
.Select-control,
.Select-menu-outer {
    border-radius: 8px;
    border-color: #d1d5db;
}

/* Graph containers */
.dcc-graph {
    background-color: #FFFFFF;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #E3E8EF;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.10);
}

/* Text colors - Better visibility */
p, li, span {
    color: #4B5563;
    line-height: 1.6;
}

/* Labels - Better contrast */
label {
    color: #1B1D23;
    font-weight: 500;
    margin-bottom: 0.5rem;
}

/* Strong text */
strong, b {
    color: #1B1D23;
    font-weight: 600;
}

/* Muted text */
.muted, small {
    color: #6B7280;
}

/* Dividers */
hr {
    border-color: #E3E8EF;
    margin: 1.5rem 0;
}

/* ------------------------------------------
   Model Tracking page (/model-tracking)
   ------------------------------------------ */
.mt-page-container {
    padding-top: 0;
    height: 100vh;
    overflow-y: auto;
}

.mt-card {
    background-color: #fff;
    border-radius: 12px;
    padding: 30px;
    border: 1px solid #e0e0e0;
    margin-bottom: 20px;
}

.mt-section-title {
    color: #222;
    margin-bottom: 16px;
}

.mt-intro {
    color: #444;
    font-size: 14px;
    line-height: 1.6;
    margin-bottom: 20px;
}

.mt-btn-full {
    width: 100%;
}

.mt-btn-mint {
    background-color: #0d9668 !important;
    border-color: #0a7550 !important;
    color: #fff !important;
}

.mt-btn-mint:hover {
    background-color: #0b7d57 !important;
    border-color: #086044 !important;
    color: #fff !important;
}

.mt-card-title {
    margin-bottom: 20px;
    color: #222;
}

.mt-loading,
.mt-empty {
    color: #666;
    font-size: 14px;
}

.mt-label {
    color: #666;
    font-size: 12px;
    margin-bottom: 4px;
}

.mt-value {
    color: #222;
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 0;
}

.mt-metric {
    color: #222;
    font-size: 14px;
    margin-bottom: 4px;
}

.mt-metric-last {
    color: #222;
    font-size: 14px;
    margin-bottom: 0;
}

.mt-metrics-wrap {
    margin-bottom: 0;
}

/* Status light (green / red) under Refresh button */
.mt-btn-with-status {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
}

.mt-status-under-btn {
    margin-top: 0.25rem;
}

.mt-status-wrap {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.mt-status-inner {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.mt-status-light {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
}

.mt-status-light--green {
    background-color: #16A34A;
    box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.3);
}

/* Red: champion or challenger is missing in the registry */
.mt-status-light--red {
    background-color: #dc2626;
    box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.3);
}

.mt-status-text {
    color: #444;
    font-size: 14px;
}

/* ML Pipelines page (mp- prefix) */
.mp-page-container {
    padding-top: 0;
    height: 100vh;
}

.mp-panel {
    background-color: #fff;
    border-radius: 12px;
    padding: 15px;
    border: 1px solid #e0e0e0;
}

.mp-panel-title {
    color: #222;
    margin-bottom: 12px;
}

.mp-section-title {
    color: #222;
    margin-bottom: 8px;
    margin-top: 16px;
    font-size: 15px;
}

.mp-section-list {
    color: #444;
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 12px;
}

.mp-viz-container {
    background-color: #fff;
    border-radius: 12px;
    padding: 12px;
    border: 1px solid #e0e0e0;
    height: calc(100vh - 60px);
    display: flex;
    flex-direction: column;
}

.mp-viz-title {
    margin-bottom: 12px;
    color: #222;
}

.mp-viz-iframe {
    width: 100%;
    height: calc(100vh - 80px);
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    display: block;
    flex: 1;
}

/* Architecture page (arch- prefix) */
.arch-row > div {
    padding-top: 16px;
}

.arch-page-title {
    color: #222;
}

.arch-panel {
    background-color: #fff;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #e0e0e0;
    margin-bottom: 20px;
}

.arch-panel-title {
    color: #222;
    margin-bottom: 16px;
}

.arch-intro {
    color: #444;
    font-size: 14px;
    line-height: 1.6;
}

.arch-section-title {
    color: #222;
    margin-top: 20px;
}

.arch-list {
    color: #444;
    font-size: 13px;
    line-height: 1.6;
}

.arch-diagram-container {
    background-color: #fff;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #e0e0e0;
}

.arch-diagram-title {
    margin-bottom: 20px;
    color: #222;
}

.arch-diagram-img {
    width: 100%;
    height: auto;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
}
```

### Under assets, add `responsive-sidebar.css`
```css
:root {
  /* ------------------------------
   * Global CSS variables (design tokens)
   * These are reused across the entire UI so that:
   * - colors and spacing are consistent
   * - theme can be tweaked from one place
   * ------------------------------ */

  /* Sidebar background and borders (dark navy theme) */
  --sidebar_bg: #020617;
  --divider: rgba(255, 255, 255, 0.1);
  
  /* Text colors for navigation links (sidebar items) */
  --passive_text: #9CA3AF;
  --active_text: #F9FAFB;
  
  /* Icon colors for sidebar items */
  --passive_icon: #6B7280;
  --active_icon: #F9FAFB;
  
  /* Background colors for hover / active states */
  --hover_bg: rgba(148, 163, 184, 0.18);
  --active_bg: linear-gradient(135deg, #1e3a8a, #2563eb);
  --active_border: transparent;
  
  /* Misc colors (logo, success states, content background) */
  --logo: #FFFFFF;
  --success: #16A34A;
  --background_active: #F4F7FE;
  
  /* Primary sidebar toggle button colors */
  --toggle_color: #FFFFFF;
  --toggle_bg: rgba(255, 255, 255, 0.1);
  --toggle_border: rgba(255, 255, 255, 0.2);
  --toggle_bg_hover: rgba(255, 255, 255, 0.2);
  --toggle_border_hover: rgba(255, 255, 255, 0.3);
  --navbar_toggle_color: rgba(0,0,0,.5);
  --navbar_toggle_border: rgba(0,0,0,.1);
  
  /* Toggle Icon Color */
  --toggle_icon_color: #FFFFFF;
  
  /* Text + icon colors when hovering over a sidebar link */
  --hover_text: #F9FAFB;
  --hover_icon: #F9FAFB;
}

/* Root layout container used by Dash layout */
#main-layout {
  background-color: var(--background_active);
  height: 100vh; /* Fill the full viewport height */
}

/* ------------------------------
 * Sidebar base styles (mobile + desktop)
 * ------------------------------ */
#sidebar {
  text-align: center;
  padding: 1.5rem 0.8rem;
  background-color: var(--sidebar_bg) !important;
  border-right: 1px solid var(--divider);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

#sidebar h2 {
  text-align: center;
  margin-bottom: 0;
}

/* On small screens we hide the descriptive text block (blurb)
 * to:
 * - reduce vertical scrolling
 * - keep focus on navigation and plots
 */
#blurb {
  display: none;
}

#blurb hr {
  border-color: var(--divider);
  border-width: 1px;
  margin: 1rem 0;
}

#sidebar-toggle {
  display: none;
  background-color: var(--toggle_bg) !important;
  border-color: var(--toggle_border) !important;
  border-radius: 6px;
  transition: all 0.3s ease;
  width: 36px;
  height: 36px;
  padding: 6px;
  border-width: 2px;
  border-style: solid;
  display: flex;
  align-items: center;
  justify-content: center;
}

#sidebar-toggle:hover {
  background-color: var(--toggle_bg_hover) !important;
  border-color: var(--toggle_border_hover) !important;
}

#collapse *:first-child {
  margin-top: 1rem;
}

/* Hamburger icon for the toggle button (3 horizontal bars)
 * The SVG is embedded directly using a data URL.
 */
.navbar-toggler-icon {
  background-image: url("data:image/svg+xml,%3csvg viewBox='0 0 30 30' xmlns='http://www.w3.org/2000/svg'%3e%3cpath stroke='%23FFFFFF' stroke-width='2.5' stroke-linecap='round' stroke-miterlimit='10' d='M4 7h22M4 15h22M4 23h22'/%3e%3c/svg%3e");
  width: 24px;
  height: 24px;
  background-position: center;
  background-repeat: no-repeat;
  display: block;
  margin: 0 auto;
}

/* Note: Toggle icon color is controlled by --toggle_icon_color variable */
/* SVG color needs to be updated manually if changing --toggle_icon_color */

/* Top-level page titles in the content area */
#page-content h1 {
  text-align: center;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 1.5em;
}

/* ------------------------------
 * Desktop layout (min-width: 48em ≈ 768px)
 * - Sidebar is fixed and always visible
 * - Main content is shifted to the right
 * - Toggle collapses the sidebar width
 * ------------------------------ */
@media (min-width: 48em) {
  /* Fix the sidebar on the left and give it a fixed width */
  #sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 16rem;
    text-align: left;
    transition: margin 0.3s ease-in-out, padding 0.3s ease-in-out;
  }

  /* Toggle button that collapses / expands the sidebar.
   * Only visible on desktop, near the top-left corner.
   */
  #sidebar-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    top: 0;
    border-color: var(--toggle_border) !important;
    background-color: var(--toggle_bg) !important;
    transition: all 0.3s ease-in-out;
    width: 36px;
    height: 36px;
    padding: 6px;
    border-width: 2px;
    border-style: solid;
    cursor: pointer;
  }
  
  #sidebar-toggle:hover {
    background-color: var(--toggle_bg_hover) !important;
    border-color: var(--toggle_border_hover) !important;
  }

  /* When collapsed:
   * - Shift the sidebar off-screen with a negative margin
   * - Reduce right padding so content gets more width
   */
  #sidebar.collapsed {
    margin-left: -12.5rem;
    padding-right: 0.5rem;
  }

  /* When collapsed move the toggle upward so it stays visible */
  #sidebar.collapsed #sidebar-toggle {
    top: 0.5rem;
  }

  /* When collapsed, move the main content closer to the left.
   * The margin-left matches the collapsed sidebar width.
   */
  #sidebar.collapsed ~ #page-content {
    margin-left: calc(5.5rem + 5px);  /* Collapsed sidebar width (5.5rem) + 5px spacing */
    padding-left: 0;  /* Remove left padding since spacing is handled by margin */
  }

  /* Push sidebar inner content (except header with toggle) further off-screen
   * so that only icons / small area is visible when collapsed.
   */
  #sidebar.collapsed > *:not(:first-child) {
    margin-left: -6rem;
    margin-right: 6rem;
  }

  /* On desktop we show the descriptive blurb again */
  #blurb {
    display: block;
  }

  /* Hide the top navbar toggle (mobile style) on desktop */
  #navbar-toggle {
    display: none;
  }

  #collapse {
    display: block;
  }

  /* Main content area: keep it to the right of the sidebar. */
  #page-content {
    padding: 0.5rem 5px;
    margin-left: calc(16rem + 5px);  /* Sidebar width (16rem) + 5px spacing */
    margin-right: 5px;
    transition: margin-left 0.3s ease-in-out;
    background-color: var(--background_active);
    height: 100vh;
  }
}

/* ------------------------------
 * Active navigation link styles
 * - Applies to Bootstrap .nav-pills and .sidebar_nav_link
 * - Gives active item a gradient background and bold text
 * ------------------------------ */
.nav-pills .nav-link.active,
.sidebar_nav_link.active,
#sidebar .nav-pills .nav-link.active,
#sidebar .sidebar_nav_link.active {
    color: var(--active_text) !important;
    background: linear-gradient(135deg, #1e3a8a, #2563eb) !important;
    font-weight: 600;
    border: none !important;
    outline: none !important;
    opacity: 1 !important;
    border-radius: 6px;
}

.nav-pills .nav-link.active .nav_link_span,
.sidebar_nav_link.active .nav_link_span,
#sidebar .nav-pills .nav-link.active .nav_link_span,
#sidebar .sidebar_nav_link.active .nav_link_span {
    color: var(--active_text) !important;
    font-weight: 600;
}

.nav-pills .nav-link.active i,
.sidebar_nav_link.active i,
#sidebar .nav-pills .nav-link.active i,
#sidebar .sidebar_nav_link.active i {
    color: var(--active_icon) !important;
    opacity: 1 !important;
}

.display-4 {
    color: #ffffff !important;
    font-size: 18px;
    font-weight: 700;
    opacity: 1 !important;
    line-height: 1.3;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.display-4 span {
    color: #ffffff !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

/* Base style for each sidebar navigation link:
 * - horizontal layout (icon + text)
 * - subtle hover transition
 */
.sidebar_nav_link {
    color: var(--passive_text);
    font-size: 0.95em;
    font-weight: 500;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 0.6rem 0.8rem;
    transition: all 0.2s ease;
    line-height: 1.4;
    border: none !important;
    outline: none !important;
    min-height: 2.5rem;
    border-radius: 6px;
    margin: 0.2rem 0;
}

.sidebar_nav_link .nav_link_span {
    color: inherit;
}

/* Hover state for sidebar links:
 * - light background highlight
 * - brighter text color
 */
.sidebar_nav_link:hover {
    color: var(--hover_text);
    background-color: var(--hover_bg);
}

.sidebar_nav_link:hover i {
    color: var(--hover_icon);
}

/* Icon inside a sidebar link
 * - fixed width so all text lines up
 * - nudged slightly upwards to visually center with text
 */
.sidebar_nav_link i {
    margin-right: 0.6rem;
    width: 18px;
    display: flex;
    align-items: center !important;
    justify-content: center;
    flex-shrink: 0;
    font-size: 0.95em;
    line-height: 1;
    color: var(--passive_icon);
    margin-top: 0;
    margin-bottom: 0;
    align-self: center !important;
    transform: translateY(-8px); /* nudge icon up for vertical centering */
}

/* Text span inside each navigation link */
.nav_link_span {
    color: inherit;
    display: flex;
    align-items: center !important;
    line-height: 1.4;
    font-size: 1em;
    font-weight: inherit;
}

/* ------------------------------
 * Toggle Button Styles (mobile + desktop)
 * ------------------------------ */
#navbar-toggle {
  color: var(--navbar_toggle_color) !important;
  border-color: var(--navbar_toggle_border) !important;
}

#sidebar-toggle {
  color: var(--toggle_color) !important;
  border-color: var(--toggle_border) !important;
}

/* Global font for the entire app */
* {
  font-family: sans-serif;
}
```

### Under components, create `sidebar.py`
- Explain class-name and CSS
```python
"""Sidebar component with icons and collapsible functionality."""
import dash_bootstrap_components as dbc
from dash import html

# Sidebar header with title and toggle button
sidebar_header = dbc.Row(
    [
        dbc.Col(
            html.H2(
                [
                    html.Span("Wind Turbine ML", style={"display": "block"}),
                    html.Span("Anomaly Platform", style={"display": "block"}),
                ],
                className="display-4", # class name links to .css file and its style in the file
            )
        ),
        dbc.Col(
            [
                html.Button(
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    id="navbar-toggle",
                ),
                html.Button(
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    style={
                        "width": "40px",
                        "height": "40px",
                        "padding": "8px",
                        "font-size": "1.2em",
                    },
                    id="sidebar-toggle",
                ),
            ],
            width="auto",
            align="center",
        ),
    ]
)

# Sidebar with navigation links and icons
sidebar = html.Div(
    [
        sidebar_header,
        html.Div(
            [
                html.Hr(),
            ],
            id="blurb",
        ),
        # Collapsible navigation menu
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavLink(
                        [
                            html.I(className="fas fa-chart-line mr-2"),
                            html.Span("Model Prediction", className="nav_link_span"),
                        ],
                        href="/",
                        active="exact",
                        className="sidebar_nav_link",
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="fas fa-database mr-2"),
                            html.Span(
                                "Model Tracking & Registry", className="nav_link_span"
                            ),
                        ],
                        href="/model-tracking",
                        active="exact",
                        className="sidebar_nav_link",
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="fas fa-project-diagram mr-2"),
                            html.Span(
                                "ML Pipelines Structure", className="nav_link_span"
                            ),
                        ],
                        href="/ml-pipelines",
                        active="exact",
                        className="sidebar_nav_link",
                    ),
                    dbc.NavLink(
                        [
                            html.I(className="fas fa-sitemap mr-2"),
                            html.Span(
                                "Solution Architecture", className="nav_link_span"
                            ),
                        ],
                        href="/architecture",
                        active="exact",
                        className="sidebar_nav_link",
                    ),
                ],
                vertical=True,
                pills=True,
            ),
            id="collapse",
        ),
    ],
    id="sidebar",
)
```
### Under pages, create `home.py`
```python
import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, callback_context, dcc, html

from src.app_data_manager.utils import read_config
from src.app_ui.utils import (
    load_prod_data,
    create_error_plot,
    create_timeseries_plot,
    sync_xaxis,
)

# Configuration setup
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)

# Register this page with Dash - makes it accessible at the root URL "/"
dash.register_page(__name__, path="/")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Control Panel Card
                        html.Div(
                            [
                                html.H4(
                                    "Control Panel",
                                    style={"color": "#222", "marginBottom": "16px"},
                                ),
                                html.Label(
                                    "Lookback Datapoints",
                                    style={"color": "#222", "marginBottom": "8px"},
                                ),
                                dcc.Input(
                                    id="lookback-datapoints",
                                    type="number",
                                    min=1,
                                    step=1,
                                    value=144,
                                    style={
                                        "marginBottom": "16px",
                                        "width": "100%",
                                        "padding": "8px",
                                    },
                                ),
                            ],
                            style={
                                "backgroundColor": "#fff",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #e0e0e0",
                                "marginBottom": "20px",
                            },
                        ),
                        html.Div(
                            [
                                html.H5(
                                    "ML Solution Overview",
                                    style={"color": "#222", "marginBottom": "12px"},
                                ),
                                html.Ul(
                                    [
                                        html.Li(
                                            (
                                                "The ML solution monitors wind turbine health by "
                                                "predicting generated power and comparing it with "
                                                "the actual power output."
                                            ),
                                            style={"marginBottom": "16px"},
                                        ),
                                        html.Li(
                                            (
                                                "The ML model (CatBoost) is trained on data from "
                                                "normal operating conditions. When the rolling "
                                                "MAE/MAPE between predicted and actual power "
                                                "exceeds a predefined threshold continuously for "
                                                "6 hours, the turbine state is classified as an "
                                                "anomaly."
                                            ),
                                            style={"marginBottom": "16px"},
                                        ),
                                        html.Li(
                                            (
                                                "The model is designed to detect turbine anomaly "
                                                "states 2–4 weeks before a failure occurs, "
                                                "resulting in significant economic benefits "
                                                "through reduced downtime."
                                            ),
                                            style={"marginBottom": "16px"},
                                        ),
                                        html.Li(
                                            (
                                                "Model inference runs every 30 seconds for "
                                                "visualization purposes using data unseen during "
                                                "training. In practice, each data point "
                                                "represents a 10-minute measurement."
                                            ),
                                            style={"marginBottom": "16px"},
                                        ),
                                        html.Li(
                                            html.Span(
                                                (
                                                    "To explore the solution architecture, ML "
                                                    "pipelines, and model tracking and registry "
                                                    "details, use the Menu."
                                                ),
                                                style={"fontStyle": "italic"},
                                            ),
                                        ),
                                    ],
                                    style={
                                        "color": "#444",
                                        "fontSize": "14px",
                                        "lineHeight": "1.6",
                                    },
                                ),
                            ],
                            style={
                                "backgroundColor": "#fff",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #e0e0e0",
                            },
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(
                    [
                        dcc.Interval(
                            id="auto-refresh-interval",
                            interval=5000,
                            n_intervals=0,
                        ),
                        dcc.Store(id="xaxis-range-store", data=None),
                        html.H5(
                            "Anomaly Indicator – ML Model Error",
                            style={"marginBottom": "10px", "color": "#222"},
                        ),
                        dcc.Graph(
                            id="error-plot",
                            style={
                                "backgroundColor": "#fff",
                                "borderRadius": "12px",
                                "padding": "8px",
                                "height": "calc(50vh - 100px)",
                                "minHeight": "400px",
                                "marginBottom": "20px",
                            },
                        ),
                        html.H5(
                            "Power: Predictions vs True Values",
                            style={"marginBottom": "10px", "color": "#222"},
                        ),
                        dcc.Graph(
                            id="time-series-plot",
                            style={
                                "backgroundColor": "#fff",
                                "borderRadius": "12px",
                                "padding": "8px",
                                "height": "calc(50vh - 100px)",
                                "minHeight": "400px",
                            },
                        ),
                    ],
                    width=8,
                ),
            ]
        ),
    ],
    fluid=True,
    style={
        "paddingTop": "20px",
        "paddingLeft": "5px",
        "paddingRight": "5px",
        "height": "calc(100vh - 60px)",
    },
)


@callback(
    [Output("error-plot", "figure"), Output("time-series-plot", "figure")],
    [
        Input("lookback-datapoints", "value"),
        Input("auto-refresh-interval", "n_intervals"),
    ],
)
def update_plots(lookback_datapoints, n_intervals):
    if lookback_datapoints and lookback_datapoints >= 1:
        n_points = lookback_datapoints
    else:
        n_points = 144
    metric_threshold = config["inference_pipeline"]["anomaly_threshold"]
    df = load_prod_data(n_points)
    fig1 = create_error_plot(df, metric_threshold)
    fig2 = create_timeseries_plot(df)
    return fig1, fig2


@callback(
    [
        Output("error-plot", "figure", allow_duplicate=True),
        Output("time-series-plot", "figure", allow_duplicate=True),
        Output("xaxis-range-store", "data", allow_duplicate=True),
    ],
    [
        Input("error-plot", "relayoutData"),
        Input("time-series-plot", "relayoutData"),
    ],
    [
        State("error-plot", "figure"),
        State("time-series-plot", "figure"),
    ],
    prevent_initial_call=True,
)
def sync_plots_xaxis(
    error_relayout_data, timeseries_relayout_data, error_figure, timeseries_figure
):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "error-plot":
        updated_figure, x_range = sync_xaxis(error_relayout_data, timeseries_figure)
        return dash.no_update, updated_figure, x_range
    if trigger_id == "time-series-plot":
        updated_figure, x_range = sync_xaxis(timeseries_relayout_data, error_figure)
        return updated_figure, dash.no_update, x_range
    return dash.no_update, dash.no_update, dash.no_update
```
### Under `app.py`, add:
```python
"""Multi-page Dash application for ML model monitoring and visualization."""
import os
import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from app_ui.components.sidebar import sidebar
from dash import Input, Output, State, dcc, html

# Path setup for working directory and other runtime needs
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
os.chdir(project_root)


# Font Awesome for icons
FA = "https://use.fontawesome.com/releases/v5.15.1/css/all.css"

# Initialize the Dash app with Bootstrap theme and Font Awesome
# Note: CSS files in assets folder are automatically loaded
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, FA],
    suppress_callback_exceptions=True,
    use_pages=True,
    pages_folder="pages",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# App layout with sidebar
content = html.Div(id="page-content", children=[dash.page_container])

app.layout = html.Div(
    id="main-layout",
    children=[
        sidebar,
        content,
    ],
)

# Callback to toggle sidebar collapse
@app.callback(
    Output("sidebar", "className"),
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "className")],
)
def toggle_classname(n, classname):
    """Toggle sidebar collapsed state."""
    if n and classname == "":
        return "collapsed"
    return ""


# Callback to toggle mobile menu collapse
@app.callback(
    Output("collapse", "is_open"),
    [Input("navbar-toggle", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    """Toggle mobile menu collapse."""
    if n:
        return not is_open
    return is_open


server = app.server

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=8050)
```

### Run `src/app_ui/app.py`

### Explain Multi-Component and Pages Dash Application Structure
### Explain `app.py` structure
### Explain Page Columns and Rows
### Explain Dash Page Structure
### Explain `home.py` page, link to `custom.css` via class names. Explain `callback` structure
### Explain `sidebar.py` and link to `responsive-sidebar.css`

# Creating MLflow Tracking page
### Add this imports to `utils.py`
```python
import mlflow
from mlflow.tracking import MlflowClient
from datetime import datetime
import os
```
### Add this to `utils.py`:
```python
def get_model_info_by_alias(
    alias: str,
    mlflow_tracking_uri: str | None = None,
    model_name: str | None = None,
) -> dict | None:
    """Return basic info + test MAE/MAPE for a model version resolved by alias."""
    # 1) Resolve tracking URI (if not provided, uses the local mlflow server)
    if mlflow_tracking_uri is None:
        mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:8080")

    mlflow.set_tracking_uri(mlflow_tracking_uri)
    client = MlflowClient()

    # 3) Look up model version by alias
    try:
        model_version = client.get_model_version_by_alias(name=model_name, alias=alias)
    except Exception:
        return None

    # Require timestamp and run_id; otherwise we can't show useful info
    if model_version.last_updated_timestamp is None or model_version.run_id is None:
        return None

    last_updated = datetime.fromtimestamp(model_version.last_updated_timestamp / 1000.0)

    # 4) Fetch run to read metrics
    try:
        run = client.get_run(model_version.run_id)
    except Exception:
        return None

    metrics = run.data.metrics

    # Helper: given a list of possible metric names, return the first one that
    # exists in `metrics` (or None if none of them are logged in this run).
    def _first_metric(keys: list[str]) -> float | None:
        return next((metrics[k] for k in keys if k in metrics), None)

    test_mae = _first_metric([
        "test_mae",
        "test_MAE",
        "test_mae_err",
        "test_MAE_err",
        "mae_test",
        "MAE_test",
    ])
    test_mape = _first_metric([
        "test_mape",
        "test_MAPE",
        "test_mape_err",
        "test_MAPE_err",
        "mape_test",
        "MAPE_test",
    ])

    return {
        "model_name": model_name,
        "version": model_version.version,
        "last_updated": last_updated,
        "test_mae": test_mae,
        "test_mape": test_mape,
    }
```
### Create `app_ui/pages/model_tracking`:
### Add this to `utils.py`:
```python
# Model tracking page: format model info for display
# Model tracking page: format model info for display
def format_last_updated(info):
    if info.get("last_updated") is None:
        return "N/A"
    return info["last_updated"].strftime("%Y-%m-%d %H:%M:%S")


def format_mae(info):
    if info.get("test_mae") is None:
        return "MAE: N/A"
    return f"MAE: {info['test_mae']:.4f}"


def format_mape(info):
    if info.get("test_mape") is None:
        return "MAPE: N/A"
    return f"MAPE: {info['test_mape']:.4f}%"


def create_challenger_info_content(challenger_info):
    """Build HTML for challenger model info card. Returns html.P with message if challenger_info is None."""
    if not challenger_info:
        return html.P(
            "No challenger model found in registry. Make sure MLflow is running and a model is registered with 'challenger' alias.",
            className="mt-empty",
        )
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H6("Model Name", className="mt-label"),
                    html.P(challenger_info.get("model_name", "N/A"), className="mt-value"),
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.H6("Version", className="mt-label"),
                    html.P(
                        f"v{challenger_info['version']}" if challenger_info.get("version") else "N/A",
                        className="mt-value",
                    ),
                ],
                width=2,
            ),
            dbc.Col(
                [
                    html.H6("Last Updated", className="mt-label"),
                    html.P(format_last_updated(challenger_info), className="mt-value"),
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.H6("Test Set Error Metrics", className="mt-label"),
                    html.Div(
                        [
                            html.P(format_mae(challenger_info), className="mt-metric"),
                            html.P(format_mape(challenger_info), className="mt-metric-last"),
                        ],
                        className="mt-metrics-wrap",
                    ),
                ],
                width=4,
            ),
        ],
        className="g-4",
    )


def create_champion_info_content(champion_info):
    """Build HTML for champion model info card. Returns html.P with message if champion_info is None."""
    if not champion_info:
        return html.P(
            "No champion model found in registry. Make sure MLflow is running and a model is registered in Production stage.",
            className="mt-empty",
        )
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H6("Model Name", className="mt-label"),
                    html.P(champion_info.get("model_name", "N/A"), className="mt-value"),
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.H6("Version", className="mt-label"),
                    html.P(
                        f"v{champion_info['version']}" if champion_info.get("version") else "N/A",
                        className="mt-value",
                    ),
                ],
                width=2,
            ),
            dbc.Col(
                [
                    html.H6("Last Updated", className="mt-label"),
                    html.P(format_last_updated(champion_info), className="mt-value"),
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.H6("Test Set Error Metrics", className="mt-label"),
                    html.Div(
                        [
                            html.P(format_mae(champion_info), className="mt-metric"),
                            html.P(format_mape(champion_info), className="mt-metric-last"),
                        ],
                        className="mt-metrics-wrap",
                    ),
                ],
                width=4,
            ),
        ],
        className="g-4",
    )
```
### Add this to `model_tracking.py`
```python
"""
Model Tracking & Registry Page - MLflow Integration
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

from app_data_manager.utils import read_config
from app_ui.utils import (
    get_model_info_by_alias,
    create_champion_info_content,
    create_challenger_info_content,
) 

# Configuration setup
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

# Read configuration file (contains MLflow model name, etc.)
parameters_path = project_root / "conf" / "base" / "parameters.yml"
config = read_config(parameters_path)

# Register this page with Dash - accessible at "/model-tracking"
dash.register_page(__name__, path="/model-tracking")

# MLflow configuration
# Get MLflow tracking URI from environment variable or use default
# Using 127.0.0.1 instead of localhost helps with some browser security policies
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:8080")
# In production, this should be the external server IP/domain
MLFLOW_UI_URI = os.getenv("MLFLOW_UI_URI", "http://localhost:8080")

# Page layout - Single column layout, stacked vertically, full screen
layout = dbc.Container(
    [
        dcc.Interval(
            id="champion-info-interval",
            interval=60000,
            n_intervals=0,
        ),
        dcc.Store(id="champion-info-trigger", data=0),
        dcc.Interval(
            id="challenger-info-interval",
            interval=60000,
            n_intervals=0,
        ),
        dcc.Store(id="challenger-info-trigger", data=0),
        dcc.Store(id="champion-status-store", data=None),
        dcc.Store(id="challenger-status-store", data=None),
        dcc.Store(id="last-update-timestamp", data=None),
        html.Div(
            [
                html.H4("MLflow Integration", className="mt-section-title"),
                html.P(
                    "This page provides access to the MLflow Tracking UI, where you can "
                    "view experiment runs and metrics, compare model performance, track hyperparameters, "
                    "manage model versions, and register and promote models. "
                    "Click the buttons below to access different sections of the MLflow Tracking UI.",
                    className="mt-intro",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        "Refresh model info",
                                        id="refresh-model-info-btn",
                                        color="secondary",
                                        size="lg",
                                        className="mt-btn-full mt-btn-mint",
                                    ),
                                    html.Div(id="model-info-status", className="mt-status-wrap mt-status-under-btn"),
                                ],
                                className="mt-btn-with-status",
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Open MLflow UI",
                                href=MLFLOW_UI_URI,
                                target="_blank",
                                color="primary",
                                size="lg",
                                className="mt-btn-full",
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Experiments",
                                href=f"{MLFLOW_UI_URI}/#/experiments",
                                target="_blank",
                                color="primary",
                                size="lg",
                                className="mt-btn-full",
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Models",
                                href=f"{MLFLOW_UI_URI}/#/models",
                                target="_blank",
                                color="primary",
                                size="lg",
                                className="mt-btn-full",
                            ),
                            width=3,
                        ),
                    ],
                    className="g-3",
                ),
            ],
            className="mt-card",
        ),
        html.Div(
            [
                html.H5("Champion Model Information", className="mt-card-title"),
                html.Div(
                    id="champion-model-info",
                    children=[
                        html.Div(
                            "Loading champion model information...",
                            className="mt-loading",
                        ),
                    ],
                ),
            ],
            className="mt-card",
        ),
        html.Div(
            [
                html.H5("Challenger Model Information", className="mt-card-title"),
                html.Div(
                    id="challenger-model-info",
                    children=[
                        html.Div(
                            "Loading challenger model information...",
                            className="mt-loading",
                        ),
                    ],
                ),
            ],
            className="mt-card",
        ),
    ],
    fluid=True,
    className="mt-page-container",
)


# --- Callback: Refresh button -> trigger stores ---
# When "Refresh model info" is clicked, we bump both trigger stores so the champion
# and challenger info callbacks re-run and refetch from MLflow.
@callback(
    [Output("champion-info-trigger", "data"), Output("challenger-info-trigger", "data")],
    Input("refresh-model-info-btn", "n_clicks"),
    prevent_initial_call=True,
)
def refresh_model_info(n_clicks):
    """On Refresh button click, update both trigger stores so champion and challenger callbacks run."""
    if n_clicks is None:
        return dash.no_update, dash.no_update
    return n_clicks, n_clicks


# --- Callback: Champion model info ---
# Runs on page load (interval n_intervals), every 60s (interval), or when refresh trigger updates.
# Fetches model with "champion" alias from MLflow, fills the champion card and writes status + timestamp
# for the green/red status light.
@callback(
    [
        Output("champion-model-info", "children"),
        Output("champion-status-store", "data"),
        Output("last-update-timestamp", "data"),
    ],
    [
        Input("champion-info-interval", "n_intervals"),
        Input("champion-info-trigger", "data"),
    ],
)
def update_champion_info(n_intervals, trigger):
    current_config = read_config(parameters_path)
    model_name = current_config["mlflow"]["registered_model_name"]
    champion_info = get_model_info_by_alias(
        "champion", MLFLOW_TRACKING_URI, model_name=model_name
    )
    status = "ok" if champion_info else "no_model"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return create_champion_info_content(champion_info), status, ts


# --- Callback: Challenger model info ---
# Runs on page load, every 60s, or when refresh trigger updates. Fetches model with "challenger"
# alias from MLflow and fills the challenger card; writes status for the status light.
@callback(
    [
        Output("challenger-model-info", "children"),
        Output("challenger-status-store", "data"),
    ],
    [
        Input("challenger-info-interval", "n_intervals"),
        Input("challenger-info-trigger", "data"),
    ],
)
def update_challenger_info(n_intervals, trigger):
    current_config = read_config(parameters_path)
    model_name = current_config["mlflow"]["registered_model_name"]
    challenger_info = get_model_info_by_alias(
        "challenger", MLFLOW_TRACKING_URI, model_name=model_name
    )
    status = "ok" if challenger_info else "no_model"
    return create_challenger_info_content(challenger_info), status


# --- Callback: Status light under Refresh button ---
# Reads champion/challenger status and last-update timestamp; shows green dot when both models
# are present, red dot when champion or challenger is missing; displays "Updated at <time>".
@callback(
    Output("model-info-status", "children"),
    [
        Input("champion-status-store", "data"),
        Input("challenger-status-store", "data"),
        Input("last-update-timestamp", "data"),
    ],
)
def update_status_light(champion_status, challenger_status, last_ts):
    """Show green light when both models found, red when either missing. Display last update time."""
    if last_ts is None:
        return html.Span("—", className="mt-status-text")
    both_ok = champion_status == "ok" and challenger_status == "ok"
    # Red light: champion or challenger is missing in the registry; green when both are present.
    light_class = "mt-status-light mt-status-light--green" if both_ok else "mt-status-light mt-status-light--red"
    return html.Div(
        [
            html.Span(className=light_class),
            html.Span(f"Updated at {last_ts}", className="mt-status-text"),
        ],
        className="mt-status-inner",
    )
```

### Run `kedro viz` on a separate terminal

### Add `ml_pipelines.py` to the page
```python
import os
import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import html

# Configuration setup
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

# Register this page with Dash - accessible at "/ml-pipelines"
dash.register_page(__name__, path="/ml-pipelines")

# Kedro-Viz configuration
# Get Kedro-Viz URI from environment variable or use default
# Kedro-Viz is a separate service that visualizes Kedro pipelines
# Default: http://localhost:4141 (local Kedro-Viz server)
# Can be configured via KEDRO_VIZ_URI environment variable
KEDRO_VIZ_URI = os.getenv("KEDRO_VIZ_URI", "http://localhost:4141")


# Page layout - 2-column layout: Info panel (left) + Visualization (right)
layout = dbc.Container(
    [
        dbc.Row(
            [
                # Left column: Pipeline Information Panel (3/12 width)
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H5("Pipeline Details", className="mp-panel-title"),
                                html.Div(
                                    [
                                        html.H6("Feature Engineering Pipeline", className="mp-section-title"),
                                        html.Ul(
                                            [
                                                html.Li(
                                                    "Standardizes column names and removes irrelevant columns"
                                                ),
                                                html.Li(
                                                    "Detects and handles outliers using difference-based methods"
                                                ),
                                                html.Li(
                                                    "Applies signal smoothing to reduce noise"
                                                ),
                                                html.Li(
                                                    "Creates lag features to capture temporal dependencies"
                                                ),
                                                html.Li(
                                                    "Generates rolling statistical features (mean, std, min, max)"
                                                ),
                                                html.Li(
                                                    "Separates features from target variable (power output)"
                                                ),
                                                html.Li(
                                                    "Ensures consistent transformations across training and production"
                                                ),
                                            ],
                                            className="mp-section-list",
                                        ),
                                        html.H6("Training Pipeline", className="mp-section-title"),
                                        html.Ul(
                                            [
                                                html.Li(
                                                    "Splits data into training and test sets"
                                                ),
                                                html.Li(
                                                    "Performs hyperparameter tuning using cross-validation"
                                                ),
                                                html.Li(
                                                    "Trains the best model on full training set"
                                                ),
                                                html.Li(
                                                    "Evaluates model performance on test set"
                                                ),
                                                html.Li(
                                                    "Logs results, metrics, and model to MLflow"
                                                ),
                                                html.Li(
                                                    "Registers model in MLflow model registry"
                                                ),
                                                html.Li(
                                                    "Validates model as challenger candidate"
                                                ),
                                            ],
                                            className="mp-section-list",
                                        ),
                                        html.H6("Inference Pipeline", className="mp-section-title"),
                                        html.Ul(
                                            [
                                                html.Li(
                                                    "Loads champion model from MLflow registry"
                                                ),
                                                html.Li(
                                                    "Applies feature engineering transformations"
                                                ),
                                                html.Li(
                                                    "Generates predictions on production data"
                                                ),
                                                html.Li(
                                                    "Computes raw and rolling prediction MAPE metric"
                                                ),
                                                html.Li(
                                                    "Detects anomalies of rolling metric is above the threshold"
                                                ),
                                                html.Li(
                                                    "Saves predictions, errors and anomalies to the database"
                                                ),
                                            ],
                                            className="mp-section-list",
                                        ),
                                    ]
                                ),
                            ],
                            className="mp-panel",
                        ),
                    ],
                    width=3,
                ),
                # Right column: Kedro-Viz Visualization (9/12 width)
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H5("ML Pipeline Visualization", className="mp-viz-title"),
                                # Kedro-Viz iframe - embeds visualization in an iframe
                                html.Iframe(
                                    src=KEDRO_VIZ_URI,
                                    className="mp-viz-iframe",
                                    allow="fullscreen",
                                ),
                            ],
                            className="mp-viz-container",
                        ),
                    ],
                    width=9,
                ),
            ]
        ),
    ],
    fluid=True,
    className="mp-page-container",
)
```

### Add `app_architecture.gif` to `app_ui/assets`

### Add `architecture.py` to `app_ui/pages`
```python
import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import html

# Configuration setup
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

# Register this page with Dash - accessible at "/architecture"
dash.register_page(__name__, path="/architecture")

# Asset path - architecture diagram is stored in the assets folder
# Dash automatically serves files from /assets/ at the root URL path
ARCHITECTURE_GIF_PATH = "/assets/app_architecture.gif"


def _li_bold_tools(description, tools_brackets):
    """Return an Li with description and parenthesized tools in bold."""
    return html.Li([description, " ", html.Strong(tools_brackets)])


# Page layout - 2-column layout: Info panel (left) + Architecture diagram (right)
layout = dbc.Container(
    [
        dbc.Row(
            [
                # Left column: Components and tools (4/12 width)
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H5("Components and tools", className="arch-section-title"),
                                html.Ul(
                                    [
                                        _li_bold_tools(
                                            "Reproducible development environment",
                                            "(uv, uv.lock)",
                                        ),
                                        _li_bold_tools(
                                            "Dockerized multi-service architecture",
                                            "(Docker, Docker Compose)",
                                        ),
                                        _li_bold_tools(
                                            "Persistent storage via Docker volumes",
                                            "(Docker volumes)",
                                        ),
                                        _li_bold_tools(
                                            "Modular ML pipelines",
                                            "(Kedro)",
                                        ),
                                        _li_bold_tools(
                                            "Separation of feature engineering, training, inference, monitoring pipelines",
                                            "(Kedro, Prefect)",
                                        ),
                                        _li_bold_tools(
                                            "Code quality automation: pre-commit + formatting/linting",
                                            "(pre-commit, Ruff)",
                                        ),
                                        _li_bold_tools(
                                            "Automated testing and validation",
                                            "(PyTest)",
                                        ),
                                        _li_bold_tools(
                                            "CI pipeline on every commit/PR",
                                            "(GitHub Actions)",
                                        ),
                                        _li_bold_tools(
                                            "CD pipeline build + push + deploy",
                                            "(GitHub Actions, Docker)",
                                        ),
                                        _li_bold_tools(
                                            "Docker image versioning and rollback",
                                            "(Docker Registry)",
                                        ),
                                        _li_bold_tools(
                                            "Cloud production deployment",
                                            "(DigitalOcean, Docker Compose)",
                                        ),
                                        _li_bold_tools(
                                            "Orchestration server for scheduling and triggers",
                                            "(Prefect)",
                                        ),
                                        _li_bold_tools(
                                            "Streaming/batch data ingestion service",
                                            "(Python, SQLite)",
                                        ),
                                        _li_bold_tools(
                                            "SQL-backed storage for history, predictions, and errors",
                                            "(SQLite)",
                                        ),
                                        _li_bold_tools(
                                            "Experiment tracking for runs, metrics, artifacts",
                                            "(MLflow)",
                                        ),
                                        _li_bold_tools(
                                            "Central model registry with versioning and stage transitions",
                                            "(MLflow Model Registry)",
                                        ),
                                        _li_bold_tools(
                                            "Hyperparameter tuning integrated into training",
                                            "(Optuna / scikit-learn, tracked in MLflow)",
                                        ),
                                        _li_bold_tools(
                                            "Champion/Challenger model promotion workflow",
                                            "(MLflow aliases/tags)",
                                        ),
                                        _li_bold_tools(
                                            "Monitoring pipeline for model performance monitoring",
                                            "(Kedro, Prefect)",
                                        ),
                                        _li_bold_tools(
                                            "Automated re-training triggers based on monitoring thresholds",
                                            "(Kedro, Prefect, MLflow)",
                                        ),
                                    ],
                                    className="arch-list",
                                ),
                            ],
                            className="arch-panel",
                        ),
                    ],
                    width=4,
                ),
                # Right column: Architecture Diagram (8/12 width)
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H5("Architecture Diagram", className="arch-diagram-title"),
                                html.Div(
                                    id="architecture-image-container",
                                    children=[
                                        html.Img(
                                            src=ARCHITECTURE_GIF_PATH,
                                            className="arch-diagram-img",
                                            alt="Application Architecture Diagram",
                                        ),
                                    ],
                                ),
                            ],
                            className="arch-diagram-container",
                        ),
                    ],
                    width=8,
                ),
            ],
            className="arch-row",
        ),
    ],
    fluid=True,
)
```

### Create entry `entrypoints/app_ui.py`
```python
"""Programmatic entrypoint for running the Dash UI application."""

import os
import sys
from pathlib import Path

# Add src and app_ui directories to path before imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "app_ui"))

# Change to project directory so relative paths resolve correctly
os.chdir(project_root)

from app_ui.app import app  # noqa: E402

if __name__ == "__main__":
    # Use debug=False in production/Docker, debug=True for local development
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, use_reloader=False, host="0.0.0.0", port=8050)
```