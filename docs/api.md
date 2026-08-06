# API

Recommendation metadata includes `matching_offline_activity_ids` and
`offline_content_reason` for every decision. `selected_candidate_predicted_probability`
is the canonical ML value; `candidate_prediction_summary` contains bounded candidate
diagnostics. `predicted_correctness_probability` is a deprecated compatibility field
and new candidate-scored recommendations return it as `null`.

All endpoints return JSON. The service has no authentication in this local research-prototype phase.

Interaction decisions expose requested and actual adaptation paths, controller rules, resource and offline availability, model/fallback metadata, and estimated plus measured latency fields. These additive audit fields support reproducible simulated experiments.

Offline metadata is validated against seeded activity metadata rather than trusted directly from the client. The app shell does not imply educational content availability.

## Health

`GET /health` returns `{"status":"ok","service":"rapid-learn"}`.

## Learners

`POST /learners` accepts:

```json
{"name":"Asha","age_group":"10-12","grade":5,"preferred_language":"en","device_profile":"low-end"}
```

`GET /learners` lists local profiles. `GET /learners/{learner_id}` returns one profile.

`GET /learners/{learner_id}/state` creates missing per-concept state entries on first use and returns current mastery, dynamic retained mastery, uncertainty, evidence, and forgetting parameters. `GET /learners/{learner_id}/progress` returns the same state list with aggregate progress. These endpoints do not yet accept learner interactions; BKT state updates arrive in the adaptive interaction milestone.

`GET /learners/{learner_id}/learning-plan` returns currently eligible concepts, concepts requiring spaced review, and concepts blocked by prerequisites. `GET /questions/next?learner_id={learner_id}` returns a learner-safe diagnostic or spaced-review question; no correct answer is exposed.

## Resources

`GET /resources/current` reports local host resource measurements with safe battery and network fallbacks. `POST /resources/simulate` evaluates a supplied resource profile for reproducible research scenarios. For example, provide memory, CPU, battery, and network fields to receive normalised score, resource level, and offline status.

## Adaptive loop and recommendations

`POST /interactions` accepts a learner ID, question ID, answer, response time, hints, offline flag, and optional simulated device state. It validates correctness, updates BKT state and uncertainty, records mastery history, detects repeated misconception evidence, selects an adaptation path, stores a recommendation, and returns the explainable decision. `GET /interactions/{learner_id}` returns stored interaction summaries. `POST /recommendations/generate` creates a fresh ranked recommendation; `GET /recommendations/{learner_id}` returns recommendation history.

## Curriculum and questions

`GET /concepts`, `GET /concepts/{concept_id}`, and `GET /curriculum/graph` expose the seeded fractions curriculum. `GET /questions?concept_id=fraction_addition&limit=10` lists safe question data; correct answers are never sent by this read API. `GET /questions/{question_id}` returns one question.
