"""Dialog modules for the spelling trainer application.

This module provides backward compatibility by importing all dialog classes
from their new locations, allowing existing code to continue working while
the dialogs are organized into logical modules.
"""

# Import from new module locations to maintain backward compatibility
from ui.dialogs.auth.password_dialogs import ChangePasswordDialog
from ui.dialogs.settings.settings_dialogs import SettingsDialog
from ui.dialogs.statistics.statistics_dialogs import ProblemWordsDialog
from ui.dialogs.word_management.word_dialogs import WordManagerDialog, WordEditorDialog, CategoryMoveDialog
from ui.dialogs.import_export.data_dialogs import BulkImportDialog, ExportCategoriesDialog

# Define what gets imported with "from ui.dialogs import *"
__all__ = [
    'ChangePasswordDialog',
    'SettingsDialog', 
    'ProblemWordsDialog',
    'WordManagerDialog',
    'WordEditorDialog',
    'CategoryMoveDialog',
    'BulkImportDialog',
    'ExportCategoriesDialog'
]
