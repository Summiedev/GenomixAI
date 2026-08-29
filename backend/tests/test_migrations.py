from alembic import command


def test_migration_can_upgrade_from_empty_database(alembic_config, migrated_database) -> None:
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


def test_migration_can_downgrade_safely(alembic_config, migrated_database) -> None:
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
