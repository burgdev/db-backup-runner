"""Custom provider classes"""

from db_backup_runner.custom.provider._custom import CustomProvider

__all__ = ["CustomProvider"]

"""Custom backup providers need to be added here, this variable is imported in the [manager]()"""
BACKUP_PROVIDERS = [CustomProvider]
