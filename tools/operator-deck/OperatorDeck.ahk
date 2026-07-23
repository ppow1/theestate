#Requires AutoHotkey v2.0
#SingleInstance Force

; Estate Operator Deck Prototype
; Narrow local Windows adapter for activating, launching, moving, and swapping configured targets.

configPath := A_ScriptDir "\config.ini"
if !FileExist(configPath)
    configPath := A_ScriptDir "\config.example.ini"

bindingsPath := A_ScriptDir "\runtime\window-bindings.ini"

settings := LoadSettings(configPath)
slots := LoadSlots(configPath)
targets := LoadTargets(configPath)

if A_Args.Length < 1
    DieWithUsage()

command := StrLower(A_Args[1])
argument := A_Args.Length >= 2 ? A_Args[2] : ""
secondArgument := A_Args.Length >= 3 ? A_Args[3] : ""

switch command {
    case "target":
        RequireArgument(argument, "target name")
        ActivateOrLaunch(GetTarget(targets, argument), slots, settings)
    case "swap":
        RequireArgument(argument, "target name")
        SwapWithTarget(GetTarget(targets, argument))
    case "move-active":
        RequireArgument(argument, "slot name")
        MoveActiveToSlot(GetSlot(slots, argument))
    case "place":
        RequireArgument(argument, "target name")
        RequireArgument(secondArgument, "slot name")
        PlaceTargetInSlot(GetTarget(targets, argument), GetSlot(slots, secondArgument))
    case "select":
        RequireArgument(argument, "target name")
        SelectTarget(GetTarget(targets, argument))
    case "select-active":
        SelectWindow(WinExist("A"))
    case "place-selected":
        RequireArgument(argument, "slot name")
        PlaceSelectedWindow(GetSlot(slots, argument))
    case "promote-selected":
        RequireArgument(argument, "slot name")
        PromoteSelectedWindow(GetSlot(slots, argument))
    case "promote-monitor":
        RequireArgument(argument, "monitor name")
        RequireArgument(secondArgument, "shape")
        PromoteSelectedWindow(GetMonitorShape(slots, argument, secondArgument))
    case "destination-monitor":
        RequireArgument(argument, "monitor name")
        HandleDestinationMonitor(slots, argument, false)
    case "arm-monitor":
        RequireArgument(argument, "monitor name")
        HandleDestinationMonitor(slots, argument, true)
    case "destination-shape":
        RequireArgument(argument, "shape")
        HandleDestinationShape(slots, argument)
    case "return-promoted":
        ReturnPromotedWindow()
    case "slot":
        RequireArgument(argument, "slot name")
        HandleSlotPress(GetSlot(slots, argument))
    case "cycle-slot":
        RequireArgument(argument, "slot name")
        EnterOrCommitCycleMode(GetSlot(slots, argument))
    case "clear-selection":
        ClearWindowSelection()
    case "undo":
        UndoLastMove()
    case "activate":
        RequireArgument(argument, "target name")
        ActivateTarget(GetTarget(targets, argument), false)
    case "dictation-toggle":
        ToggleDictation()
    case "bind":
        RequireArgument(argument, "target name")
        BindActiveTarget(GetTarget(targets, argument))
    case "unbind":
        RequireArgument(argument, "target name")
        UnbindTarget(GetTarget(targets, argument))
    default:
        DieWithUsage("Unknown command: " command)
}

LoadSettings(configFile) {
    return Map(
        "DefaultWaitSeconds", Integer(IniRead(configFile, "Settings", "DefaultWaitSeconds", "10")),
        "PostLaunchDelayMs", Integer(IniRead(configFile, "Settings", "PostLaunchDelayMs", "500"))
    )
}

LoadSlots(configFile) {
    slotMap := Map()
    section := IniRead(configFile, "Slots", , "")
    for line in StrSplit(section, "`n", "`r") {
        line := Trim(line)
        if line = ""
            continue
        parts := StrSplit(line, "=", , 2)
        if parts.Length != 2
            continue
        name := Trim(parts[1])
        coords := StrSplit(Trim(parts[2]), ",")
        if coords.Length != 4
            throw Error("Slot '" name "' must use x,y,width,height format.")
        slotMap[name] := Map(
            "name", name,
            "x", Integer(Trim(coords[1])),
            "y", Integer(Trim(coords[2])),
            "w", Integer(Trim(coords[3])),
            "h", Integer(Trim(coords[4]))
        )
    }
    return slotMap
}

LoadTargets(configFile) {
    targetMap := Map()
    for sectionName in GetIniSectionNames(configFile) {
        if !StartsWith(sectionName, "Target:")
            continue
        name := SubStr(sectionName, 8)
        targetMap[name] := Map(
            "name", name,
            "match", IniRead(configFile, sectionName, "match", ""),
            "launch", IniRead(configFile, sectionName, "launch", ""),
            "slot", IniRead(configFile, sectionName, "slot", ""),
            "behavior", IniRead(configFile, sectionName, "behavior", "activate_or_launch")
        )
    }
    return targetMap
}

GetIniSectionNames(configFile) {
    names := []
    raw := FileRead(configFile)
    for line in StrSplit(raw, "`n", "`r") {
        line := Trim(line)
        if RegExMatch(line, "^\[(.+)\]$", &match)
            names.Push(match[1])
    }
    return names
}

ActivateOrLaunch(target, slots, settings) {
    hwnd := FindTargetWindow(target)
    if !hwnd {
        launch := target["launch"]
        if launch = ""
            throw Error("Target '" target["name"] "' is missing and has no launch command.")
        Run(launch)
        Sleep(settings["PostLaunchDelayMs"])
        if !WinWait(target["match"], , settings["DefaultWaitSeconds"])
            throw Error("Timed out waiting for target window: " target["name"])
        hwnd := FindTargetWindow(target)
    }
    MoveWindowToConfiguredSlot(hwnd, target, slots)
    WinActivate("ahk_id " hwnd)
}

ActivateTarget(target, moveToSlot := false, slots := unset) {
    hwnd := FindTargetWindow(target)
    if !hwnd
        throw Error("Target window not found: " target["name"])
    if moveToSlot
        MoveWindowToConfiguredSlot(hwnd, target, slots)
    WinRestore("ahk_id " hwnd)
    WinActivate("ahk_id " hwnd)
}

SwapWithTarget(target) {
    activeHwnd := WinExist("A")
    if !activeHwnd
        throw Error("No active window found.")
    targetHwnd := FindTargetWindow(target)
    if !targetHwnd
        throw Error("Target window not found: " target["name"])
    if activeHwnd = targetHwnd {
        WinRestore("ahk_id " targetHwnd)
        WinActivate("ahk_id " targetHwnd)
        return
    }

    WinRestore("ahk_id " targetHwnd)
    activeRect := GetWindowRect(activeHwnd)
    targetRect := GetWindowRect(targetHwnd)
    SaveUndoTransaction([activeHwnd, targetHwnd])
    MoveWindow(activeHwnd, targetRect, false)
    MoveWindow(targetHwnd, activeRect, false)
    WinActivate("ahk_id " targetHwnd)
}

ToggleDictation() {
    Send("#h")
}

MoveActiveToSlot(slot) {
    hwnd := WinExist("A")
    if !hwnd
        throw Error("No active window found.")
    MoveWindow(hwnd, slot)
}

PlaceTargetInSlot(target, slot) {
    hwnd := FindTargetWindow(target)
    if !hwnd
        throw Error("Target window not found: " target["name"])
    MoveWindow(hwnd, slot)
    WinActivate("ahk_id " hwnd)
}

SelectTarget(target) {
    hwnd := FindTargetWindow(target)
    if !hwnd
        throw Error("Target window not found: " target["name"])
    SelectWindow(hwnd)
}

SelectWindow(hwnd, sourceSlot := "") {
    if !hwnd
        throw Error("No window found to select.")
    global bindingsPath
    selectionPath := A_ScriptDir "\runtime\window-selection.ini"
    DirCreate(A_ScriptDir "\runtime")
    IniWrite(hwnd, selectionPath, "Selection", "hwnd")
    IniWrite(WinGetPID("ahk_id " hwnd), selectionPath, "Selection", "pid")
    IniWrite(WinGetTitle("ahk_id " hwnd), selectionPath, "Selection", "title")
    IniWrite(WinGetProcessName("ahk_id " hwnd), selectionPath, "Selection", "process")
    IniWrite(sourceSlot, selectionPath, "Selection", "source_slot")
}

PlaceSelectedWindow(slot) {
    hwnd := GetSelectedWindow()
    if !hwnd
        throw Error("No valid window is currently selected.")
    MoveWindow(hwnd, slot)
    WinActivate("ahk_id " hwnd)
    ClearWindowSelection()
}

PromoteSelectedWindow(slot) {
    hwnd := GetSelectedWindow()
    if !hwnd
        throw Error("No valid window is currently selected.")
    SavePromotionOrigin(hwnd)
    MoveWindow(hwnd, slot)
    WinActivate("ahk_id " hwnd)
    ClearWindowSelection()
    ClearPlacementChoice()
}

GetMonitorShape(slots, monitorName, shapeName) {
    prefix := StrUpper(monitorName)
    topLeft := GetSlot(slots, prefix "_TOP_LEFT")
    topRight := GetSlot(slots, prefix "_TOP_RIGHT")
    bottomLeft := GetSlot(slots, prefix "_BOTTOM_LEFT")
    bottomRight := GetSlot(slots, prefix "_BOTTOM_RIGHT")

    left := Min(topLeft["x"], bottomLeft["x"])
    top := Min(topLeft["y"], topRight["y"])
    right := Max(topRight["x"] + topRight["w"], bottomRight["x"] + bottomRight["w"])
    bottom := Max(bottomLeft["y"] + bottomLeft["h"], bottomRight["y"] + bottomRight["h"])
    width := right - left
    height := bottom - top
    shape := StrLower(shapeName)

    switch shape {
        case "full":
            return Map("x", left, "y", top, "w", width, "h", height)
        case "left":
            return Map("x", left, "y", top, "w", Floor(width / 2), "h", height)
        case "right":
            half := Floor(width / 2)
            return Map("x", left + half, "y", top, "w", width - half, "h", height)
        case "top":
            return Map("x", left, "y", top, "w", width, "h", Floor(height / 2))
        case "bottom":
            half := Floor(height / 2)
            return Map("x", left, "y", top + half, "w", width, "h", height - half)
        default:
            throw Error("Unknown monitor shape: " shapeName)
    }
}

HandleDestinationMonitor(slots, monitorName, armOnly) {
    choicePath := A_ScriptDir "\\runtime\\placement-choice.ini"
    shape := FileExist(choicePath) ? IniRead(choicePath, "Placement", "shape", "") : ""
    if shape != "" {
        PromoteSelectedWindow(GetMonitorShape(slots, monitorName, shape))
        return
    }
    if armOnly {
        DirCreate(A_ScriptDir "\\runtime")
        IniWrite(StrUpper(monitorName), choicePath, "Placement", "monitor")
        return
    }
    PromoteSelectedWindow(GetMonitorShape(slots, monitorName, "full"))
}

HandleDestinationShape(slots, shapeName) {
    shape := StrLower(shapeName)
    if !InStr("|full|left|right|top|bottom|", "|" shape "|")
        throw Error("Unknown destination shape: " shapeName)
    choicePath := A_ScriptDir "\\runtime\\placement-choice.ini"
    monitor := FileExist(choicePath) ? IniRead(choicePath, "Placement", "monitor", "") : ""
    if monitor != "" {
        PromoteSelectedWindow(GetMonitorShape(slots, monitor, shape))
        return
    }
    DirCreate(A_ScriptDir "\\runtime")
    IniWrite(shape, choicePath, "Placement", "shape")
}

ClearPlacementChoice() {
    choicePath := A_ScriptDir "\\runtime\\placement-choice.ini"
    if FileExist(choicePath)
        FileDelete(choicePath)
}

SavePromotionOrigin(hwnd) {
    promotionPath := A_ScriptDir "\\runtime\\window-promotion.ini"
    rect := GetWindowRect(hwnd)
    DirCreate(A_ScriptDir "\\runtime")
    if FileExist(promotionPath)
        FileDelete(promotionPath)
    IniWrite(hwnd, promotionPath, "Promotion", "hwnd")
    IniWrite(WinGetPID("ahk_id " hwnd), promotionPath, "Promotion", "pid")
    IniWrite(rect["x"], promotionPath, "Promotion", "x")
    IniWrite(rect["y"], promotionPath, "Promotion", "y")
    IniWrite(rect["w"], promotionPath, "Promotion", "w")
    IniWrite(rect["h"], promotionPath, "Promotion", "h")
}

ReturnPromotedWindow() {
    promotionPath := A_ScriptDir "\\runtime\\window-promotion.ini"
    if !FileExist(promotionPath)
        throw Error("No promoted window is available to return.")
    hwnd := Integer(IniRead(promotionPath, "Promotion", "hwnd", "0"))
    expectedPid := Integer(IniRead(promotionPath, "Promotion", "pid", "0"))
    if !hwnd || !WinExist("ahk_id " hwnd) || !expectedPid || WinGetPID("ahk_id " hwnd) != expectedPid {
        FileDelete(promotionPath)
        throw Error("The promoted window is no longer available.")
    }
    rect := Map(
        "x", Integer(IniRead(promotionPath, "Promotion", "x", "0")),
        "y", Integer(IniRead(promotionPath, "Promotion", "y", "0")),
        "w", Integer(IniRead(promotionPath, "Promotion", "w", "0")),
        "h", Integer(IniRead(promotionPath, "Promotion", "h", "0"))
    )
    MoveWindow(hwnd, rect)
    WinActivate("ahk_id " hwnd)
    FileDelete(promotionPath)
}

HandleSlotPress(slot) {
    cyclePath := A_ScriptDir "\\runtime\\window-cycle.ini"
    selectedHwnd := GetSelectedWindow()
    if selectedHwnd && FileExist(cyclePath) {
        cycleSlot := IniRead(cyclePath, "Cycle", "slot", "")
        if cycleSlot = slot["name"] {
            CycleSelectedWindow(slot)
            return
        }
        MoveWindow(selectedHwnd, slot)
        WinActivate("ahk_id " selectedHwnd)
        ClearWindowSelection()
        return
    }
    if FileExist(cyclePath)
        ClearCycleMode()

    if selectedHwnd {
        MoveWindow(selectedHwnd, slot)
        WinActivate("ahk_id " selectedHwnd)
        ClearWindowSelection()
        return
    }

    hwnd := FindWindowInSlot(slot)
    if !hwnd
        throw Error("No movable window occupies the selected slot.")
    SelectWindow(hwnd, slot["name"])
    WinRestore("ahk_id " hwnd)
    WinActivate("ahk_id " hwnd)
}

EnterOrCommitCycleMode(slot) {
    cyclePath := A_ScriptDir "\\runtime\\window-cycle.ini"
    selectedHwnd := GetSelectedWindow()
    if !selectedHwnd
        throw Error("Select a window from this quadrant before entering cycle mode.")

    selectionPath := A_ScriptDir "\\runtime\\window-selection.ini"
    sourceSlot := IniRead(selectionPath, "Selection", "source_slot", "")
    if sourceSlot != slot["name"]
        throw Error("Cycle mode must be entered from the selected source quadrant.")

    if FileExist(cyclePath) && IniRead(cyclePath, "Cycle", "slot", "") = slot["name"] {
        MoveWindow(selectedHwnd, slot)
        WinActivate("ahk_id " selectedHwnd)
        ClearWindowSelection()
        return
    }

    candidates := FindWindowsInSlot(slot)
    if candidates.Length < 1
        throw Error("No cycle candidates occupy the selected quadrant.")

    DirCreate(A_ScriptDir "\\runtime")
    if FileExist(cyclePath)
        FileDelete(cyclePath)
    IniWrite(slot["name"], cyclePath, "Cycle", "slot")
    IniWrite(candidates.Length, cyclePath, "Cycle", "count")
    selectedIndex := 0
    for index, hwnd in candidates {
        section := "Window:" index
        IniWrite(hwnd, cyclePath, section, "hwnd")
        IniWrite(WinGetPID("ahk_id " hwnd), cyclePath, section, "pid")
        if hwnd = selectedHwnd
            selectedIndex := index
    }
    if selectedIndex = 0 {
        selectedIndex := 1
        SelectWindow(candidates[1], slot["name"])
        WinRestore("ahk_id " candidates[1])
        WinActivate("ahk_id " candidates[1])
    }
    IniWrite(selectedIndex, cyclePath, "Cycle", "index")
}

CycleSelectedWindow(slot) {
    cyclePath := A_ScriptDir "\\runtime\\window-cycle.ini"
    count := Integer(IniRead(cyclePath, "Cycle", "count", "0"))
    index := Integer(IniRead(cyclePath, "Cycle", "index", "0"))
    if count < 1 {
        ClearCycleMode()
        throw Error("The cycle candidate list is empty.")
    }

    Loop count {
        index := Mod(index, count) + 1
        section := "Window:" index
        hwnd := Integer(IniRead(cyclePath, section, "hwnd", "0"))
        expectedPid := Integer(IniRead(cyclePath, section, "pid", "0"))
        if hwnd && WinExist("ahk_id " hwnd) && expectedPid && WinGetPID("ahk_id " hwnd) = expectedPid {
            IniWrite(index, cyclePath, "Cycle", "index")
            SelectWindow(hwnd, slot["name"])
            WinRestore("ahk_id " hwnd)
            WinActivate("ahk_id " hwnd)
            return
        }
    }
    ClearCycleMode()
    ClearWindowSelection()
    throw Error("No cycle candidate windows remain available.")
}

ClearCycleMode() {
    cyclePath := A_ScriptDir "\\runtime\\window-cycle.ini"
    if FileExist(cyclePath)
        FileDelete(cyclePath)
}

GetSelectedWindow() {
    selectionPath := A_ScriptDir "\runtime\window-selection.ini"
    if !FileExist(selectionPath)
        return 0
    hwnd := Integer(IniRead(selectionPath, "Selection", "hwnd", "0"))
    expectedPid := Integer(IniRead(selectionPath, "Selection", "pid", "0"))
    if hwnd && WinExist("ahk_id " hwnd) && expectedPid && WinGetPID("ahk_id " hwnd) = expectedPid
        return hwnd
    ClearWindowSelection()
    return 0
}

FindWindowsInSlot(slot) {
    candidates := []
    for hwnd in WinGetList() {
        try {
            if WinGetMinMax("ahk_id " hwnd) = -1
                continue
            title := WinGetTitle("ahk_id " hwnd)
            className := WinGetClass("ahk_id " hwnd)
            if title = "" || className = "Progman" || className = "WorkerW"
                continue
            WinGetPos(&x, &y, &w, &h, "ahk_id " hwnd)
            overlapWidth := Max(0, Min(x + w, slot["x"] + slot["w"]) - Max(x, slot["x"]))
            overlapHeight := Max(0, Min(y + h, slot["y"] + slot["h"]) - Max(y, slot["y"]))
            if overlapWidth * overlapHeight > 0
                candidates.Push(hwnd)
        }
    }
    return candidates
}

FindWindowInSlot(slot) {
    candidates := FindWindowsInSlot(slot)
    return candidates.Length > 0 ? candidates[1] : 0
}

ClearWindowSelection() {
    selectionPath := A_ScriptDir "\runtime\window-selection.ini"
    if FileExist(selectionPath)
        FileDelete(selectionPath)
    ClearPlacementChoice()
    ClearCycleMode()
}

MoveWindowToConfiguredSlot(hwnd, target, slots) {
    slotName := target["slot"]
    if slotName = ""
        return
    MoveWindow(hwnd, GetSlot(slots, slotName))
}

FindTargetWindow(target) {
    global bindingsPath

    if FileExist(bindingsPath) {
        boundHwnd := IniRead(bindingsPath, "Bindings", target["name"], "")
        if boundHwnd != "" {
            expectedPid := Integer(IniRead(bindingsPath, "BindingMeta:" target["name"], "pid", "0"))
            if WinExist("ahk_id " boundHwnd) && expectedPid != 0 && WinGetPID("ahk_id " boundHwnd) = expectedPid
                return Integer(boundHwnd)
            IniDelete(bindingsPath, "Bindings", target["name"])
            IniDelete(bindingsPath, "BindingMeta:" target["name"])
        }
    }

    matchRule := target["match"]
    if matchRule = ""
        throw Error("Target is missing a window match rule.")
    return WinExist(matchRule)
}

BindActiveTarget(target) {
    global bindingsPath

    hwnd := WinExist("A")
    if !hwnd
        throw Error("No active window found to bind.")
    DirCreate(A_ScriptDir "\runtime")
    IniWrite(hwnd, bindingsPath, "Bindings", target["name"])
    IniWrite(WinGetTitle("ahk_id " hwnd), bindingsPath, "BindingMeta:" target["name"], "title")
    IniWrite(WinGetProcessName("ahk_id " hwnd), bindingsPath, "BindingMeta:" target["name"], "process")
    IniWrite(WinGetPID("ahk_id " hwnd), bindingsPath, "BindingMeta:" target["name"], "pid")
}

UnbindTarget(target) {
    global bindingsPath

    if !FileExist(bindingsPath)
        return
    IniDelete(bindingsPath, "Bindings", target["name"])
    IniDelete(bindingsPath, "BindingMeta:" target["name"])
}

GetWindowRect(hwnd) {
    WinGetPos(&x, &y, &w, &h, "ahk_id " hwnd)
    return Map("x", x, "y", y, "w", w, "h", h)
}

MoveWindow(hwnd, rect, recordUndo := true) {
    WinRestore("ahk_id " hwnd)
    if recordUndo
        SaveUndoTransaction([hwnd])
    WinMove(rect["x"], rect["y"], rect["w"], rect["h"], "ahk_id " hwnd)
}

SaveUndoTransaction(hwnds) {
    undoPath := A_ScriptDir "\runtime\window-undo.ini"
    DirCreate(A_ScriptDir "\runtime")
    if FileExist(undoPath)
        FileDelete(undoPath)
    IniWrite(hwnds.Length, undoPath, "Undo", "count")
    for index, hwnd in hwnds {
        rect := GetWindowRect(hwnd)
        section := "Window:" index
        IniWrite(hwnd, undoPath, section, "hwnd")
        IniWrite(WinGetPID("ahk_id " hwnd), undoPath, section, "pid")
        IniWrite(rect["x"], undoPath, section, "x")
        IniWrite(rect["y"], undoPath, section, "y")
        IniWrite(rect["w"], undoPath, section, "w")
        IniWrite(rect["h"], undoPath, section, "h")
    }
}

UndoLastMove() {
    undoPath := A_ScriptDir "\runtime\window-undo.ini"
    if !FileExist(undoPath)
        throw Error("No window movement is available to undo.")

    count := Integer(IniRead(undoPath, "Undo", "count", "0"))
    if count < 1
        throw Error("The undo record is invalid.")

    restoreItems := []
    Loop count {
        section := "Window:" A_Index
        hwnd := Integer(IniRead(undoPath, section, "hwnd", "0"))
        expectedPid := Integer(IniRead(undoPath, section, "pid", "0"))
        if !hwnd || !WinExist("ahk_id " hwnd) || !expectedPid || WinGetPID("ahk_id " hwnd) != expectedPid {
            FileDelete(undoPath)
            throw Error("An undo window is no longer available.")
        }
        restoreItems.Push(Map(
            "hwnd", hwnd,
            "rect", Map(
                "x", Integer(IniRead(undoPath, section, "x", "0")),
                "y", Integer(IniRead(undoPath, section, "y", "0")),
                "w", Integer(IniRead(undoPath, section, "w", "0")),
                "h", Integer(IniRead(undoPath, section, "h", "0"))
            )
        ))
    }

    for item in restoreItems
        MoveWindow(item["hwnd"], item["rect"], false)
    FileDelete(undoPath)
}

GetTarget(targets, name) {
    if !targets.Has(name)
        throw Error("Unknown target: " name)
    return targets[name]
}

GetSlot(slots, name) {
    if !slots.Has(name)
        throw Error("Unknown slot: " name)
    return slots[name]
}

RequireArgument(value, label) {
    if value = ""
        DieWithUsage("Missing " label ".")
}

StartsWith(value, prefix) {
    return SubStr(value, 1, StrLen(prefix)) = prefix
}

DieWithUsage(message := "") {
    usage := "Estate Operator Deck Prototype`n`n"
        . (message != "" ? message "`n`n" : "")
        . "Usage:`n"
        . "  OperatorDeck.ahk target <TargetName>`n"
        . "  OperatorDeck.ahk swap <TargetName>`n"
        . "  OperatorDeck.ahk move-active <SlotName>`n"
        . "  OperatorDeck.ahk place <TargetName> <SlotName>`n"
        . "  OperatorDeck.ahk select <TargetName>`n"
        . "  OperatorDeck.ahk select-active`n"
        . "  OperatorDeck.ahk place-selected <SlotName>`n"
        . "  OperatorDeck.ahk promote-selected <SlotName>`n"
        . "  OperatorDeck.ahk promote-monitor <M1|M2|M3|M4> <full|left|right|top|bottom>`n"
        . "  OperatorDeck.ahk destination-monitor <M1|M2|M3|M4>`n"
        . "  OperatorDeck.ahk arm-monitor <M1|M2|M3|M4>`n"
        . "  OperatorDeck.ahk destination-shape <left|right|top|bottom>`n"
        . "  OperatorDeck.ahk return-promoted`n"
        . "  OperatorDeck.ahk slot <SlotName>`n"
        . "  OperatorDeck.ahk clear-selection`n"
        . "  OperatorDeck.ahk undo`n"
        . "  OperatorDeck.ahk activate <TargetName>`n"
        . "  OperatorDeck.ahk dictation-toggle`n"
        . "  OperatorDeck.ahk bind <TargetName>`n"
        . "  OperatorDeck.ahk unbind <TargetName>`n"
    MsgBox(usage, "Operator Deck", "Icon!")
    ExitApp(1)
}
