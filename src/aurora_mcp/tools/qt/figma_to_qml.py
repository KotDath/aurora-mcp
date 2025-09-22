"""Main MCP tool for converting Figma designs to QML pages and components."""

import json
from pathlib import Path
from typing import Any


def figma_to_qml(
    figma_file_url: str,
    access_token: str,
    workspace_dir: str,
    enhancement_types: list[str] = None,
) -> str:
    """
    Convert Figma design to QML pages and components for Aurora OS.

    This tool fetches a Figma design file and converts it to basic QML structure.
    Generated files are marked for enhancement - use enhance_qml_code tool to apply
    advanced features like auto-layout, components, effects, animations, and responsive design.

    The tool integrates with existing Aurora OS project structure:
    - Saves pages to qml/pages/ directory
    - Creates qml/components/ for reusable components
    - Does NOT modify existing {app-name}.qml main application file
    - Works within existing Aurora OS workspace

    Args:
        figma_file_url: Full Figma URL (e.g., https://www.figma.com/file/ABC123/MyDesign)
        access_token: Personal Access Token for Figma API (starts with 'figd_')
        workspace_dir: Aurora OS project workspace directory (contains existing {app-name}.qml and qml/ subdirectory)
        enhancement_types: List of enhancement types to suggest (informational only).
                          Options: ['auto_layout', 'components', 'effects', 'animations', 'responsive']
                          Default: ['auto_layout', 'components']

    Returns:
        Detailed report of the conversion process and next steps

    Raises:
        Exception: If conversion fails due to invalid inputs or API errors
    """
    if enhancement_types is None:
        enhancement_types = ["auto_layout", "components"]

    try:
        # Import utilities
        from aurora_mcp.utils.figma_client import (
            FigmaClient,
            extract_file_key_from_url,
        )
        from aurora_mcp.utils.qml_generator import QMLGenerator
        from aurora_mcp.utils.qml_validator import QMLValidator

        # Validate inputs
        validation_errors = _validate_inputs(
            figma_file_url, access_token, workspace_dir
        )
        if validation_errors:
            return "❌ Validation failed:\n" + "\n".join(validation_errors)

        # Step 1: Fetch Figma data via Personal Access Token
        print("🔄 Fetching Figma data...")
        file_key = extract_file_key_from_url(figma_file_url)
        figma_client = FigmaClient(access_token)
        figma_data = figma_client.fetch_file(file_key)

        # Step 2: Parse Figma file structure
        print("🔄 Parsing Figma file structure...")
        parsed_data = figma_client.extract_all_metadata(figma_data)

        # Step 3: Generate basic QML structure (no enhancement yet)
        print("🔄 Generating basic QML structure...")
        qml_generator = QMLGenerator()
        base_qml = qml_generator.generate_basic_structure(parsed_data)

        # Step 4: Validate basic QML
        print("🔄 Validating generated QML...")
        validator = QMLValidator()
        validation_result = validator.validate_syntax(base_qml)

        # Step 5: Save generated files to Aurora OS workspace
        print("🔄 Saving generated files...")
        output_info = _save_qml_project(
            enhanced_qml=base_qml,
            workspace_dir=workspace_dir,
            figma_data=figma_data,
            validation_result=validation_result,
        )

        # Step 6: Generate comprehensive report
        report = _generate_conversion_report(
            figma_data=figma_data,
            enhanced_qml=base_qml,
            validation_result=validation_result,
            workspace_dir=workspace_dir,
            enhancement_types=enhancement_types,
            output_info=output_info,
        )

        # Save report to workspace
        report_path = Path(workspace_dir) / "conversion-report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        # Step 7: Prepare enhancement suggestion
        enhancement_suggestion = f"""
🎯 **Next Step: Enhance Your QML Files**

The generated QML files are marked for enhancement. To apply advanced features, run:

```
enhance_qml_code --qml-file {output_info["main_page"]} --enhancement-types {" ".join(enhancement_types)}
```

Or enhance individual files:
- Main page: `enhance_qml_code --qml-file {output_info["main_page"]}`
- Cover page: `enhance_qml_code --qml-file {output_info["cover_page"]}`

Available enhancement types: auto_layout, components, effects, animations, responsive
"""

        return f"""✅ Basic QML conversion completed successfully!

Files saved to: {workspace_dir}

{enhancement_suggestion}

{report}"""

    except Exception as e:
        error_message = f"❌ Conversion failed: {str(e)}"
        print(error_message)
        return error_message


def _validate_inputs(
    figma_file_url: str, access_token: str, workspace_dir: str
) -> list[str]:
    """Validate tool inputs and return list of errors if any."""
    errors = []

    # Validate Figma URL
    if not figma_file_url:
        errors.append("Figma file URL is required")
    elif "figma.com" not in figma_file_url:
        errors.append("Invalid Figma URL format")

    # Validate access token
    from aurora_mcp.utils.figma_client import validate_figma_access_token

    if not access_token:
        errors.append("Figma access token is required")
    elif not validate_figma_access_token(access_token):
        errors.append("Invalid Figma access token format")

    # Validate workspace directory
    if not workspace_dir:
        errors.append("Workspace directory is required")
    else:
        try:
            workspace_path = Path(workspace_dir)
            if not workspace_path.exists():
                errors.append(f"Workspace directory does not exist: {workspace_dir}")
            elif not workspace_path.is_dir():
                errors.append(f"Workspace path is not a directory: {workspace_dir}")
            else:
                # Check if it looks like an Aurora OS project (has typical structure)
                # This is optional validation - we'll create qml/ directory if needed
                pass
        except Exception as e:
            errors.append(f"Invalid workspace directory path: {e}")

    return errors


def _save_qml_project(
    enhanced_qml: str,
    workspace_dir: str,
    figma_data: dict[str, Any],
    validation_result: dict[str, Any],
) -> dict[str, Any]:
    """Save the generated QML project files to Aurora OS workspace."""
    workspace_path = Path(workspace_dir)

    # Ensure the workspace directory exists
    if not workspace_path.exists():
        raise ValueError(f"Workspace directory does not exist: {workspace_dir}")

    # Create QML directory structure within the Aurora OS workspace
    qml_dir = workspace_path / "qml"
    pages_dir = qml_dir / "pages"
    components_dir = qml_dir / "components"

    # Create directories if they don't exist
    pages_dir.mkdir(parents=True, exist_ok=True)
    components_dir.mkdir(parents=True, exist_ok=True)

    # Add enhancement marker to QML content
    enhancement_marker = "// AURORA_MCP_ENHANCE_REQUIRED - Generated by figma_to_qml, run enhance_qml_code to improve"
    enhanced_qml_with_marker = f"{enhancement_marker}\n{enhanced_qml}"

    # Save main page to qml/pages/
    main_page_path = pages_dir / "MainPage.qml"
    with open(main_page_path, "w", encoding="utf-8") as f:
        f.write(enhanced_qml_with_marker)

    # Note: Do NOT create Main.qml - Aurora OS projects have {app-name}.qml already
    # The existing {app-name}.qml file should remain untouched

    # Find existing application main file (pattern: *.qml in workspace root, excluding qml/ subdirectory)
    app_main_files = [f for f in workspace_path.glob("*.qml") if f.is_file()]
    app_main_path = None
    if app_main_files:
        # Use the first found .qml file as the main app file
        app_main_path = app_main_files[0]

    # Create a basic cover page if cover directory exists or create it
    cover_dir = qml_dir / "cover"
    cover_dir.mkdir(parents=True, exist_ok=True)
    cover_path = cover_dir / "CoverPage.qml"

    if not cover_path.exists():
        cover_qml = _generate_cover_page(figma_data.get("name", "App"))
        # Add enhancement marker to cover page as well
        cover_qml_with_marker = f"{enhancement_marker}\n{cover_qml}"
        with open(cover_path, "w", encoding="utf-8") as f:
            f.write(cover_qml_with_marker)

    # Create README in workspace root if it doesn't exist
    readme_path = workspace_path / "README.md"
    if not readme_path.exists():
        readme_content = _generate_readme(figma_data, validation_result)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

    # Save Figma metadata for enhancement context
    figma_data_path = workspace_path / "figma-metadata.json"
    with open(figma_data_path, "w", encoding="utf-8") as f:
        json.dump(figma_data, f, indent=2)

    return {
        "main_page": str(main_page_path),
        "app_main": str(app_main_path) if app_main_path else "No main app file found",
        "cover_page": str(cover_path),
        "readme": str(readme_path),
        "figma_metadata": str(figma_data_path),
        "qml_pages_dir": str(pages_dir),
        "qml_components_dir": str(components_dir),
    }


def _generate_cover_page(app_name: str) -> str:
    """Generate a basic cover page for the Sailfish app."""
    return f"""import QtQuick 2.0
import Sailfish.Silica 1.0

CoverPage {{
    objectName: "defaultCover"

    CoverPlaceholder {{
        text: qsTr("{app_name}")
        icon.source: "image://theme/icon-launcher-default"
    }}
}}"""


def _generate_readme(
    figma_data: dict[str, Any], validation_result: dict[str, Any]
) -> str:
    """Generate README for the QML project."""
    app_name = figma_data.get("name", "Figma App")
    return f"""# {app_name}

Generated from Figma using Aurora MCP Figma-to-QML tool.

## Project Structure

```
├── Main.qml                 # Application entry point
├── qml/
│   ├── pages/
│   │   └── MainPage.qml     # Main application page
│   ├── components/          # Reusable components
│   └── cover/
│       └── CoverPage.qml    # App cover for Sailfish OS
├── assets/
│   ├── images/              # Image assets
│   └── icons/               # Icon assets
└── README.md                # This file

## Source Information

- **Figma File**: {figma_data.get("name", "Unknown")}
- **Last Modified**: {figma_data.get("lastModified", "Unknown")}
- **Version**: {figma_data.get("version", "Unknown")}

## Development

This is a Sailfish Silica QML application. To build and run:

1. Import into Aurora SDK
2. Build the project
3. Deploy to device or emulator

## Code Quality

- **Validation Status**: {"✅ Valid" if validation_result.get("syntax_valid", True) else "❌ Has Issues"}
- **Warnings**: {len(validation_result.get("warnings", []))}
- **Suggestions**: {len(validation_result.get("suggestions", []))}

## Next Steps

1. Review generated QML code
2. Customize styling and behavior
3. Add application logic
4. Test on different screen sizes
5. Add translations using qsTr()

---
Generated with Aurora MCP Figma-to-QML tool
"""


def _generate_fix_prompt(qml_code: str, validation_result: dict[str, Any]) -> str:
    """Generate a prompt for fixing validation issues."""
    errors = validation_result.get("errors", [])
    warnings = validation_result.get("warnings", [])

    fix_prompt = f"""
Fix the following QML validation issues:

ERRORS:
{chr(10).join("- " + error for error in errors)}

WARNINGS:
{chr(10).join("- " + warning for warning in warnings)}

Current QML code:
{qml_code}

Please fix these issues and return corrected QML code that:
1. Has valid syntax with balanced braces
2. Uses proper QML naming conventions
3. Follows Sailfish Silica guidelines
4. Uses Theme properties where appropriate
5. Includes proper qsTr() for localization
"""
    return fix_prompt


def _generate_conversion_report(
    figma_data: dict[str, Any],
    enhanced_qml: str,
    validation_result: dict[str, Any],
    workspace_dir: str,
    enhancement_types: list[str],
    output_info: dict[str, Any],
) -> str:
    """Generate a comprehensive conversion report."""
    # Calculate statistics
    document = figma_data.get("document", {})
    total_nodes = _count_nodes_recursive(document)
    qml_lines = len(enhanced_qml.split("\n"))

    # Get compliance score
    from aurora_mcp.utils.qml_validator import QMLValidator

    validator = QMLValidator()
    compliance_score = validator.get_sailfish_compliance_score(enhanced_qml)

    # Get app main file info
    app_main_info = output_info.get("app_main", "No main app file found")
    app_main_name = (
        Path(app_main_info).name
        if app_main_info != "No main app file found"
        else "{app-name}.qml"
    )

    report = f"""# Figma to QML Conversion Report

## Source Information
- **Figma File**: {figma_data.get("name", "Unknown")}
- **File URL**: {figma_data.get("thumbnailUrl", "N/A")}
- **Last Modified**: {figma_data.get("lastModified", "Unknown")}
- **Version**: {figma_data.get("version", "Unknown")}
- **Total Nodes Processed**: {total_nodes}

## Conversion Results
- **Aurora OS Workspace**: `{workspace_dir}`
- **Generated QML Lines**: {qml_lines}
- **Basic Structure**: Generated successfully
- **Sailfish Compliance Score**: {compliance_score:.2f}/1.0

## Aurora OS Project Structure
```
{workspace_dir}/
├── {app_main_name}              # Existing main application file (unchanged)
├── qml/
│   ├── pages/
│   │   └── MainPage.qml         # Generated main page ({qml_lines} lines) [NEEDS ENHANCEMENT]
│   ├── components/              # Ready for reusable components
│   └── cover/
│       └── CoverPage.qml        # App cover page [NEEDS ENHANCEMENT]
├── figma-metadata.json          # Figma data for enhancement context
├── README.md                    # Project documentation (if created)
└── conversion-report.md         # This report
```

## Code Quality Assessment
- **Syntax Valid**: {"✅ Yes" if validation_result.get("syntax_valid", True) else "❌ No"}
- **Errors**: {len(validation_result.get("errors", []))}
- **Warnings**: {len(validation_result.get("warnings", []))}
- **Suggestions**: {len(validation_result.get("suggestions", []))}
- **Enhancement Status**: 🔄 **PENDING** - Files marked for enhancement

### Issues Found
"""

    # Add errors if any
    errors = validation_result.get("errors", [])
    if errors:
        report += "\n**Errors:**\n"
        for error in errors:
            report += f"- ❌ {error}\n"

    # Add warnings if any
    warnings = validation_result.get("warnings", [])
    if warnings:
        report += "\n**Warnings:**\n"
        for warning in warnings:
            report += f"- ⚠️ {warning}\n"

    # Add suggestions if any
    suggestions = validation_result.get("suggestions", [])
    if suggestions:
        report += "\n**Suggestions:**\n"
        for suggestion in suggestions:
            report += f"- 💡 {suggestion}\n"

    report += f"""

## Enhancement Required

### 🎯 Immediate Action Required
The generated QML files contain basic structure only. **Enhancement is required** for production use.

Generated files are marked with enhancement comments. Use the `enhance_qml_code` tool:

```bash
# Enhance main page
enhance_qml_code --qml-file {output_info.get("main_page", "qml/pages/MainPage.qml")} --enhancement-types {" ".join(enhancement_types)}

# Enhance cover page  
enhance_qml_code --qml-file {output_info.get("cover_page", "qml/cover/CoverPage.qml")} --enhancement-types {" ".join(enhancement_types)}
```

### Available Enhancement Types
{chr(10).join(f"- **{enhancement}**: Improves layout and Aurora OS integration" for enhancement in enhancement_types)}

### Additional Enhancement Options
- **auto_layout**: Converts absolute positioning to proper Layout components
- **components**: Extracts reusable components for repeated UI elements
- **effects**: Adds visual effects (shadows, gradients, blur)
- **animations**: Implements smooth transitions and interactions
- **responsive**: Makes UI adaptive for different screen sizes

## Sailfish Silica Integration
- Uses Sailfish.Silica 1.0 components
- Follows Aurora OS UI guidelines
- Implements proper Theme usage
- Includes localization support with qsTr()

## Integration Steps

### 1. Enhance Generated Files (Required)
Before using the generated QML, run enhancement:
```bash
enhance_qml_code --qml-file {output_info.get("main_page", "qml/pages/MainPage.qml")}
```

### 2. Import Enhanced Page
Add to your `{app_main_name}`:

```qml
import "qml/pages"

ApplicationWindow {{
    initialPage: Component {{ MainPage {{}} }}
    // ... rest of your app configuration
}}
```

### 3. Development Workflow
1. **Enhance**: Run `enhance_qml_code` on generated files
2. **Integrate**: Import enhanced pages in your `{app_main_name}`
3. **Test**: Build and test on device/emulator
4. **Customize**: Adjust styling and add business logic
5. **Iterate**: Use `enhance_qml_code` with different types as needed

### Development Recommendations
1. **Component Development**: Create reusable components in `qml/components/`
2. **Page Navigation**: Add additional pages in `qml/pages/` as needed
3. **Responsive Testing**: Test on different screen sizes and orientations
4. **Performance Optimization**: Profile and optimize for mobile performance
5. **Accessibility**: Add Accessible properties for better user experience
6. **Localization**: Complete translation strings using qsTr()

### Aurora OS Specific Improvements
1. **Page Stack Navigation**: Implement proper PageStack navigation
2. **Pulley Menu Integration**: Add PullDownMenu and PushUpMenu where appropriate
3. **Context Menu Support**: Add context menus for list items
4. **Cover Actions**: Enhance CoverPage with relevant actions
5. **Settings Integration**: Connect to Aurora OS settings if needed

## Tool Information
- **Conversion Tool**: Aurora MCP figma_to_qml
- **Enhancement Tool**: Aurora MCP enhance_qml_code
- **Conversion Date**: {_get_current_timestamp()}
- **Pipeline**: Figma API → Basic QML → **[Enhancement Required]** → Production Ready
- **Target Platform**: Aurora OS (Sailfish OS based)
- **Workspace Integration**: Preserves existing app structure

## Generated QML Preview (Basic)
```qml
{enhanced_qml[:500]}{"..." if len(enhanced_qml) > 500 else ""}
```

## Next Steps Summary
1. ✅ **Basic QML Generated** - Files created with Aurora OS structure
2. 🔄 **Enhancement Required** - Run `enhance_qml_code` tool
3. ⏸️ **Integration Pending** - Import enhanced pages in your app
4. ⏸️ **Testing Pending** - Build and test on Aurora OS device

---
🤖 Generated with Aurora MCP figma_to_qml tool  
🎯 **Action Required**: Run enhancement tool before production use
"""

    return report


def _count_nodes_recursive(node: dict[str, Any]) -> int:
    """Count total nodes in Figma document tree."""
    count = 1
    for child in node.get("children", []):
        count += _count_nodes_recursive(child)
    return count


def _get_current_timestamp() -> str:
    """Get current timestamp in readable format."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Export the main function for MCP registration
__all__ = ["figma_to_qml"]
