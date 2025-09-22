# Flutter Local Templates

This directory contains local fallback templates for Flutter projects when GitLab repositories are not accessible.

## Template Structure

- `app_template/` - Main Flutter application template (fallback for https://gitlab.com/omprussia/flutter/templates/app_template)
- `dbus_template/` - D-Bus plugin template (fallback for https://gitlab.com/omprussia/flutter/templates/dbus_template)
- `ffi_template/` - FFI plugin template (fallback for https://gitlab.com/omprussia/flutter/templates/ffi_template)
- `platform_channel_template/` - Platform channel plugin template (fallback for https://gitlab.com/omprussia/flutter/templates/platform_channel_template)
- `platform_interface_template/` - Platform interface template (fallback for https://gitlab.com/omprussia/flutter/templates/platform_interface_template)

## Usage

These templates are automatically used by `create_flutter_project` when:
1. Network connectivity issues prevent GitLab access
2. Repository authentication fails
3. Repository is temporarily unavailable

Each template should be a complete copy of the corresponding GitLab repository's `example` branch.

## Maintenance

To update templates:
1. Clone the latest version from GitLab
2. Copy contents (excluding .git) to the appropriate template directory
3. Ensure templates contain placeholder values that will be replaced during project creation:
   - `ApplicationTemplate` - will be replaced with actual application name
   - `ru.auroraos` - will be replaced with actual organization name