# API

All endpoints return JSON. The service has no authentication in this local research-prototype phase.

## Health

`GET /health` returns `{"status":"ok","service":"rapid-learn"}`.

## Learners

`POST /learners` accepts:

```json
{"name":"Asha","age_group":"10-12","grade":5,"preferred_language":"en","device_profile":"low-end"}
```

`GET /learners` lists local profiles. `GET /learners/{learner_id}` returns one profile.

## Curriculum and questions

`GET /concepts`, `GET /concepts/{concept_id}`, and `GET /curriculum/graph` expose the seeded fractions curriculum. `GET /questions?concept_id=fraction_addition&limit=10` lists safe question data; correct answers are never sent by this read API. `GET /questions/{question_id}` returns one question.

