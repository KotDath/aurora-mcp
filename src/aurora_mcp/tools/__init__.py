"""Aurora MCP Tools - Development tools for Aurora OS."""

# Qt tools
from .conan.create_package import create_conan_package

# Conan tools
from .conan.install_dependencies import install_conan_dependencies

# Flutter tools
from .flutter.build_project import build_flutter_project
from .flutter.create_project import create_flutter_project
from .flutter.setup_embedder import setup_flutter_embedder
from .qt.build_project import build_qt_project
from .qt.configure_environment import configure_qt_environment
from .qt.create_project import create_qt_project
from .qt.enhance_qml import enhance_qml_code
from .qt.figma_to_qml import figma_to_qml
from .qt.list_build_tools import list_build_tools
from .qt.list_targets import list_qt_targets

# RPM tools
from .rpm.create_package import create_rpm_package
from .rpm.sign_package import sign_rpm_package
from .rpm.validate_package import validate_rpm_package
from .server.check_environment import check_aurora_environment

# Server tools
from .server.info import aurora_mcp_info

# Export all tools for automatic registration
ALL_TOOLS = [
    # Qt tools - READY
    build_qt_project,
    create_qt_project,
    # Flutter tools - READY
    create_flutter_project,
    # Qt tools - NOT READY (commented out)
    # configure_qt_environment,
    # figma_to_qml,
    # enhance_qml_code,
    # list_qt_targets,
    # list_build_tools,
    # Flutter tools - NOT READY (commented out)
    # build_flutter_project,
    # setup_flutter_embedder,
    # RPM tools - NOT READY (commented out)
    # create_rpm_package,
    # sign_rpm_package,
    # validate_rpm_package,
    # Conan tools - NOT READY (commented out)
    # install_conan_dependencies,
    # create_conan_package,
    # Server tools - NOT READY (commented out)
    # aurora_mcp_info,
    # check_aurora_environment,
]

__all__ = [
    # READY Functions
    "build_qt_project",
    "create_qt_project",
    "figma_to_qml",
    "enhance_qml_code",
    "create_flutter_project",
    # NOT READY Functions (commented out but available for import)
    "configure_qt_environment",
    "list_qt_targets",
    "list_build_tools",
    "build_flutter_project",
    "setup_flutter_embedder",
    "create_rpm_package",
    "sign_rpm_package",
    "validate_rpm_package",
    "install_conan_dependencies",
    "create_conan_package",
    "aurora_mcp_info",
    "check_aurora_environment",
    # Collection
    "ALL_TOOLS",
]
