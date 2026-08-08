<#
    Stitch the frame sequence from capture-gazebo.sh into an mp4.

        .\setup\frames-to-video.ps1              # 15 fps playback
        .\setup\frames-to-video.ps1 -Fps 10      # slower

    Frames are captured at 2 fps, so 15 fps playback is roughly a 7x timelapse.
#>
param(
    [int]    $Fps    = 15,
    [string] $Frames = "$PSScriptRoot\..\results\demo-footage\frames",
    [string] $OutDir = "$PSScriptRoot\..\results\demo-footage"
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path $Frames)) { Write-Error "No frames at $Frames - run capture-gazebo.sh first." }
$n = (Get-ChildItem $Frames -Filter "f_*.png" | Measure-Object).Count
if ($n -eq 0) { Write-Error "No f_*.png frames in $Frames." }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out   = Join-Path $OutDir "gazebo_demo_$stamp.mp4"

Write-Host "$n frames -> $out at ${Fps}fps" -ForegroundColor Cyan
& ffmpeg -hide_banner -loglevel warning -stats `
    -framerate $Fps -i (Join-Path $Frames "f_%05d.png") `
    -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p `
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" `
    $out

if (Test-Path $out) {
    $mb  = [math]::Round((Get-Item $out).Length / 1MB, 1)
    $dur = [math]::Round($n / $Fps, 1)
    Write-Host "`nWrote $out  ($mb MB, ${dur}s)" -ForegroundColor Green
} else {
    Write-Error "ffmpeg produced no output."
}
