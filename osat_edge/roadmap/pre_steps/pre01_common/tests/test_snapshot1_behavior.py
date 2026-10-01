"""Snapshot 1 behavior contracts captured before the snapshot 2 refactor.

The expected digests are fixed baseline observations, not recalculated from the
current implementation. Release/source identity metadata is excluded. Current report sections are
flattened to the original record, and only the authorized product-name change
and added scope wording are normalized; original digests remain untouched.
"""
import dataclasses
import datetime as dt
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import unittest
from collections.abc import Mapping

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[5]
import numpy as np
from PyQt6.QtWidgets import QApplication, QLabel, QPlainTextEdit, QTableWidget
from osat_edge.roadmap.post_steps.post01_demo.demo import create_demo_fleet, run_demo
from osat_edge.roadmap.post_steps.post02_reference_replay.replay import run_reference_replay
from osat_edge.roadmap.post_steps.post05_full_poc.poc import run_full_poc
from osat_edge.ui.dashboard import SemiGuardWindow

def normalize(value):
    if dataclasses.is_dataclass(value):
        return {f.name: normalize(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Enum): return value.value
    if isinstance(value, dt.datetime): return value.isoformat()
    if isinstance(value, Mapping): return {str(normalize(k)): normalize(v) for k,v in value.items()}
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, (tuple,list)): return [normalize(v) for v in value]
    if isinstance(value, (set,frozenset)): return sorted(normalize(v) for v in value)
    if isinstance(value, np.generic): return value.item()
    return value

def encoded(value):
    return json.dumps(normalize(value), ensure_ascii=False, sort_keys=True, separators=(",",":"), allow_nan=False).encode("utf-8")

def digest(value): return hashlib.sha256(encoded(value)).hexdigest()

def fleet_trace():
    demo=create_demo_fleet()
    result=hashlib.sha256()
    try:
        for phase, ticks in (("normal",10),("fault",75),("recovery",100)):
            if phase=="fault": demo.inject_ws_spindle()
            if phase=="recovery": demo.clear_ws_fault()
            for _ in range(ticks): result.update(encoded(demo.tick())+b"\n")
        return result.hexdigest()
    finally: demo.close()

def historical_branding(text):
    """Compare display behavior while allowing the explicitly requested rename."""
    return text.replace("OSAT SemiGuard", "OSAT Fleet Command").replace("OSAT SEMIGUARD", "OSAT FLEET COMMAND")

def ui_content(window):
    labels=sorted(historical_branding(w.text()) for w in window.findChildren(QLabel) if not w.text().startswith("UTC:"))
    text=sorted(historical_branding(w.toPlainText()) for w in window.findChildren(QPlainTextEdit))
    tables=[]
    for w in window.findChildren(QTableWidget):
        tables.append((w.accessibleName(),[[w.item(r,c).text() if w.item(r,c) else "" for c in range(w.columnCount())] for r in range(w.rowCount())]))
    return {"labels":labels,"text":text,"tables":sorted(tables),"tabs":[window.tabs.tabText(i) for i in range(window.tabs.count())]}

def ui_trace():
    application=QApplication.instance() or QApplication([])
    window=SemiGuardWindow()
    window.inference_timer.stop(); window.paint_timer.stop()
    result=hashlib.sha256()
    try:
        for phase in ("normal","fault","disconnected"):
            if phase=="fault":
                window.demo.inject_ws_spindle()
                for _ in range(75): window.demo.tick()
            if phase=="disconnected": window.pipeline.set_connected(False)
            for family in window.pipeline.machines:
                window._select(family)
                result.update(encoded(ui_content(window))+b"\n")
        return result.hexdigest()
    finally:
        window.close(); application.processEvents()


EXPECTED = json.loads((ROOT / "osat_edge/roadmap/pre_steps/pre01_common/resources/snapshot1_behavior.json").read_bytes())["behavior_sha256"]

class Snapshot1BehaviorTests(unittest.TestCase):
    def test_complete_fleet_results_for_185_ticks_match_snapshot1(self):
        self.assertEqual(EXPECTED["fleet_185_ticks_all_fields"], fleet_trace())

    def test_demo_payload_matches_snapshot1(self):
        self.assertEqual(EXPECTED["demo"], digest(run_demo()))

    def test_reference_replay_payload_matches_snapshot1(self):
        self.assertEqual(EXPECTED["reference_replay"], digest(run_reference_replay()))

    def test_poc_decisions_match_snapshot1(self):
        report = run_full_poc()
        proof = report.pop("functional_proof")
        proof.pop("scope")
        proof.pop("ui_validation")
        report.update(proof)
        report.pop("external_scientific_evidence")
        report["connectivity"]["sent_by_fleet_command"] = report["connectivity"].pop("sent_by_host")
        report["limitations"].remove("MODEL + TICKET RELOAD WITH DETERMINISTIC REPLAY; Step09 live state is not checkpointed.")
        for key in ("report_sha256", "implementation_identity", "snapshot"):
            report.pop(key)
        self.assertEqual(EXPECTED["poc_decisions"], digest(report))

    def test_27_dashboard_machine_views_match_snapshot1(self):
        self.assertEqual(EXPECTED["ui_27_machine_views"], ui_trace())
