param(
    [ValidateSet('install', 'uninstall')]
    [string]$Action = 'install',
    [switch]$UsePythonw
)

# 在当前用户「启动」文件夹里创建 / 移除 device-nav 的快捷方式。
# 输出故意只用 ASCII，避免不同 PowerShell 版本读 UTF-8 脚本时中文乱码。
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$server = Join-Path $dir 'server.py'
$startup = [Environment]::GetFolderPath('Startup')
$lnkPath = Join-Path $startup 'device-nav.lnk'

if ($Action -eq 'uninstall') {
    if (Test-Path -LiteralPath $lnkPath) {
        Remove-Item -LiteralPath $lnkPath -Force
        Write-Host "[OK] removed $lnkPath"
    }
    else {
        Write-Host "[--] no autostart entry at $lnkPath"
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $server)) {
    Write-Host "[!!] server.py not found next to this script: $dir"
    exit 1
}

$python = $null
if ($UsePythonw) {
    $found = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($found) { $python = $found.Source }
}
if (-not $python) {
    $found = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($found) { $python = $found.Source }
}
if (-not $python) {
    foreach ($candidate in @(
            'C:\python313\python.exe',
            "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
        )) {
        if (Test-Path -LiteralPath $candidate) { $python = $candidate; break }
    }
}
if (-not $python) {
    Write-Host "[!!] python.exe not found. Install Python 3 and add it to PATH."
    exit 1
}

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($lnkPath)
$lnk.TargetPath = $python
$lnk.Arguments = '"' + $server + '"'
$lnk.WorkingDirectory = $dir
$lnk.WindowStyle = 7
$lnk.Description = 'device-nav: per-device navigation page'
$lnk.Save()

Write-Host "[OK] autostart created"
Write-Host "     shortcut : $lnkPath"
Write-Host "     python   : $python"
Write-Host "     server   : $server"
Write-Host "     port     : 6996, falls back to 6997-7015 when busy"
if (-not $UsePythonw) {
    Write-Host ""
    Write-Host "[i] Using python.exe (already allowed by Windows Firewall on most machines)."
    Write-Host "    A minimized console window will appear in the taskbar."
    Write-Host "    For a fully hidden window, allow pythonw.exe inbound once, then re-run:"
    Write-Host "      powershell -ExecutionPolicy Bypass -File autostart.ps1 -UsePythonw"
}
Write-Host ""
