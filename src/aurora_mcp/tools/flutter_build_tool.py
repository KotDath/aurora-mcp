"""
Copyright 2025 Daniil Markevich (KotDath)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from ..decorators import DevelopmentStatus, development_status

logger = logging.getLogger(__name__)


class FlutterBuildTool:
    """Flutter build tool for Aurora OS projects."""

    def __init__(self, aurora_home: Path):
        self.aurora_home = aurora_home
        self.flutter_path = aurora_home / "flutter"
        self.embedder_path = aurora_home / "flutter-embedder"

    @development_status(DevelopmentStatus.NOT_READY)
    async def build_project(
        self,
        project_path: str,
        target_arch: str = "armv7hl",
        build_type: str = "Release",
    ) -> dict[str, Any]:
        """Build Flutter project for Aurora OS.

        Args:
            project_path: Path to Flutter project directory
            target_arch: Target architecture (armv7hl, aarch64, i486)
            build_type: Build type (Debug/Release)

        Returns:
            Build result with status, output, and artifacts
        """
        try:
            project_dir = Path(project_path)
            if not project_dir.exists():
                return {
                    "success": False,
                    "error": f"Project directory not found: {project_path}",
                }

            # Check if it's a Flutter project
            pubspec_path = project_dir / "pubspec.yaml"
            if not pubspec_path.exists():
                return {
                    "success": False,
                    "error": "Not a Flutter project (pubspec.yaml not found)",
                }

            # Build Flutter bundle first
            bundle_result = await self._build_flutter_bundle(project_dir)
            if not bundle_result["success"]:
                return bundle_result

            # Build native Aurora OS app
            native_result = await self._build_native_app(
                project_dir, target_arch, build_type
            )

            return native_result

        except Exception as e:
            logger.error(f"Error building Flutter project: {e}")
            return {"success": False, "error": str(e)}

    async def _build_flutter_bundle(self, project_dir: Path) -> dict[str, Any]:
        """Build Flutter bundle."""
        try:
            # Run flutter build linux (as base)
            proc = await asyncio.create_subprocess_exec(
                "flutter",
                "build",
                "linux",
                "--release",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            stdout, _ = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": "Flutter bundle build failed",
                    "output": output,
                }

            bundle_path = project_dir / "build" / "linux" / "x64" / "release" / "bundle"

            return {"success": True, "bundle_path": str(bundle_path), "output": output}

        except Exception as e:
            return {"success": False, "error": f"Error building Flutter bundle: {e}"}

    async def _build_native_app(
        self, project_dir: Path, target_arch: str, bundle_path: str
    ) -> dict[str, Any]:
        """Build native Aurora OS app with Flutter embedder."""
        try:
            # Create Aurora OS build directory
            build_dir = project_dir / f"build-aurora-{target_arch}"
            build_dir.mkdir(exist_ok=True)

            # Copy Flutter bundle
            bundle_src = Path(bundle_path)
            bundle_dst = build_dir / "bundle"

            if bundle_dst.exists():
                import shutil

                shutil.rmtree(bundle_dst)

            import shutil

            shutil.copytree(bundle_src, bundle_dst)

            # Generate Aurora OS project files
            cmake_result = await self._generate_cmake_files(
                project_dir, build_dir, target_arch
            )
            if not cmake_result["success"]:
                return cmake_result

            # Build with CMake
            build_result = await self._build_cmake_project(build_dir, target_arch)

            return build_result

        except Exception as e:
            logger.error(f"Error building native app: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_cmake_files(
        self, project_dir: Path, build_dir: Path, target_arch: str
    ) -> dict[str, Any]:
        """Generate CMakeLists.txt for Aurora OS build."""
        try:
            # Read pubspec.yaml for project info
            import yaml

            pubspec_file = project_dir / "pubspec.yaml"

            with open(pubspec_file) as f:
                pubspec = yaml.safe_load(f)

            app_name = pubspec.get("name", "flutter_app")
            app_version = pubspec.get("version", "1.0.0").split("+")[0]

            # Generate CMakeLists.txt
            cmake_content = self._generate_cmake_content(
                app_name, app_version, target_arch
            )

            cmake_file = build_dir / "CMakeLists.txt"
            with open(cmake_file, "w") as f:
                f.write(cmake_content)

            # Generate main.cpp
            main_cpp = self._generate_main_cpp(app_name)
            main_file = build_dir / "main.cpp"
            with open(main_file, "w") as f:
                f.write(main_cpp)

            return {"success": True, "message": "CMake files generated successfully"}

        except Exception as e:
            return {"success": False, "error": f"Error generating CMake files: {e}"}

    def _generate_cmake_content(
        self, app_name: str, app_version: str, target_arch: str
    ) -> str:
        """Generate CMakeLists.txt content."""
        return f"""cmake_minimum_required(VERSION 3.16)
project({app_name} VERSION {app_version})

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(PkgConfig REQUIRED)
find_package(Qt5 REQUIRED COMPONENTS Core Gui Widgets)

# Flutter embedder
set(FLUTTER_EMBEDDER_PATH "/opt/aurora-os/flutter-embedder")
if(EXISTS "${{FLUTTER_EMBEDDER_PATH}}")
    include_directories("${{FLUTTER_EMBEDDER_PATH}}/include")
    link_directories("${{FLUTTER_EMBEDDER_PATH}}/lib")
endif()

# Sources
set(SOURCES
    main.cpp
)

# Executable
add_executable({app_name} ${{SOURCES}})

# Link libraries
target_link_libraries({app_name}
    Qt5::Core
    Qt5::Gui  
    Qt5::Widgets
    flutter_linux_gtk
)

# Install
install(TARGETS {app_name} DESTINATION /usr/bin)
install(DIRECTORY bundle/ DESTINATION /usr/share/{app_name})

# RPM packaging
set(CPACK_GENERATOR "RPM")
set(CPACK_PACKAGE_NAME "{app_name}")
set(CPACK_PACKAGE_VERSION "{app_version}")
set(CPACK_PACKAGE_DESCRIPTION "Flutter application for Aurora OS")
set(CPACK_PACKAGE_CONTACT "developer@example.com")
set(CPACK_RPM_PACKAGE_ARCHITECTURE "{target_arch}")

include(CPack)
"""

    def _generate_main_cpp(self, app_name: str) -> str:
        """Generate main.cpp content."""
        return f"""#include <QApplication>
#include <QWidget>
#include <QVBoxLayout>
#include <flutter_linux/flutter_linux.h>

int main(int argc, char *argv[])
{{
    QApplication app(argc, argv);
    app.setApplicationName("{app_name}");
    
    // Initialize Flutter
    fl_register_plugins(nullptr);
    
    QWidget window;
    window.setWindowTitle("{app_name}");
    window.resize(800, 600);
    
    QVBoxLayout *layout = new QVBoxLayout(&window);
    
    // Flutter view would be embedded here
    // This is a placeholder implementation
    
    window.show();
    
    return app.exec();
}}
"""

    async def _build_cmake_project(
        self, build_dir: Path, target_arch: str
    ) -> dict[str, Any]:
        """Build CMake project for Aurora OS."""
        try:
            commands = [
                # Configure
                [
                    "cmake",
                    "-DCMAKE_BUILD_TYPE=Release",
                    "-DCMAKE_TOOLCHAIN_FILE=/usr/share/cmake/aurora-platform-toolchain.cmake",
                    ".",
                ],
                # Build
                ["cmake", "--build", ".", "--config", "Release"],
                # Package
                ["cpack", "-G", "RPM"],
            ]

            outputs = []
            for cmd in commands:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=build_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )

                stdout, _ = await proc.communicate()
                output = stdout.decode("utf-8", errors="replace")
                outputs.append(output)

                if proc.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Command failed: {' '.join(cmd)}",
                        "output": output,
                    }

            # Find built artifacts
            artifacts = []
            for pattern in ["*.rpm", "*.deb"]:
                artifacts.extend([str(p) for p in build_dir.glob(pattern)])

            return {
                "success": True,
                "output": "\\n".join(outputs),
                "artifacts": artifacts,
                "build_dir": str(build_dir),
            }

        except Exception as e:
            return {"success": False, "error": f"Error building CMake project: {e}"}

    @development_status(DevelopmentStatus.NOT_READY)
    async def setup_embedder(self, project_path: str) -> dict[str, Any]:
        """Set up Flutter embedder for Aurora OS project.

        Args:
            project_path: Path to project directory

        Returns:
            Setup result with status and information
        """
        try:
            project_dir = Path(project_path)
            embedder_dir = project_dir / "aurora"

            if not embedder_dir.exists():
                embedder_dir.mkdir(parents=True)

            # Copy embedder files if available
            if self.embedder_path.exists():
                # Implementation would copy necessary embedder files
                return {
                    "success": True,
                    "message": "Flutter embedder setup completed",
                    "embedder_path": str(embedder_dir),
                }
            else:
                return {
                    "success": False,
                    "error": "Flutter embedder not found. Please install Aurora Flutter SDK",
                }

        except Exception as e:
            logger.error(f"Error setting up embedder: {e}")
            return {"success": False, "error": str(e)}
