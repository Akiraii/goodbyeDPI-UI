import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Dialogs
import FluentUI.Controls
import FluentUI.impl
import GoodbyeDPI_UI

Page {
    id: page
    title: "Zapret2"
    header: Item {}
    padding: 0
    topPadding: 24

    property bool installed: backend.getBool("COMPONENTS", "zapret2")
    property bool busy: false
    property bool running: process.is_process_alive() && backend.getValue("GLOBAL", "engine") === "zapret2"
    property string actionMessage: ""
    property bool russian: backend.getValue("GLOBAL", "language") === "RU"

    function tr2(ru, en) { return russian ? ru : en }
    function saveStrategy() {
        var result = backend.validate_zapret2_args(strategyEditor.text)
        if (result.indexOf("OK:") !== 0) {
            actionMessage = result
            return false
        }
        backend.set_to_config("ZAPRET2", "custom_parameters", strategyEditor.text)
        process.update_preset()
        actionMessage = tr2("Стратегия сохранена. Для применения перезапусти движок.",
                            "Strategy saved. Restart the engine to apply it.")
        return true
    }
    function startStop() {
        if (process.is_process_alive()) {
            if (backend.getValue("GLOBAL", "engine") !== "zapret2") {
                actionMessage = tr2("Сначала останови другой активный движок.",
                                    "Stop the other running engine first.")
                return
            }
            process.stop_process()
            running = false
            return
        }
        if (!saveStrategy()) return
        process.change_engine("zapret2")
        if (!process.start_process()) {
            actionMessage = tr2("Не удалось запустить: смотри журнал приложения.",
                                "Start failed: inspect application log.")
        }
        running = process.is_process_alive()
    }

    FileDialog {
        id: importDialog
        title: tr2("Импорт стратегии Zapret2 (JSON или CMD)", "Import Zapret2 strategy (JSON or CMD)")
        nameFilters: ["Zapret2 strategy (*.json *.cmd *.bat)"]
        fileMode: FileDialog.OpenFile
        onAccepted: {
            var path = selectedFile.toString().replace("file:///", "")
            if (backend.load_preset("zapret2", path)) {
                strategyEditor.text = backend.get_from_config("ZAPRET2", "custom_parameters")
                process.update_preset()
                actionMessage = tr2("Стратегия импортирована.", "Strategy imported.")
            } else {
                actionMessage = tr2("Неверный файл или неподдерживаемый синтаксис.", "Invalid file or unsupported syntax.")
            }
        }
    }
    FileDialog {
        id: exportDialog
        title: tr2("Экспорт стратегии Zapret2", "Export Zapret2 strategy")
        nameFilters: ["JSON (*.json)"]
        fileMode: FileDialog.SaveFile
        onAccepted: {
            if (saveStrategy()) {
                backend.save_preset("zapret2", selectedFile.toString().replace("file:///", ""))
                actionMessage = tr2("Стратегия экспортирована.", "Strategy exported.")
            }
        }
    }

    ScrollablePage {
        anchors.fill: parent
        leftPadding: 0
        rightPadding: 0
        topPadding: 0

        ColumnLayout {
            width: Math.min(950, Math.max(320, parent.width - 48))
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 14

            Label {
                text: "Zapret2 / winws2.exe"
                font: Typography.subtitle
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: tr2(
                    "Отдельный движок на основе официального bol-van/zapret-win-bundle. Существующий Zapret не изменяется.",
                    "Separate engine from the official Windows bundle. Classic Zapret is unaffected.")
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: tr2("Установлен: ", "Installed: ") +
                      (page.installed ? backend.getValue("COMPONENTS", "zapret2_version") :
                                        tr2("нет", "no"))
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Button {
                    enabled: !page.busy
                    text: page.installed ? tr2("Обновить Zapret2", "Update Zapret2") :
                                           tr2("Установить Zapret2", "Install Zapret2")
                    onClicked: {
                        if (process.is_process_alive()) {
                            actionMessage = tr2("Останови работающий движок перед установкой.",
                                                "Stop the running engine before installing.")
                            return
                        }
                        page.busy = true
                        page.actionMessage = tr2("Скачивание официальной Windows-сборки…",
                                                 "Downloading official Windows bundle…")
                        backend.download_component("zapret2", false)
                    }
                }
                BusyIndicator {
                    running: page.busy
                    visible: page.busy
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                }
                Button {
                    enabled: page.installed && !page.busy
                    text: page.running ? tr2("Остановить", "Stop") : tr2("Запустить", "Start")
                    onClicked: page.startStop()
                }
                Button {
                    text: tr2("Папка", "Folder")
                    enabled: page.installed
                    onClicked: backend.open_component_folder("zapret2")
                }
            }
            Label {
                Layout.fillWidth: true
                text: page.actionMessage
                wrapMode: Text.Wrap
                visible: page.actionMessage.length > 0
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: tr2(
                    "Для запуска требуются права администратора. Перед запуском другой программы с WinDivert останови Zapret2.",
                    "Administrator rights are required. Stop Zapret2 before using another WinDivert engine.")
            }
            Label {
                text: tr2("Стратегия (аргументы winws2.exe)", "Strategy (winws2.exe arguments)")
                font: Typography.bodyStrong
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: tr2(
                    "Редактируй только аргументы без имени EXE. Lua-выражения с пробелами заключай в кавычки, пути записывай через /.",
                    "Enter arguments only, not the EXE. Quote Lua expressions containing spaces; use / in paths.")
            }
            TextArea {
                id: strategyEditor
                Layout.fillWidth: true
                Layout.preferredHeight: 210
                wrapMode: TextEdit.Wrap
                text: backend.get_from_config("ZAPRET2", "custom_parameters")
                placeholderText: "--wf-tcp-out=80,443 --lua-init=@lua/zapret-lib.lua ..."
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Button {
                    text: tr2("Проверить", "Validate")
                    onClicked: page.actionMessage = backend.validate_zapret2_args(strategyEditor.text)
                }
                Button {
                    text: tr2("Сохранить", "Save")
                    onClicked: page.saveStrategy()
                }
                Button {
                    text: tr2("Импорт JSON/CMD", "Import JSON/CMD")
                    onClicked: importDialog.open()
                }
                Button {
                    text: tr2("Экспорт JSON", "Export JSON")
                    onClicked: exportDialog.open()
                }
            }
            Label {
                text: tr2("Диагностика установки", "Installation diagnostics")
                font: Typography.bodyStrong
            }
            Button {
                text: tr2("Проверить установку", "Check installation")
                onClicked: diagnosticsOutput.text = backend.zapret2_diagnostics()
            }
            TextArea {
                id: diagnosticsOutput
                Layout.fillWidth: true
                Layout.preferredHeight: 140
                readOnly: true
                wrapMode: TextEdit.Wrap
                text: ""
                placeholderText: tr2("Статус исполняемого файла, библиотек и стратегии.",
                                     "Binary, dependencies and strategy status.")
            }
            Label {
                text: "Blockcheck2"
                font: Typography.bodyStrong
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: tr2(
                    "Перед диагностикой останови Zapret2 и все остальные DPI-программы. Откроется отдельное окно официального Blockcheck2.",
                    "Stop Zapret2 and all other DPI tools before testing. Official Blockcheck2 opens in a separate window.")
            }
            Button {
                text: tr2("Запустить Blockcheck2", "Run Blockcheck2")
                enabled: page.installed && !page.busy
                onClicked: {
                    if (process.is_process_alive()) {
                        page.actionMessage = tr2("Сначала останови DPI-движок.",
                                                 "Stop the active DPI engine first.")
                        return
                    }
                    var result = backend.run_zapret2_blockcheck()
                    page.actionMessage = result === "True" ?
                        tr2("Blockcheck2 запущен в отдельном окне.", "Blockcheck2 started in another window.") :
                        result
                }
            }
            Button {
                text: tr2("Исходники Windows-bundle", "Official Windows bundle")
                onClicked: Qt.openUrlExternally("https://github.com/bol-van/zapret-win-bundle")
            }
            Item { Layout.preferredHeight: 24 }
        }
    }
    Connections {
        target: backend
        function onComponent_installing_finished(result) {
            if (!page.busy) return
            page.busy = false
            if (result === "True" || result === "reload_need") {
                page.installed = true
                page.actionMessage = page.tr2("Zapret2 установлен.", "Zapret2 installed.")
            } else {
                page.actionMessage = result
            }
        }
    }
    Connections {
        target: process
        function onProcess_started() { page.running = process.is_process_alive() && backend.getValue("GLOBAL","engine") === "zapret2" }
        function onProcess_stopped() { page.running = false }
        function onEngine_changed() { page.running = process.is_process_alive() && backend.getValue("GLOBAL","engine") === "zapret2" }
    }
}
