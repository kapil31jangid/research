def test_health(client):
    response = client("GET", "/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_learner(client):
    created = client("POST", "/learners", json={"name": "Asha", "age_group": "10-12", "grade": 5})
    assert created.status_code == 201
    learner = created.json()
    assert learner["name"] == "Asha"
    assert client("GET", "/learners").json()[0]["id"] == learner["id"]


def test_seeded_curriculum_and_graph(client):
    concepts = client("GET", "/concepts")
    assert concepts.status_code == 200
    assert len(concepts.json()) == 16
    graph = client("GET", "/curriculum/graph").json()
    assert len(graph["nodes"]) == 16
    assert {edge["source"] for edge in graph["edges"]} >= {"whole_numbers"}


def test_questions_hide_correct_answer(client):
    questions = client("GET", "/questions?concept_id=fraction_addition&limit=10")
    assert questions.status_code == 200
    assert len(questions.json()) == 8
    assert "correct_answer" not in questions.json()[0]


def test_learner_state_and_progress_initialise_all_concepts(client):
    learner = client(
        "POST", "/learners", json={"name": "Ravi", "age_group": "10-12", "grade": 5}
    ).json()
    states = client("GET", f"/learners/{learner['id']}/state")
    assert states.status_code == 200
    assert len(states.json()) == 12
    assert states.json()[0]["mastery_probability"] == 0.2
    progress = client("GET", f"/learners/{learner['id']}/progress")
    assert progress.status_code == 200
    assert progress.json()["concept_count"] == 12
    assert progress.json()["average_uncertainty"] == 1.0


def test_learning_plan_and_diagnostic_question_respect_prerequisites(client):
    learner = client(
        "POST", "/learners", json={"name": "Meera", "age_group": "10-12", "grade": 5}
    ).json()
    plan = client("GET", f"/learners/{learner['id']}/learning-plan")
    assert plan.status_code == 200
    assert plan.json()["ready_concept_ids"] == ["whole_numbers"]
    assert "fraction_addition" in plan.json()["blocked_concept_ids"]
    next_question = client("GET", f"/questions/next?learner_id={learner['id']}")
    assert next_question.status_code == 200
    assert next_question.json()["selection_type"] == "diagnostic_assessment"
    assert next_question.json()["concept_id"] == "whole_numbers"


def test_resource_simulation_returns_explainable_resource_level(client):
    response = client(
        "POST",
        "/resources/simulate",
        json={
            "available_memory_mb": 50,
            "total_memory_mb": 1_000,
            "cpu_percent": 95,
            "battery_percent": 5,
            "network_available": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["offline"] is True
    assert response.json()["level"] == "critical"


def test_interaction_runs_adaptive_loop_and_persists_recommendation(client):
    learner = client(
        "POST", "/learners", json={"name": "Ira", "age_group": "10-12", "grade": 5}
    ).json()
    response = client(
        "POST",
        "/interactions",
        json={
            "learner_id": learner["id"],
            "question_id": "whole_numbers_01",
            "submitted_answer": "19",
            "response_time_ms": 2_000,
            "device_resource_state": {
                "available_memory_mb": 600,
                "total_memory_mb": 1_000,
                "cpu_percent": 20,
                "battery_percent": 70,
                "network_available": True,
            },
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["interaction_result"]["correct"] is True
    assert body["learner_state"]["attempts"] == 1
    assert body["decision"]["selected_activity_id"]
    assert body["explanation"]
    assert client("GET", f"/interactions/{learner['id']}").json()[0]["correct"] is True
    assert len(client("GET", f"/recommendations/{learner['id']}").json()) == 1


def test_repeated_matching_errors_trigger_persisted_misconception_remediation(client):
    learner = client(
        "POST", "/learners", json={"name": "Nia", "age_group": "10-12", "grade": 5}
    ).json()
    payload = {
        "learner_id": learner["id"],
        "question_id": "fraction_addition_01",
        "submitted_answer": "3/8",
        "response_time_ms": 1000,
        "device_resource_state": {
            "available_memory_mb": 800,
            "total_memory_mb": 1000,
            "cpu_percent": 10,
            "battery_percent": 90,
            "network_available": True,
        },
    }
    assert (
        client("POST", "/interactions", json=payload).json()["misconception"]["detected"] is False
    )
    response = client("POST", "/interactions", json=payload).json()
    assert response["misconception"]["id"] == "adds_denominators"
    assert response["decision"]["adaptation_path"] == "misconception_remediation"
    assert response["decision"]["selected_activity_id"] == "visual_common_denominator_demo"


def test_cross_concept_remediation_uses_rule_owned_activity(client):
    learner = client(
        "POST", "/learners", json={"name": "Adi", "age_group": "10-12", "grade": 5}
    ).json()
    payload = {
        "learner_id": learner["id"],
        "question_id": "improper_fractions_01",
        "submitted_answer": "0",
        "response_time_ms": 1000,
        "device_resource_state": {
            "available_memory_mb": 800,
            "total_memory_mb": 1000,
            "cpu_percent": 10,
            "battery_percent": 90,
            "network_available": True,
        },
    }
    assert client("POST", "/interactions", json=payload).status_code == 201
    response = client("POST", "/interactions", json=payload)
    assert response.status_code == 201
    decision = response.json()["decision"]
    assert decision["adaptation_path"] == "misconception_remediation"
    assert decision["selected_activity_id"] == "conversion_steps"
    assert decision["selected_concept_id"] == "mixed_numbers"
