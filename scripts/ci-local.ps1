# Every gate CI runs, run locally on Windows: ruff, pytest, vue-tsc, Vitest,
# oxlint, ESLint, Prettier, and the HTTP smoke test against a throwaway
# container. Needs Python with requirements-dev.txt installed, Node, and
# Docker for the smoke test alone.

$root     = Split-Path -Parent $PSScriptRoot
$backend  = Join-Path $root 'Folderly\Backend'
$frontend = Join-Path $root 'Folderly\Frontend'
$python   = Join-Path $backend 'venv_back\Scripts\python.exe'

if (-not (Test-Path $python)) {
    $onPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $onPath) {
        Write-Host 'No Python found. Create the virtualenv first:' -ForegroundColor Red
        Write-Host '  cd Folderly\Backend' -ForegroundColor Red
        Write-Host '  python -m venv venv_back' -ForegroundColor Red
        Write-Host '  venv_back\Scripts\python.exe -m pip install -r requirements-dev.txt' -ForegroundColor Red
        exit 1
    }
    Write-Host "venv_back not found - falling back to $onPath" -ForegroundColor Yellow
    $python = $onPath
}

# ruff and pytest live in requirements-dev.txt, which the image does not have.
& $python -m ruff --version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Dev dependencies missing. Install them with:' -ForegroundColor Red
    Write-Host "  $python -m pip install -r Folderly\Backend\requirements-dev.txt" -ForegroundColor Red
    exit 1
}

docker version --format '{{.Server.Version}}' 2>$null | Out-Null
$hasDocker = $LASTEXITCODE -eq 0
if (-not $hasDocker) {
    Write-Host 'Docker is not responding - the smoke test will be skipped.' -ForegroundColor Yellow
}

# The smoke test gets its own image, container and data directories, so it
# never touches the database or the files of your own dev instance.
$image     = 'folderly-backend:test-all'
$container = 'folderly-test-all'
$port      = 5050
$dataRoot  = Join-Path $env:TEMP 'folderly-test-all'

$results = [ordered]@{}

function Step($name, $block) {
    Write-Host ''
    Write-Host "=== $name " -ForegroundColor Cyan -NoNewline
    Write-Host ('=' * [Math]::Max(1, 60 - $name.Length)) -ForegroundColor Cyan
    & $block
    if ($LASTEXITCODE -eq 0) { $results[$name] = 'PASS' }
    else                     { $results[$name] = "FAIL (exit $LASTEXITCODE)" }
}

Push-Location $backend
Step 'backend: ruff'   { & $python -m ruff check . }
Step 'backend: pytest' { & $python -m pytest }
Pop-Location

Push-Location $frontend
if (-not (Test-Path 'node_modules')) {
    Write-Host 'node_modules missing - running npm ci' -ForegroundColor Yellow
    npm ci
}
Step 'frontend: vitest'   { npx vitest run }
Step 'frontend: vue-tsc'  { npx vue-tsc --build }
Step 'frontend: oxlint'   { npx oxlint . }
Step 'frontend: eslint'   { npx eslint . --cache }
Step 'frontend: prettier' { npx prettier --check . }
Pop-Location

if (-not $hasDocker) {
    $results['backend: smoke (HTTP, in a container)'] = 'SKIPPED (no Docker)'
}
else {
Step 'backend: smoke (HTTP, in a container)' {
    $global:LASTEXITCODE = 0
    New-Item -ItemType Directory -Force -Path (Join-Path $dataRoot 'files') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $dataRoot 'db')    | Out-Null
    $files = (Join-Path $dataRoot 'files') -replace '\\', '/'
    $db    = (Join-Path $dataRoot 'db')    -replace '\\', '/'

    docker rm -f $container 2>$null | Out-Null
    docker build -t $image $backend
    if ($LASTEXITCODE -ne 0) { return }

    $secret = & $python -c "import secrets; print(secrets.token_hex(32))"
    docker run -d --name $container -p "${port}:5000" `
        -e DISK_PATH=/data -e DB_DIR=/db -e "JWT_SECRET_KEY=$secret" `
        -v "${files}:/data" -v "${db}:/db" $image | Out-Null
    if ($LASTEXITCODE -ne 0) { return }

    try {
        $up = $false
        foreach ($attempt in 1..30) {
            try {
                Invoke-WebRequest -Uri "http://localhost:$port/hello" -UseBasicParsing -TimeoutSec 2 | Out-Null
                Write-Host "container answered after $attempt attempt(s)"
                $up = $true
                break
            } catch { Start-Sleep -Seconds 1 }
        }
        if (-not $up) {
            Write-Host 'the container never answered:' -ForegroundColor Red
            docker logs $container
            $global:LASTEXITCODE = 1
            return
        }

        # Activation codes come only from the CLI, and each is single use, so
        # mint one inside this container rather than spending one of yours.
        $minted = docker exec $container flask --app "app:init()" codes new --label test-all
        $code = [regex]::Match(($minted -join "`n"),
            '[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}').Value
        if (-not $code) {
            Write-Host 'could not read an activation code from:' -ForegroundColor Red
            Write-Host ($minted -join "`n")
            $global:LASTEXITCODE = 1
            return
        }

        & $python (Join-Path $backend 'tests\smoke.py') "http://localhost:$port" $code
    } finally {
        $exit = $LASTEXITCODE
        docker rm -f $container 2>$null | Out-Null
        docker rmi $image 2>$null | Out-Null
        Remove-Item -Recurse -Force $dataRoot -ErrorAction SilentlyContinue
        $global:LASTEXITCODE = $exit
    }
}
}

Write-Host ''
Write-Host '=== Summary ====================================================' -ForegroundColor Cyan
foreach ($entry in $results.GetEnumerator()) {
    $colour = 'Green'
    if ($entry.Value -like 'SKIPPED*') { $colour = 'Yellow' }
    elseif ($entry.Value -ne 'PASS')   { $colour = 'Red' }
    Write-Host ("  {0,-44} {1}" -f $entry.Key, $entry.Value) -ForegroundColor $colour
}
$failed = @($results.Values | Where-Object { $_ -ne 'PASS' -and $_ -notlike 'SKIPPED*' }).Count
Write-Host ''
if ($failed -eq 0) { Write-Host 'Everything passed.' -ForegroundColor Green }
else               { Write-Host "$failed suite(s) failed." -ForegroundColor Red }
