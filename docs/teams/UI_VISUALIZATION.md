# UI & Data Visualization

**How can maintenance engineers and factory floor managers understand the whole
system, its evidence and its uncertainty through a clear, useful interface?**

## Entry files

- [dashboard.py](../../osat_edge/ui/dashboard.py): selection, timers, input and
  simulation controls.
- [screens/](../../osat_edge/ui/screens/README.md): five ordinary QWidget classes,
  each building and refreshing its own widgets.
- [widgets.py](../../osat_edge/ui/widgets.py): raw trends, cards, tables and formatting.
- [theme.py](../../osat_edge/ui/theme.py): shared styles and color meanings.
- [cli.py](../../osat_edge/ui/cli.py): headless commands and optional dashboard launch.

Start with MachineScreen's `refresh` and [UI tests](../../osat_edge/ui/tests/test_ui.py).
Tests run offscreen and cover current/last-known evidence, model status,
physics research and ticket selection.

## What this team owns

Design transparent visualization of the whole system, guided by the OSAT plant's
requirements. The main intended users are maintenance engineers and factory floor
managers. Learn their tasks, terminology, units, information needs and maintenance
workflow, then turn those requirements into clear screens and reviewable user
scenarios. The controlled 0.2.6 PoC has not established plant acceptance; intended
users and future requirements must not be presented as completed plant validation.

A maintenance engineer should be able to follow a warning back to measurements,
model context, physical evidence, limitations and maintenance information. A
floor manager needs understandable fleet condition, priorities, currentness and
unavailable assessments. Support both overview and drill-down without hiding
uncertainty or making a proposed failure look confirmed.

## The cross-team contract

Read PipelineResult and research catalog objects from their owners. Work with
Failure Research on physical meaning, ML on algorithm and score meaning,
Reliability on supported claims and statistical limits, and Data Pipeline on
identity, source, currentness and authority. Feed user requirements back to all
teams so necessary information travels through the pipeline rather than being
invented by a screen.

Make the path from input status through analysis to health, evidence and
maintenance records understandable. Use plain labels, consistent units, readable
charts and text alongside color. Distinguish UNKNOWN, last-known data,
research-only physics, uncalibrated risk and demo-only tickets.

A first contribution can improve an unavailable explanation for a named engineer
or manager task. Check all nine families, disconnected input and absent models.
For a future code version, verify a bounded screen change offscreen and review it
against the user scenario. The 0.2.6 application remains frozen. Do not fit models,
choose thresholds or grant ticket authority in UI code. Preserve five screens
and the single-instance lock.
