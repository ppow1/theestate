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
    MoveWindow(activeHwnd, targetRect)
    MoveWindow(targetHwnd, activeRect)
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

MoveWindow(hwnd, rect) {
    WinRestore("ahk_id " hwnd)
    WinMove(rect["x"], rect["y"], rect["w"], rect["h"], "ahk_id " hwnd)
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
        . "  OperatorDeck.ahk activate <TargetName>`n"
        . "  OperatorDeck.ahk dictation-toggle`n"
        . "  OperatorDeck.ahk bind <TargetName>`n"
        . "  OperatorDeck.ahk unbind <TargetName>`n"
    MsgBox(usage, "Operator Deck", "Icon!")
    ExitApp(1)
}
