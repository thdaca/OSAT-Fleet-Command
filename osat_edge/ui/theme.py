"""Shared display colors and Qt styles; colors always accompany state text."""
from ..roadmap.pre_steps.pre01_common.contracts import HealthState

PALETTE = {
    "background": "#0B0904",
    "panel": "#121006",
    "panel_secondary": "#18130A",
    "amber": "#FFB000",
    "amber_secondary": "#D89A00",
    "amber_muted": "#C08B23",
    "light": "#F4E2B5",
    "watch": "#FFCC00",
    "degraded": "#FF5A36",
    "critical": "#FF2D2D",
    "unknown": "#B8B0A0",
}


QSS = f"""
QWidget {{ background: {PALETTE['background']}; color: {PALETTE['light']};
           font-family: 'Segoe UI'; font-size: 10pt; }}
QMainWindow {{ background: {PALETTE['background']}; }}
QFrame#header, QFrame#demo, QFrame#summary, QFrame#statusStrip {{
    background: {PALETTE['panel']}; border: 1px solid {PALETTE['amber_secondary']};
}}
QLabel#title {{ color: {PALETTE['amber']}; font: 700 20px 'Cascadia Mono', 'Consolas'; }}
QLabel#release {{ color: {PALETTE['amber_muted']}; font: 700 9px 'Cascadia Mono', 'Consolas'; }}
QLabel#section {{ color: {PALETTE['amber']}; font: 700 10px 'Cascadia Mono', 'Consolas'; }}
QLabel#instrument {{ color: {PALETTE['light']}; font-family: 'Cascadia Mono', 'Consolas'; }}
QFrame#machine {{ background: {PALETTE['panel']}; border: 1px solid {PALETTE['amber_secondary']};
                  border-left: 4px solid {PALETTE['amber_secondary']}; }}
QFrame#machine[selected="true"] {{ border-top: 2px solid {PALETTE['amber']}; }}
QFrame#machine[state="watch"] {{ border-left-color: {PALETTE['watch']}; }}
QFrame#machine[state="degraded"] {{ border-left-color: {PALETTE['degraded']}; }}
QFrame#machine[state="critical"] {{ border-left-color: {PALETTE['critical']}; }}
QFrame#machine[state="unknown"] {{ border-left-color: {PALETTE['unknown']}; }}
QLabel#machineTitle {{ color: {PALETTE['amber']}; font: 700 10px 'Cascadia Mono', 'Consolas'; }}
QLabel#health {{ color: {PALETTE['amber_secondary']}; font: 700 15px 'Cascadia Mono', 'Consolas'; }}
QPushButton {{ background: {PALETTE['panel_secondary']}; border: 1px solid {PALETTE['amber_secondary']};
               color: {PALETTE['light']}; padding: 6px 10px; }}
QPushButton:hover, QPushButton:focus {{ border-color: {PALETTE['amber']}; }}
QPushButton#danger {{ color: {PALETTE['degraded']}; border-color: {PALETTE['degraded']}; }}
QComboBox, QPlainTextEdit, QTableWidget {{ background: {PALETTE['panel']};
    border: 1px solid {PALETTE['amber_secondary']}; selection-background-color: #4A350D;
    selection-color: {PALETTE['light']}; }}
QComboBox {{ padding: 5px 8px; }}
QHeaderView::section {{ background: {PALETTE['panel_secondary']}; color: {PALETTE['amber']};
                        padding: 5px; border: 0; border-right: 1px solid #4A350D; }}
QTableWidget {{ gridline-color: #3D2D10; alternate-background-color: #151106; }}
QTabWidget::pane {{ border: 1px solid {PALETTE['amber_secondary']}; }}
QTabBar::tab {{ background: {PALETTE['panel']}; color: {PALETTE['amber_muted']};
                padding: 8px 18px; border: 1px solid #3D2D10; }}
QTabBar::tab:selected {{ background: {PALETTE['panel_secondary']}; color: {PALETTE['amber']};
                         border-bottom: 2px solid {PALETTE['amber']}; }}
QTabBar::tab:focus {{ border: 1px solid {PALETTE['light']}; }}
QCheckBox {{ color: {PALETTE['light']}; }}
QSplitter::handle {{ background: #4A350D; }}
QScrollArea {{ border: 0; }}
"""


HEALTH_COLOR = {
    HealthState.UNKNOWN: PALETTE["unknown"],
    HealthState.NORMAL: PALETTE["amber_secondary"],
    HealthState.WATCH: PALETTE["watch"],
    HealthState.DEGRADED: PALETTE["degraded"],
    HealthState.CRITICAL: PALETTE["critical"],
}


