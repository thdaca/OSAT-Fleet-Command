# Final test physics dossier

## Mechanism

A test handler moves packaged devices through contact and test phases. Motor
signatures reflect motion, drive/control behavior, friction, tooling, and load;
downstream DUT electrical results can supply process-ordered context but are not
themselves proof of handler cause.

## Candidate measurable relation

- `final_test.handler_motor_signature_consistency`: research-only and deliberately
  has no physical equation until current, position, velocity, motor, drive,
  control mode, motion command, and phase semantics are known.
- `final_test.contact_resistance`: existing research-only metrology candidate;
  unchanged and separate.

## Exact variables and units

Identified motor current `A`; actual position `mm` or `rad`; velocity `mm/s` or
`rad/s`; acceleration `mm/s^2` or `rad/s^2`; motion/contact phase and motor/
drive/control identity `state`; downstream DUT electrical results in their exact
source units with pseudonymous test context.

## Available OEM/process signals

FT-01 names handler motor current and vibration plus contact voltage/current and
socket temperature. DOI 10.1016/j.cie.2026.111872 reports real semiconductor
final-test use of upstream test-handler motor signatures and downstream DUT
electrical-test results.

## Confounders

Motion command/profile; motor and drive; control mode/gains; position, velocity,
and acceleration; handler tooling/contactors; friction/lubrication; temperature;
DUT/contact/test context; cycle/window alignment; maintenance state.

## Parameter identifiability

No physical parameter or baseline is identifiable from an anonymous current
trace alone. The exact motor/axis, motion phase, position/velocity trajectory,
controller, tool, and independently adjudicated equipment event are required.

## Calibration domain

One exact handler, motor/axis, drive/controller, tool/contact configuration, and
motion phase, with pseudonymous DUT context and chronologically held-out data.

## Uncertainty sources

Current scaling/filtering, position/velocity calibration, trigger alignment,
motor/control changes, maintenance/fault interval adjudication, and DUT/context
coupling.

## Falsification criteria

Reject if signatures are not repeatable by phase, DUT/motion/context changes
dominate, equipment events have no reproducible response, or sensor/window
faults mimic the result.

## Minimum machine experiment

First document the motor/drive/current and position/velocity/phase semantics.
Then compare approved healthy and independently adjudicated event intervals with
motion-profile, DUT-context, control-mode, and sensor/window negative controls.

## Source quality

DOI 10.1016/j.cie.2026.111872 is strong peer-reviewed real-semiconductor
equipment evidence. It is a publication, not raw executable telemetry and not
FT-01 validation.

## Measurement-semantics maturity

`LITERATURE_SUPPORTED`; the required FT-01 motion/control semantics and event
records are absent.

## Status

`RESEARCH_ONLY`. No equation, model, threshold, runtime feature, health output,
or paper-derived score is added.
