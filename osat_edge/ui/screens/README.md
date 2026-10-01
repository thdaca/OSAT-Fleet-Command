# Five screens, five owners

The window in `../dashboard.py` owns selection, timers and simulation/input controls.
Each ordinary QWidget below owns its widgets and refresh logic. It reads the
window's selected machine and pipeline; it never changes inference or authority.

- [FleetScreen](fleet.py): nine cards, summary counts and local monitoring scope.
- [MachineScreen](machine.py): canonical telemetry, raw trend, model and subsystem evidence.
- [PhysicsScreen](physics.py): runtime/research/rejected claims, uncertainty and references.
- [MaintenanceScreen](maintenance.py): persisted tickets, deterministic evidence and prose.
- [SystemScreen](system.py): runtime, origin, security and authority facts.

Shared widgets/formatting live in `../widgets.py`; styles live in `../theme.py`.
No mixins, dynamic forwarding or compatibility proxies connect these screens.
Run `python -m unittest osat_edge.ui.tests.test_ui -v` from the repository root.
The tests use offscreen Qt and retain all five screens and uncertainty displays.
