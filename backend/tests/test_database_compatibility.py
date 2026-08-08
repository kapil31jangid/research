from sqlalchemy import create_engine, inspect

from app.database.compatibility import apply_sqlite_compatibility_migrations


def test_sqlite_compatibility_migration_is_additive_and_idempotent() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE learning_activities (id VARCHAR(120) PRIMARY KEY)")
        connection.exec_driver_sql(
            "CREATE TABLE learner_concept_states (id VARCHAR(36) PRIMARY KEY)"
        )
        connection.exec_driver_sql("CREATE TABLE concepts (id VARCHAR(80) PRIMARY KEY)")
        connection.exec_driver_sql(
            "CREATE TABLE learners (id VARCHAR(36) PRIMARY KEY, name VARCHAR(120))"
        )
        connection.exec_driver_sql("INSERT INTO concepts (id) VALUES ('fraction_meaning')")
        connection.exec_driver_sql("INSERT INTO learners (id, name) VALUES ('legacy', 'Asha')")
    apply_sqlite_compatibility_migrations(engine)
    apply_sqlite_compatibility_migrations(engine)
    activity_columns = {
        column["name"] for column in inspect(engine).get_columns("learning_activities")
    }
    state_columns = {
        column["name"] for column in inspect(engine).get_columns("learner_concept_states")
    }
    assert {"is_active", "deprecated_at", "deprecation_reason"} <= activity_columns
    assert {"response_time_count", "response_time_m2"} <= state_columns
    with engine.connect() as connection:
        concept = connection.exec_driver_sql(
            "SELECT chapter_id FROM concepts WHERE id = 'fraction_meaning'"
        ).one()
        learner = connection.exec_driver_sql(
            "SELECT class_level, active_subject_id, active_chapter_id "
            "FROM learners WHERE id = 'legacy'"
        ).one()
    assert concept.chapter_id == "ncert-c5-math-fractions"
    assert learner.class_level == 5
    assert learner.active_subject_id == "ncert-c5-mathematics"
    assert learner.active_chapter_id == "ncert-c5-math-fractions"
    engine.dispose()
