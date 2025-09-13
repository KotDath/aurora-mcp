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

#THIS TOOL UNDER DEVELOPMENT

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from ..decorators import development_status, DevelopmentStatus
logger = logging.getLogger(__name__)


class RPMPackagingTool:
    """RPM packaging tool for Aurora OS applications."""
    
    def __init__(self, aurora_home: Path):
        self.aurora_home = aurora_home
        self.rpmbuild_root = aurora_home / "rpmbuild"
        self._setup_rpmbuild_dirs()
        
    def _setup_rpmbuild_dirs(self):
        """Setup RPM build directory structure."""
        for subdir in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
            (self.rpmbuild_root / subdir).mkdir(parents=True, exist_ok=True)
    
    @development_status(DevelopmentStatus.NOT_READY)
    async def create_package(
        self,
        spec_file: str,
        source_dir: str,
        target_arch: str = "armv7hl"
    ) -> Dict[str, Any]:
        """Create RPM package from spec file and sources.
        
        Args:
            spec_file: Path to .spec file
            source_dir: Path to source directory
            target_arch: Target architecture for package
        
        Returns:
            Package creation result with RPM file path
        """
        try:
            spec_path = Path(spec_file)
            if not spec_path.exists():
                return {
                    "success": False,
                    "error": f"Spec file not found: {spec_file}"
                }
            
            source_path = Path(source_dir)
            if not source_path.exists():
                return {
                    "success": False,
                    "error": f"Source directory not found: {source_dir}"
                }
            
            # Setup rpmbuild directory structure
            await self._setup_rpmbuild_dirs()
            
            # Create source tarball
            tarball_result = await self._create_source_tarball(source_path, spec_path)
            if not tarball_result["success"]:
                return tarball_result
            
            # Build RPM
            rpm_result = await self._build_rpm(spec_path, target_arch)
            
            return rpm_result
            
        except Exception as e:
            logger.error(f"Error creating RPM package: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_source_tarball(self, source_dir: Path) -> Dict[str, Any]:
        """Create source tarball for RPM build."""
        try:
            # Get project name from directory
            project_name = source_dir.name
            
            # Create tarball
            tarball_path = self.rpmbuild_root / "SOURCES" / f"{project_name}.tar.gz"
            
            proc = await asyncio.create_subprocess_exec(
                "tar", "-czf", str(tarball_path), "-C", str(source_dir.parent), source_dir.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to create tarball: {stderr.decode()}"
                }
            
            return {
                "success": True,
                "tarball": str(tarball_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating source tarball: {e}"
            }
    
    async def _build_rpm(self, spec_file: Path, output_dir: Optional[str]) -> Dict[str, Any]:
        """Build RPM package using rpmbuild."""
        try:
            # Prepare rpmbuild command
            cmd = [
                "rpmbuild",
                "--define", f"_topdir {self.rpmbuild_root}",
                "-bb",  # Build binary package
                str(spec_file)
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            stdout, _ = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace')
            
            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": "RPM build failed",
                    "output": output
                }
            
            # Find generated RPMs
            rpms_dir = self.rpmbuild_root / "RPMS"
            rpm_files = []
            for rpm_file in rpms_dir.rglob("*.rpm"):
                rpm_files.append(str(rpm_file))
            
            # Copy to output directory if specified
            if output_dir and rpm_files:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                import shutil
                copied_files = []
                for rpm_file in rpm_files:
                    dest = output_path / Path(rpm_file).name
                    shutil.copy2(rpm_file, dest)
                    copied_files.append(str(dest))
                
                rpm_files = copied_files
            
            return {
                "success": True,
                "output": output,
                "rpm_files": rpm_files,
                "rpmbuild_dir": str(self.rpmbuild_root)
            }
            
        except Exception as e:
            logger.error(f"Error building RPM: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @development_status(DevelopmentStatus.NOT_READY)
    async def sign_package(
        self,
        rpm_file: str,
        key_id: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sign RPM package with GPG key.
        
        Args:
            rpm_file: Path to RPM file to sign
            key_id: GPG key ID to use for signing
            passphrase: GPG key passphrase
        
        Returns:
            Signing result with signature verification
        """
        try:
            rpm_path = Path(rpm_file)
            if not rpm_path.exists():
                return {
                    "success": False,
                    "error": f"RPM file not found: {rpm_file}"
                }
            
            # Build rpm --addsign command
            cmd = ["rpm", "--addsign", str(rpm_path)]
            
            env = os.environ.copy()
            if key_id:
                env["GPG_KEY_ID"] = key_id
            if passphrase:
                env["GPG_PASSPHRASE"] = passphrase
            
            # Execute signing
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )
            
            stdout, _ = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace')
            
            if proc.returncode == 0:
                # Verify signature
                verify_result = await self._verify_signature(rpm_path)
                
                return {
                    "success": True,
                    "rpm_file": str(rpm_path),
                    "signed": True,
                    "verification": verify_result,
                    "output": output
                }
            else:
                return {
                    "success": False,
                    "error": "Package signing failed",
                    "output": output
                }
                
        except Exception as e:
            logger.error(f"Error signing package: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _verify_signature(self, rpm_file: Path) -> Dict[str, Any]:
        """Verify RPM package signature."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "rpm", "--checksig", str(rpm_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace')
            
            # Check if signature is present and valid
            if "OK" in output and "gpg" in output.lower():
                return {
                    "success": True,
                    "output": output
                }
            else:
                return {
                    "success": False,
                    "output": output
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @development_status(DevelopmentStatus.NOT_READY)
    async def validate_package(self, rpm_file: str) -> Dict[str, Any]:
        """Validate RPM package integrity and metadata.
        
        Args:
            rpm_file: Path to RPM file to validate
        
        Returns:
            Validation result with package information
        """
        try:
            rpm_path = Path(rpm_file)
            if not rpm_path.exists():
                return {
                    "success": False,
                    "error": f"RPM file not found: {rpm_file}"
                }
            
            # Get package information
            info_result = await self._get_package_info(rpm_path)
            if not info_result["success"]:
                return info_result
            
            # List package files
            files_result = await self._list_package_files(rpm_path)
            if not files_result["success"]:
                return files_result
            
            # Check dependencies
            deps_result = await self._check_dependencies(rpm_path)
            if not deps_result["success"]:
                return deps_result
            
            # Verify signature if present
            sig_result = await self._verify_signature(rpm_path)
            
            return {
                "success": True,
                "rpm_file": str(rpm_path),
                "package_info": info_result["info"],
                "files": files_result["files"],
                "dependencies": deps_result["dependencies"],
                "signature": sig_result,
                "valid": True
            }
            
        except Exception as e:
            logger.error(f"Error validating package: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_package_info(self, rpm_file: Path) -> Dict[str, Any]:
        """Get RPM package information."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "rpm", "-qip", str(rpm_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode()
                }
            
            output = stdout.decode('utf-8', errors='replace')
            return {
                "success": True,
                "info": output
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_package_files(self, rpm_file: Path) -> Dict[str, Any]:
        """List files in RPM package."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "rpm", "-qlp", str(rpm_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode()
                }
            
            files = stdout.decode('utf-8', errors='replace').strip().split('\n')
            return {
                "success": True,
                "files": files,
                "file_count": len(files)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_dependencies(self, rpm_file: Path) -> Dict[str, Any]:
        """Check RPM package dependencies."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "rpm", "-qRp", str(rpm_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode()
                }
            
            deps = stdout.decode('utf-8', errors='replace').strip().split('\n')
            deps = [d.strip() for d in deps if d.strip()]
            
            return {
                "success": True,
                "requires": deps,
                "dependency_count": len(deps)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }