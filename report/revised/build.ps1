$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & pdflatex -interaction=nonstopmode -halt-on-error main.tex
    if ($LASTEXITCODE -ne 0) { throw 'Initial LaTeX pass failed. See main.log.' }
    & bibtex main
    if ($LASTEXITCODE -ne 0) { throw 'Bibliography build failed. See main.blg.' }
    foreach ($pass in 1..2) {
        & pdflatex -interaction=nonstopmode -halt-on-error main.tex
        if ($LASTEXITCODE -ne 0) { throw "LaTeX pass $pass failed. See main.log." }
    }
    $logText = Get-Content -LiteralPath main.log -Raw
    if ($logText -match 'undefined references|Citation .* undefined|Overfull \\hbox') {
        throw 'PDF built, but unresolved citations, references, or overflowing text remain.'
    }
    Write-Output 'Built main.pdf with resolved references and no overflowing text.'
} finally {
    Pop-Location
}
