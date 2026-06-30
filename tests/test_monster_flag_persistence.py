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

    # BUG-M97 refactor (2026-06-30): the root-level is_monster stamping moved
    # OUT of main.py and INTO src.monster_hunt.revalidate_and_apply_monster,
    # which now sets pick["is_monster"] = True only when the widened SL/TP/qty
    # pass re-validation. The Bug #16 contract below (picks_for_log reads the
    # root flag) is unchanged. Assert the stamping still exists in the helper.
    helper_src = Path("src/monster_hunt.py").read_text()
    assert 'pick["is_monster"] = True' in helper_src or "pick['is_monster'] = True" in helper_src, (
        "Monster treatment must stamp root-level is_monster on the pick "
        "(now in src.monster_hunt.revalidate_and_apply_monster)."
    )

    assert '"is_monster": p.get("is_monster") or p["scores"].get("is_monster") or False' in src, (
        "picks_for_log must read root-level p['is_monster'] before falling back "
        "to p['scores']['is_monster'], otherwise monster-treated picks log false."
    )
