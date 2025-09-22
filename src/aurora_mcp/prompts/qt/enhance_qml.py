"""MCP prompt for enhancing generated QML code with Figma data."""


def enhance_qml_code(
    qml_code: str, figma_data: str, enhancement_type: str = "auto_layout"
) -> str:
    """
    Улучшение сгенерированного QML кода с использованием данных из Figma.

    Args:
        qml_code: Базовый QML код для улучшения
        figma_data: JSON данные из Figma с метаданными элементов
        enhancement_type: Тип улучшений (auto_layout, components, effects, animations, responsive)

    Returns:
        Улучшенный QML код
    """

    enhancement_prompts = {
        "auto_layout": f"""
Проанализируй следующий базовый QML код и данные Figma auto-layout:

QML код:
{qml_code}

Figma данные:
{figma_data}

Задача: Преобразуй Figma auto-layout в соответствующие QML Layout компоненты.

Правила преобразования:
1. Figma horizontal auto-layout → QML RowLayout
2. Figma vertical auto-layout → QML ColumnLayout
3. Figma wrap layout → QML Flow или Grid
4. Учти spacing из Figma данных
5. Преобразуй alignment в Layout.alignment
6. Используй Layout.fillWidth/fillHeight для responsive элементов
7. Добавь proper anchors.margins используя Theme.paddingLarge/Medium

Пример преобразования:
```qml
// Вместо абсолютного позиционирования:
Item {{
    x: 20; y: 30
    width: 200; height: 40
}}

// Используй Layout:
RowLayout {{
    spacing: Theme.paddingMedium
    anchors {{
        left: parent.left
        right: parent.right
        margins: Theme.paddingLarge
    }}

    Item {{
        Layout.fillWidth: true
        Layout.preferredHeight: 40
    }}
}}
```

Требования к результату:
- Обязательно импортируй QtQuick.Layouts 1.0 если используешь Layout
- Используй Sailfish Theme для spacing и margins
- Сохрани иерархию элементов
- Добавь комментарии где применил auto-layout

Верни улучшенный QML код с правильными Layout компонентами.
""",
        "components": f"""
Проанализируй QML код и найди повторяющиеся элементы:

QML код:
{qml_code}

Figma данные:
{figma_data}

Задача: Создай переиспользуемые QML компоненты для повторяющихся элементов.

Алгоритм анализа:
1. Найди элементы с похожей структурой (более 2 повторений)
2. Определи различающиеся свойства (текст, размер, цвет)
3. Создай Component с property declarations для различий
4. Добавь signal handlers для интерактивности
5. Используй Sailfish naming conventions (camelCase)

Пример выделения компонента:
```qml
// Повторяющийся код:
Rectangle {{
    width: 200; height: 60
    color: "blue"
    Text {{ text: "Button 1" }}
}}

Rectangle {{
    width: 200; height: 60
    color: "red"
    Text {{ text: "Button 2" }}
}}

// Становится компонентом:
// CustomButton.qml
Rectangle {{
    property string text: ""
    property color buttonColor: Theme.primaryColor

    width: 200; height: 60
    color: buttonColor

    Text {{
        text: parent.text
        anchors.centerIn: parent
        color: Theme.primaryTextColor
    }}

    MouseArea {{
        anchors.fill: parent
        onClicked: parent.clicked()
    }}

    signal clicked()
}}
```

Требования:
- Компоненты должны наследоваться от подходящих Silica типов когда возможно
- Добавь objectName для debugging
- Используй qsTr() для всех пользовательских текстов
- Следуй Sailfish UX guidelines для interactive элементов
- Добавь property aliases для часто используемых свойств

Верни:
1. Список отдельных компонентов (.qml файлов)
2. Обновленный основной QML с использованием этих компонентов
3. Краткое описание что каждый компонент делает
""",
        "effects": f"""
Добавь визуальные эффекты к QML коду на основе Figma данных:

QML код:
{qml_code}

Figma эффекты данные:
{figma_data}

Задача: Реализуй Figma эффекты в QML коде.

Маппинг эффектов Figma → QML:
1. Drop Shadow → DropShadow {{ horizontalOffset: X; verticalOffset: Y; radius: R; color: C }}
2. Inner Shadow → InnerShadow {{ horizontalOffset: X; verticalOffset: Y; radius: R; color: C }}
3. Linear Gradient → LinearGradient {{ orientation: Gradient.Horizontal/Vertical; stops: [...] }}
4. Radial Gradient → RadialGradient {{ center: Qt.point(x,y); stops: [...] }}
5. Background Blur → FastBlur {{ radius: X; source: sourceItem; cached: true }}
6. Layer Blur → RecursiveBlur {{ radius: X; loops: 2 }}

Пример реализации эффектов:
```qml
Rectangle {{
    id: baseItem
    width: 200; height: 100

    // Градиент фон
    gradient: Gradient {{
        GradientStop {{ position: 0.0; color: "#ff6b6b" }}
        GradientStop {{ position: 1.0; color: "#4ecdc4" }}
    }}

    // Тень
    DropShadow {{
        anchors.fill: parent
        horizontalOffset: 4
        verticalOffset: 4
        radius: 12
        samples: 25
        color: Theme.rgba(Theme.secondaryColor, 0.4)
        source: parent
        cached: true
    }}
}}
```

Важные моменты:
- Импортируй QtGraphicalEffects 1.0 если используешь эффекты
- Ограничь количество эффектов для производительности (максимум 2-3 на элемент)
- Используй cached: true для улучшения performance
- Для теней используй цвета из Sailfish Theme
- Учти, что эффекты увеличивают потребление GPU

Sailfish специфика:
- Предпочитай встроенные gradient свойства вместо LinearGradient когда возможно
- Используй Theme.rgba() для прозрачности
- Тестируй на устройствах с разной производительностью

Верни QML код с реализованными эффектами и необходимыми импортами.
""",
        "animations": f"""
Добавь анимации и переходы к QML коду:

QML код:
{qml_code}

Figma интерактивные данные:
{figma_data}

Задача: Создай плавные переходы и анимации для UI элементов.

Типы анимаций для реализации:
1. State transitions (normal → pressed → focused → disabled)
2. Property animations (opacity, scale, position, color)
3. Page transitions (push/pop с PageStack)
4. Loading states и progress indicators
5. Hover effects (для desktop/tablet)
6. Spring animations для естественных движений

Sailfish animation guidelines:
- Быстрые: 150ms (micro-interactions)
- Средние: 300ms (standard transitions)
- Медленные: 500ms (page transitions)
- Easing: Easing.InOutQuad для большинства случаев
- Easing.OutBack для bounce эффектов
- Все transitions должны быть reversible

Пример структуры с анимациями:
```qml
Rectangle {{
    id: button
    width: 200; height: 60

    states: [
        State {{
            name: "normal"
            PropertyChanges {{ target: button; scale: 1.0; opacity: 1.0 }}
        }},
        State {{
            name: "pressed"
            PropertyChanges {{ target: button; scale: 0.95; opacity: 0.8 }}
        }},
        State {{
            name: "disabled"
            PropertyChanges {{ target: button; opacity: 0.5 }}
        }}
    ]

    transitions: [
        Transition {{
            from: "*"; to: "*"
            PropertyAnimation {{
                duration: 150
                easing.type: Easing.InOutQuad
                properties: "scale,opacity"
            }}
        }}
    ]

    MouseArea {{
        anchors.fill: parent
        onPressed: button.state = "pressed"
        onReleased: button.state = "normal"
        onCanceled: button.state = "normal"
    }}
}}
```

Специальные анимации для Sailfish:
- PushUpMenu/PullDownMenu появление
- Page push/pop с правильными transitions
- List item highlight animations
- Keyboard появление/скрытие

Производительность:
- Избегай animating большого количества элементов одновременно
- Используй transform properties (scale, rotation) вместо size changes
- Предпочитай opacity changes вместо visibility

Верни QML код с добавленными анимациями и состояниями.
""",
        "responsive": f"""
Сделай QML код адаптивным для разных экранов Sailfish OS:

QML код:
{qml_code}

Figma данные с breakpoints:
{figma_data}

Задача: Адаптируй UI для различных размеров экрана и ориентаций.

Sailfish responsive система:
1. Screen.sizeCategory константы:
   - Screen.Small (phone portrait, ~540x960)
   - Screen.Medium (phone landscape, ~960x540)
   - Screen.Large (tablet portrait, ~768x1024)
   - Screen.ExtraLarge (tablet landscape, ~1024x768)

2. Adaptive spacing с Theme:
   - Theme.paddingSmall (8dp)
   - Theme.paddingMedium (16dp)
   - Theme.paddingLarge (24dp)
   - Theme.paddingExtraLarge (32dp)

3. Responsive typography:
   - Theme.fontSizeExtraSmall
   - Theme.fontSizeSmall
   - Theme.fontSizeMedium
   - Theme.fontSizeLarge
   - Theme.fontSizeExtraLarge

4. Orientation handling:
   - allowedOrientations: Orientation.All
   - orientation === Orientation.Portrait/Landscape
   - Screen.width, Screen.height

Пример адаптивного кода:
```qml
Page {{
    allowedOrientations: Orientation.All

    Column {{
        width: parent.width
        spacing: Screen.sizeCategory >= Screen.Large ?
                Theme.paddingLarge : Theme.paddingMedium

        // Адаптивная ширина контента
        Item {{
            width: Math.min(600, parent.width - 2 * Theme.paddingLarge)
            height: orientation === Orientation.Portrait ? 120 : 80
            anchors.horizontalCenter: parent.horizontalCenter

            Text {{
                font.pixelSize: {{
                    if (Screen.sizeCategory >= Screen.Large)
                        return Theme.fontSizeLarge
                    else if (Screen.sizeCategory >= Screen.Medium)
                        return Theme.fontSizeMedium
                    else
                        return Theme.fontSizeSmall
                }}

                // Адаптивное количество строк
                maximumLineCount: Screen.sizeCategory >= Screen.Large ? 3 : 2
                wrapMode: Text.WordWrap
            }}
        }}
    }}
}}
```

Adaptive layout patterns:
- Single column → Multi column на больших экранах
- Vertical navigation → Horizontal tabs
- Stacked content → Side-by-side panels
- Full width → Centered с max-width

Тестирование responsive:
- Проверь все orientation changes
- Убедись что content не обрезается
- Проверь readability на маленьких экранах
- Оптимизируй touch targets (минимум 44dp)

Верни адаптивный QML код с правильным responsive behavior.
""",
    }

    return enhancement_prompts.get(enhancement_type, enhancement_prompts["auto_layout"])
