"""Aurora MCP Qt Prompts - QML enhancement and generation prompts."""

from .enhance_qml import enhance_qml_code

ALL_QT_PROMPTS = [
    enhance_qml_code,
]

__all__ = [
    "enhance_qml_code",
    "ALL_QT_PROMPTS",
]
