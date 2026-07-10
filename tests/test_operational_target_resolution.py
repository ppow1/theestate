from estate.core.operational_target_resolution import OperationalTargetResolver
from estate.core.operational_targets import OperationalTarget
from estate.core.operational_targets_runtime import OperationalTargetRuntime


def test_estate_aliases_resolve_to_canonical(tmp_path):
    r = OperationalTargetResolver(tmp_path)
    for ident, method in [("estate-main", "canonical_id"), ("estate", "alias"), ("theestate", "alias"), ("ppow1/theestate", "alias")]:
        res = r.resolve(ident)
        assert res.resolved
        assert res.canonical_target_id == "estate-main"
        assert res.resolution_method == method or ident == "ppow1/theestate"


def test_canonical_id_wins_over_alias(tmp_path):
    rt = OperationalTargetRuntime(tmp_path)
    targets = rt.load_targets()
    targets.append(OperationalTarget("estate", "Other", "git_repository", "X", aliases=["estate-main"], watch_state="disabled"))
    rt.write_targets(targets)
    res = OperationalTargetResolver(tmp_path).resolve("estate")
    assert res.canonical_target_id == "estate"
    assert res.resolution_method == "canonical_id"


def test_ambiguous_alias_and_not_found(tmp_path):
    rt = OperationalTargetRuntime(tmp_path)
    targets = rt.load_targets()
    targets.append(OperationalTarget("other", "Other", "git_repository", "X", aliases=["same"], watch_state="disabled"))
    targets[0].aliases.append("same")
    rt.write_targets(targets)
    assert OperationalTargetResolver(tmp_path).resolve("same").resolution_method == "ambiguous"
    nf = OperationalTargetResolver(tmp_path).resolve("missing")
    assert not nf.resolved
    assert nf.resolution_method == "not_found"
