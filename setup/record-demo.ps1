<#
    Screen-record the Gazebo simulation for the dissertation summary video.

    Uses the Windows ffmpeg (already installed via winget) with gdigrab, so
    nothing needs installing inside WSL. WSLg windows are real Windows windows,
    so gdigrab can capture them directly.

    Note: PrintWindow-based capture renders WSLg windows black. gdigrab reads
    the composited screen instead, which is why it works where screenshot tools
    do not.

    Examples
        .\setup\record-demo.ps1                          # whole desktop, until Q
        .\setup\record-demo.ps1 -Window "Gazebo"         # just the Gazebo window
        .\setup\record-demo.ps1 -Seconds 90 -Fps 24      # fixed length, smaller file

    Stop early with Q in the ffmpeg window, or Ctrl+C.
#>
param(
    [string] $Window  = "",                     # window title; empty = full desktop
    [int]    $Seconds = 0,                      # 0 = record until stopped
    [int]    $Fps     = 30,
    [string] $OutDir  = "$PSScriptRoot\..\results\demo-footage"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Error "ffmpeg not found on PATH. It was installed via winget (Gyan.FFmpeg); reopen the shell or reinstall."
}

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out   = Join-Path $OutDir "sim_$stamp.mp4"

if ($Window) {
    $found = Get-Process | Where-Object { $_.MainWindowTitle -like "*$Window*" }
    if (-not $found) {
        Write-Warning "No window matching '$Window'. Open windows:"
        Get-Process | Where-Object { $_.MainWindowTitle -ne '' } |
            Select-Object ProcessName, MainWindowTitle | Format-Table -AutoSize
        Write-Error "Launch the simulation first, then re-run."
    }
    Write-Host "Capturing window: $($found[0].MainWindowTitle)" -ForegroundColor Cyan
    $input = "title=$($found[0].MainWindowTitle)"
} else {
    Write-Host "Capturing full desktop" -ForegroundColor Cyan
    $input = "desktop"
}

$args = @(
    "-hide_banner", "-loglevel", "warning", "-stats",
    "-f", "gdigrab", "-framerate", $Fps, "-i", $input,
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
    "-pix_fmt", "yuv420p"          # required or QuickTime/PowerPoint won't play it
)
if ($Seconds -gt 0) { $args += @("-t", $Seconds) }
$args += $out

Write-Host "Recording -> $out" -ForegroundColor Green
Write-Host "Press Q in this window to stop." -ForegroundColor Yellow
& ffmpeg @args

if (Test-Path $out) {
    $mb = [math]::Round((Get-Item $out).Length / 1MB, 1)
    Write-Host "`nWrote $out  ($mb MB)" -ForegroundColor Green
    Write-Host "results/demo-footage/ is gitignored - keep the file somewhere that travels." -ForegroundColor Yellow
} else {
    Write-Error "ffmpeg produced no output file."
}
