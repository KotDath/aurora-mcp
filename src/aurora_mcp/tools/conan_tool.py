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
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..decorators import development_status, DevelopmentStatus
logger = logging.getLogger(__name__)


class ConanTool:
    """Conan package manager integration for Aurora OS C++ projects."""
    
    def __init__(self, aurora_home: Path):
        self.aurora_home = aurora_home
        self.conan_home = aurora_home / "conan"
        self.profiles_dir = self.conan_home / "profiles"
        self._setup_conan_environment()
        
    def _setup_conan_environment(self):
        """Setup Conan environment directories."""
        self.conan_home.mkdir(exist_ok=True)
        self.profiles_dir.mkdir(exist_ok=True)
        
    @development_status(DevelopmentStatus.NOT_READY)
    async def install_dependencies(
        self,
        conanfile_path: str,
        profile: str = "aurora",
        build_type: str = "Release",
        settings: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Install dependencies using Conan.
        
        Args:
            conanfile_path: Path to conanfile.txt or conanfile.py
            profile: Conan profile to use
            build_type: Build type (Debug/Release)
            settings: Additional Conan settings
        
        Returns:
            Installation result with status and package information
        """
        try:
            conanfile = Path(conanfile_path)
            if not conanfile.exists():
                return {
                    "success": False,
                    "error": f"Conanfile not found: {conanfile_path}"
                }
            
            # Get profile path
            profile_result = await self._get_profile_path(profile)
            if not profile_result["success"]:
                return profile_result
            
            profile_path = profile_result["profile_path"]
            
            # Build conan install command
            cmd = [
                "conan", "install",
                str(conanfile),
                f"--profile={profile_path}",
                f"--settings=build_type={build_type}",
                "--build=missing"
            ]
            
            # Add additional settings
            if settings:
                for key, value in settings.items():
                    cmd.append(f"--settings={key}={value}")
            
            # Execute conan install
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=self._get_conan_env()
            )
            
            stdout, _ = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace')
            
            if proc.returncode == 0:
                # Parse installation output
                packages = self._parse_install_output(output)
                
                return {
                    "success": True,
                    "packages_installed": packages,
                    "profile_used": profile,
                    "build_type": build_type,
                    "output": output
                }
            else:
                return {
                    "success": False,
                    "error": "Conan install failed",
                    "output": output
                }
                
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @development_status(DevelopmentStatus.NOT_READY)
    async def create_package(
        self,
        recipe_path: str,
        package_ref: str,
        profile: str = "aurora"
    ) -> Dict[str, Any]:
        """Create a Conan package.
        
        Args:
            recipe_path: Path to conanfile.py recipe
            package_ref: Package reference (name/version@user/channel)
            profile: Conan profile to use
        
        Returns:
            Package creation result
        """
        try:
            recipe = Path(recipe_path)
            if not recipe.exists():
                return {
                    "success": False,
                    "error": f"Recipe not found: {recipe_path}"
                }
            
            # Get profile path
            profile_result = await self._get_profile_path(profile)
            if not profile_result["success"]:
                return profile_result
            
            profile_path = profile_result["profile_path"]
            
            # Build conan create command
            cmd = [
                "conan", "create",
                str(recipe),
                package_ref,
                f"--profile={profile_path}"
            ]
            
            # Execute conan create
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=self._get_conan_env()
            )
            
            stdout, _ = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace')
            
            if proc.returncode == 0:
                return {
                    "success": True,
                    "package_ref": package_ref,
                    "profile_used": profile,
                    "output": output
                }
            else:
                return {
                    "success": False,
                    "error": "Conan create failed",
                    "output": output
                }
                
        except Exception as e:
            logger.error(f"Error creating package: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @development_status(DevelopmentStatus.NOT_READY)
    async def search_packages(
        self,
        pattern: str,
        remote: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for Conan packages.
        
        Args:
            pattern: Search pattern for package names
            remote: Optional remote to search in
        
        Returns:
            Search results with matching packages
        """
        try:
            cmd = ["conan", "search", pattern]
            
            if remote:
                cmd.extend(["-r", remote])
            
            # Execute conan search
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=self._get_conan_env()
            )
            
            stdout, _ = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace')
            
            if proc.returncode == 0:
                # Parse search results
                packages = []
                lines = output.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if '/' in line and '@' in line:
                        packages.append(line)
                
                return {
                    "success": True,
                    "packages": packages,
                    "pattern": pattern,
                    "remote": remote,
                    "output": output
                }
            else:
                return {
                    "success": False,
                    "error": "Conan search failed",
                    "output": output
                }
                
        except Exception as e:
            logger.error(f"Error searching packages: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @development_status(DevelopmentStatus.NOT_READY)
    async def create_aurora_profile(self, arch: str = "armv7hl") -> Dict[str, Any]:
        """Create Aurora OS Conan profile.
        
        Args:
            arch: Target architecture
        
        Returns:
            Profile creation result
        """
        try:
            profile_name = f"aurora-{arch}"
            profile_path = self.profiles_dir / profile_name
            
            # Ensure profiles directory exists
            self.profiles_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate profile content
            profile_content = self._generate_aurora_profile_content(arch)
            
            # Write profile
            with open(profile_path, 'w') as f:
                f.write(profile_content)
            
            return {
                "success": True,
                "profile_name": profile_name,
                "profile_path": str(profile_path),
                "architecture": arch
            }
            
        except Exception as e:
            logger.error(f"Error creating Aurora profile: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_aurora_profile_content(self) -> str:
        """Generate Conan profile content for Aurora OS."""
        return """[settings]
os=Linux
os_build=Linux
arch=armv7hf
arch_build=x86_64
compiler=gcc
compiler.version=9
compiler.libcxx=libstdc++11
build_type=Release

[options]

[build_requires]

[env]
CC=/usr/bin/arm-aurora-linux-gnueabihf-gcc
CXX=/usr/bin/arm-aurora-linux-gnueabihf-g++
PKG_CONFIG_PATH=/usr/lib/pkgconfig
CMAKE_TOOLCHAIN_FILE=/usr/share/cmake/aurora-platform-toolchain.cmake
"""
    
    async def _get_conan_env(self) -> Dict[str, str]:
        """Get Conan environment variables."""
        import os
        env = os.environ.copy()
        env["CONAN_USER_HOME"] = str(self.conan_home)
        return env
    
    async def _get_profile_path(self, profile_name: str) -> Optional[Path]:
        """Get path to Conan profile."""
        profile_path = self.profiles_dir / profile_name
        if profile_path.exists():
            return profile_path
        
        # Try system profiles
        try:
            proc = await asyncio.create_subprocess_exec(
                "conan", "profile", "path", profile_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                system_profile = Path(stdout.decode().strip())
                if system_profile.exists():
                    return system_profile
                    
        except Exception:
            pass
        
        return None
    
    async def _parse_install_output(self, output: str) -> Dict[str, Any]:
        """Parse conan install output for package information."""
        info = {"packages": []}
        
        # Look for installed packages in output
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Installing') or line.startswith('Requirement'):
                # Extract package name/version
                parts = line.split()
                if len(parts) >= 2:
                    package_info = parts[1].rstrip(':')
                    info["packages"].append(package_info)
        
        return info
    
    @development_status(DevelopmentStatus.NOT_READY)
    async def list_installed_packages(self) -> Dict[str, Any]:
        """List installed Conan packages.
        
        Returns:
            List of installed packages
        """
        try:
            cmd = ["conan", "search"]
            
            # Execute conan search
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=self._get_conan_env()
            )
            
            stdout, _ = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace')
            
            if proc.returncode == 0:
                # Parse installed packages
                packages = []
                lines = output.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if '/' in line and '@' in line:
                        packages.append({
                            "reference": line,
                            "name": line.split('/')[0],
                            "version": line.split('/')[1].split('@')[0]
                        })
                
                return {
                    "success": True,
                    "packages": packages,
                    "count": len(packages)
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to list packages",
                    "output": output
                }
                
        except Exception as e:
            logger.error(f"Error listing packages: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @development_status(DevelopmentStatus.NOT_READY)
    async def remove_package(self, package_ref: str) -> Dict[str, Any]:
        """Remove a Conan package.
        
        Args:
            package_ref: Package reference to remove
        
        Returns:
            Removal result
        """
        try:
            cmd = ["conan", "remove", package_ref, "-f"]
            
            # Execute conan remove
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=self._get_conan_env()
            )
            
            stdout, _ = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace')
            
            if proc.returncode == 0:
                return {
                    "success": True,
                    "removed_package": package_ref,
                    "output": output
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to remove package",
                    "package_ref": package_ref,
                    "output": output
                }
                
        except Exception as e:
            logger.error(f"Error removing package: {e}")
            return {
                "success": False,
                "error": str(e)
            }