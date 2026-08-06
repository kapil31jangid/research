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
    assert len(concepts.json()) == 12
    graph = client("GET", "/curriculum/graph").json()
    assert len(graph["nodes"]) == 12
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
