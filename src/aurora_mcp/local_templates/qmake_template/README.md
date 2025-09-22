# Application Template

The project provides a template for Aurora OS applications.

The main purpose is to demonstrate using a minimum of source code to get a correct and extensible application.

## Terms of Use and Participation

The source code of the project is provided under [the license](LICENSE.BSD-3-Clause.md),
which allows its use in third-party applications.

The [contributor agreement](CONTRIBUTING.md) documents the rights granted by contributors
of the Open Mobile Platform.

Information about the contributors is specified in the [AUTHORS](AUTHORS.md) file.

[Code of conduct](CODE_OF_CONDUCT.md) is a current set of rules of the Open Mobile
Platform which informs you how we expect the members of the community will interact
while contributing and communicating.

## Project Structure

The project has a standard structure
of an application based on C++ and QML for Aurora OS.

* **[ru.auroraos.ApplicationTemplate.pro](ru.auroraos.ApplicationTemplate.pro)** file describes the project structure for the qmake build system.
* **[icons](icons)** directory contains the application icons for different screen resolutions.
* **[qml](qml)** directory contains the QML source code and the UI resources.
  * **[cover](qml/cover)** directory contains the application cover implementations.
  * **[icons](qml/icons)** directory contains the additional custom UI icons.
  * **[pages](qml/pages)** directory contains the application pages.
  * **[ApplicationTemplate.qml](qml/ApplicationTemplate.qml)** file provides the application window implementation.
* **[rpm](rpm)** directory contains the rpm-package build settings.
  * **[ru.auroraos.ApplicationTemplate.spec](rpm/ru.auroraos.ApplicationTemplate.spec)** file is used by rpmbuild tool.
* **[src](src)** directory contains the C++ source code.
  * **[main.cpp](src/main.cpp)** file is the application entry point.
* **[translations](translations)** directory contains the UI translation files.
* **[ru.auroraos.ApplicationTemplate.desktop](ru.auroraos.ApplicationTemplate.desktop)** file defines the display and parameters for launching the application.

## Compatibility

The project is compatible with all the current versions of the Aurora OS.

## Screenshots

![screenshots](screenshots/screenshots.png)

## This document in Russian / Перевод этого документа на русский язык

- [README.ru.md](README.ru.md)
