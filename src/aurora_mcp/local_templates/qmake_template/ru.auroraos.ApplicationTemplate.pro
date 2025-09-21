# SPDX-FileCopyrightText: 2024 Open Mobile Platform LLC <community@omp.ru>
# SPDX-License-Identifier: BSD-3-Clause

TARGET = ru.auroraos.ApplicationTemplate

CONFIG += \
    auroraapp \

PKGCONFIG += \

SOURCES += \
    src/main.cpp \

HEADERS += \

DISTFILES += \
    rpm/ru.auroraos.ApplicationTemplate.spec \
    AUTHORS.md \
    CODE_OF_CONDUCT.md \
    CONTRIBUTING.md \
    LICENSE.BSD-3-Clause.md \
    README.md \
    README.ru.md \

AURORAAPP_ICONS = 86x86 108x108 128x128 172x172

CONFIG += auroraapp_i18n

TRANSLATIONS += \
    translations/ru.auroraos.ApplicationTemplate.ts \
    translations/ru.auroraos.ApplicationTemplate-ru.ts \
