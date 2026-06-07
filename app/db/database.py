from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import config

engine = create_engine(
    config.database_url,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def _rename_column_if_needed(connection, table_columns, table_name, old_name, new_name):
    if new_name not in table_columns and old_name in table_columns:
        connection.execute(
            text(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")
        )


def ensure_schema_compatibility():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    column_names_by_table = {
        table_name: {
            column["name"] for column in inspector.get_columns(table_name)
        }
        for table_name in table_names
    }

    with engine.begin() as connection:
        _rename_column_if_needed(
            connection,
            column_names_by_table.get("collections", set()),
            "collections",
            "name",
            "collection_name",
        )
        _rename_column_if_needed(
            connection,
            column_names_by_table.get("collections", set()),
            "collections",
            "description_uri",
            "data_description_uri",
        )

        patient_columns = column_names_by_table.get("patients", set())
        for old_name, new_name in {
            "id": "patient_id",
            "sex": "patient_sex",
            "age": "patient_age",
        }.items():
            _rename_column_if_needed(
                connection, patient_columns, "patients", old_name, new_name
            )

        study_columns = column_names_by_table.get("studies", set())
        for old_name, new_name in {
            "instance_uid": "study_instance_uid",
            "collection": "collection_name_study",
            "date": "study_date",
            "description": "study_description",
            "patient_id": "patient_id_study",
        }.items():
            _rename_column_if_needed(
                connection, study_columns, "studies", old_name, new_name
            )

        series_columns = column_names_by_table.get("series", set())
        for old_name, new_name in {
            "instance_uid": "series_instance_uid",
            "study_instance_uid": "study_instance_uid_series",
            "body_part": "body_part_examined",
        }.items():
            _rename_column_if_needed(
                connection, series_columns, "series", old_name, new_name
            )
