from sqlalchemy import create_engine, inspect

from app.database.compatibility import apply_sqlite_compatibility_migrations


def test_sqlite_compatibility_migration_is_additive_and_idempotent() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE learning_activities (id VARCHAR(120) PRIMARY KEY)")
        connection.exec_driver_sql(
            "CREATE TABLE learner_concept_states (id VARCHAR(36) PRIMARY KEY)"
        )
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
    engine.dispose()
