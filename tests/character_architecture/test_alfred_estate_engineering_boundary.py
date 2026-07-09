from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "docs/character-architecture/Alfred_Estate_Engineering_Boundary_v0_1.md"
ACTIVE_PATHS = [
    ROOT / "docs/character-architecture/Alfred_Estate_Engineering_Boundary_v0_1.md",
    ROOT / "docs/character-architecture/CueMastery_Return_Gate_After_Resident_Standup.md",
    ROOT / "docs/residents/alfred/runtime/Alfred_Background_Operations_Integration_v0_1.md",
    ROOT / "docs/residents/helen/Helen_Resident_Profile_v0_1.md",
    ROOT / "docs/residents/helen/runtime/Helen_Background_Operations_Integration_v0_1.md",
    ROOT / "operations/departments/engineering/engineering_department_charter.md",
    ROOT / "operations/departments/engineering/cuemastery_execution_handoff.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_boundary_artifact_exists():
    assert BOUNDARY.is_file()


def test_boundary_states_alfred_estate_coordination_role():
    text = read(BOUNDARY)
    assert "Alfred worries about the Estate" in text
    assert "Chief of Staff for the Estate" in text
    assert "Estate coordination" in text


def test_boundary_states_alfred_does_not_own_cuemastery_execution():
    text = read(BOUNDARY)
    assert "Alfred does not own CueMastery execution" in text
    assert "must not be framed as directly executing, managing, or project-managing CueMastery work" in text


def test_boundary_states_engineering_owns_cuemastery_engineering_tasks():
    text = read(BOUNDARY)
    assert "CueMastery is an Engineering Department project/workstream" in text
    assert "Engineering Department is the institutional owner for CueMastery engineering execution" in text
    assert "takes on the engineering tasks associated with CueMastery" in text


def test_active_alfred_language_does_not_frame_direct_cuemastery_execution():
    forbidden = [
        "Alfred owns CueMastery",
        "Alfred owns CueMastery execution",
        "Alfred manages CueMastery",
        "Alfred project manages CueMastery",
        "Alfred executes CueMastery",
        "Alfred runs CueMastery development",
        "Alfred is responsible for CueMastery execution",
        "CueMastery is Alfred's project",
    ]
    for path in ACTIVE_PATHS:
        text = read(path)
        for phrase in forbidden:
            assert phrase not in text, (path, phrase)


def test_active_boundary_language_names_engineering_execution_and_alfred_coordination():
    combined = "\n".join(read(path) for path in ACTIVE_PATHS)
    assert "Engineering Department owns CueMastery engineering execution" in combined
    assert "Alfred may route attention and surface blockers" in combined
    assert "Engineering Department to take on CueMastery engineering work" in combined
