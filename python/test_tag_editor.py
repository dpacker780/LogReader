"""Test the Tag Editor dialog."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from python.tag_editor_dialog import TagEditorDialog
from python.config import ConfigManager


def main():
    """Test Tag Editor dialog."""
    app = QApplication(sys.argv)

    # Clean config for testing
    ConfigManager.delete_config()
    ConfigManager._config = None

    # Load default config
    config = ConfigManager.load_config()
    print(f"Initial tags: {[tag.name for tag in config.tags]}")

    # Show Tag Editor
    dialog = TagEditorDialog()
    result = dialog.exec()

    if result:
        print("\nDialog accepted!")
        tags = dialog.get_tags()
        print(f"Final tags: {[(tag.name, tag.color) for tag in tags]}")

        # Save tags
        ConfigManager.save_tags(tags)
        print("\nTags saved to config.")
    else:
        print("\nDialog cancelled.")

    # Show final config
    config2 = ConfigManager.load_config()
    print(f"\nConfig after dialog:")
    for tag in config2.tags:
        print(f"  {tag.name:10s} {tag.color}")


if __name__ == "__main__":
    main()
