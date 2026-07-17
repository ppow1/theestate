CLS

[CmdletBinding()]
param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'inventory')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms

if (-not ('OperatorDeck.NativeWindow' -as [type])) {
    Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;

namespace OperatorDeck {
    public static class NativeWindow {
        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        [DllImport("user32.dll")]
        public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

        [DllImport("user32.dll")]
        public static extern