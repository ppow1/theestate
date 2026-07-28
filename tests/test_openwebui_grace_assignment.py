from estate.core.openwebui_grace_assignment import detect_grace_image_assignment


def test_openwebui_grace_model_recognizes_ordinary_image_assignment():
    message = "Grace, please generate a professional headshot of Evelyn for the Estate staff directory."
    assert detect_grace_image_assignment("estate/grace-grounded-test", message) is True


def test_other_models_and_non_assignments_do_not_enter_execution_path():
    assert detect_grace_image_assignment("estate/helen", "Please generate a headshot") is False
    assert detect_grace_image_assignment("estate/grace-grounded-test", "What is runtime readiness?") is False
