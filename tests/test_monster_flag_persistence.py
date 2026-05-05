"""Bug #16 (2026-05-05): monster treatment flag must persist to picks_log.

Problem:
  main.py sets root-level p["is_monster"] = True after applying monster
  treatment, but the pick logging dict historically read only
  p["scores"].get("is_monster"). That can log false even when a pick was
  actually monster-treated.

Contract:
  The code path that builds picks_for_log must preserve root-level
  is_monster when present.
"""
from pathlib import Path


MAIN = Path("main.py")


def test_main_logs_root_level_is_monster_flag():
    src = MAIN.read_text()

    assert '_p["is_monster"] = True' in src or "_p['is_monster'] = True" in src, (
        "Test assumes monster treatment stamps root-level is_monster on pick."
    )

    assert '"is_monster": p.get("is_monster") or p["scores"].get("is_monster") or False' in src, (
        "picks_for_log must read root-level p['is_monster'] before falling back "
        "to p['scores']['is_monster'], otherwise monster-treated picks log false."
    )
