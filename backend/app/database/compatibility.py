"""Safe additive compatibility updates for pre-migration-framework SQLite databases."""

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

_SQLITE_ADDITIVE_COLUMNS: dict[str, dict[str, str]] = {
    "learner_concept_states": {
        "response_time_count": "INTEGER NOT NULL DEFAULT 0",
        "response_time_m2": "FLOAT NOT NULL DEFAULT 0.0",
    },
    "learning_activities": {
        "is_active": "BOOLEAN NOT NULL DEFAULT 1",
        "deprecated_at": "DATETIME",
        "deprecation_reason": "TEXT",
    },
    "recommendations": {
        "requested_adaptation_path": "VARCHAR(60) NOT NULL DEFAULT ''",
        "fallback_used": "BOOLEAN NOT NULL DEFAULT 0",
        "fallback_reason": "TEXT",
        "ml_model_available": "BOOLEAN NOT NULL DEFAULT 0",
        "model_version": "VARCHAR(40)",
        "predicted_correctness_probability": "FLOAT",
        "selected_candidate_predicted_probability": "FLOAT",
        "candidate_prediction_summary": "TEXT NOT NULL DEFAULT '[]'",
        "triggered_rules": "TEXT NOT NULL DEFAULT '[]'",
        "rejected_paths": "TEXT NOT NULL DEFAULT '[]'",
        "offline_content_available": "BOOLEAN NOT NULL DEFAULT 0",
        "matching_offline_activity_ids": "TEXT NOT NULL DEFAULT '[]'",
        "offline_content_reason": "TEXT",
        "measured_controller_latency_ms": "FLOAT NOT NULL DEFAULT 0.0",
        "measured_recommendation_latency_ms": "FLOAT NOT NULL DEFAULT 0.0",
        "measured_total_adaptive_latency_ms": "FLOAT NOT NULL DEFAULT 0.0",
        "controller_mode": "VARCHAR(60) NOT NULL DEFAULT 'deterministic'",
    },
}


def apply_sqlite_compatibility_migrations(engine: Engine) -> None:
    """Add known nullable/defaulted columns without deleting existing local data."""
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table, columns in _SQLITE_ADDITIVE_COLUMNS.items():
            if table not in existing_tables:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table)}
            for column, definition in columns.items():
                if column not in existing_columns:
                    connection.exec_driver_sql(
                        f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}'
                    )
            if table == "recommendations":
                connection.exec_driver_sql(
                    "UPDATE recommendations SET requested_adaptation_path = adaptation_path "
                    "WHERE requested_adaptation_path = ''"
                )
