<#
build_exe.ps1

Usage (PowerShell) :
    .\build_exe.ps1 -ScriptPath .\encrypt_folder_cli.py -ExeName M-Encrypt -IconPath .\icon.ico

Paramètres :
    -ScriptPath : chemin vers le script python à convertir (par défaut ./encrypt_folder_cli.py)
    -ExeName    : nom de l'exécutable de sortie (par défaut: EncryptFolderCli)
    -IconPath   : chemin vers .ico optionnel (par défaut: none)
    -OneFile    : switch pour --onefile (par défaut : présent)
    -NoConsole  : switch pour cacher la console (supprimer --console)
#>

param(
    [string]$ScriptPath = ".\encrypt_folder_cli.py",
    [string]$ExeName = "EncryptFolderCli",
    [string]$IconPath = "",
    [switch]$OneFile = $true,
    [switch]$NoConsole = $false
)

$ErrorActionPreference = "Stop"

function Write-Info($msg){ Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg){ Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Err($msg){ Write-Host "[ERR] $msg" -ForegroundColor Red }

# Vérifier que le script Python existe
if (-Not (Test-Path $ScriptPath)) {
    Write-Err "Script introuvable : $ScriptPath"
    exit 1
}

# Définir le venv
$venvDir = ".\venv"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"

# Créer venv si nécessaire
if (-Not (Test-Path $pythonExe)) {
    Write-Info "Création de l'environnement virtuel dans $venvDir ..."
    python -m venv $venvDir
    if (-Not (Test-Path $pythonExe)) {
        Write-Err "Impossible de créer le venv. Assurez-vous que 'python' est dans le PATH."
        exit 1
    }
    Write-Ok "venv créé."
} else {
    Write-Info "venv existant détecté."
}

# Résoudre le chemin complet de python.exe
$pythonExe = (Resolve-Path "$venvDir\Scripts\python.exe").Path

# Mettre pip à jour
Write-Info "Mise à jour de pip..."
& $pythonExe -m pip install --upgrade pip setuptools wheel | Out-Null
Write-Ok "pip mis à jour."

# Installer dépendances nécessaires via python -m pip
$reqs = @("cryptography","colorama","pyinstaller")
Write-Info "Installation des paquets : $($reqs -join ', ')"
& $pythonExe -m pip install --upgrade @reqs
Write-Ok "Dépendances installées."

# Nettoyer les anciens builds
$distDir = ".\dist"
$buildDir = ".\build"
$outDir = ".\release"
if (Test-Path $distDir) { Remove-Item $distDir -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path $outDir) { Remove-Item $outDir -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $outDir | Out-Null

# Préparer les arguments pour PyInstaller
$pyInstallerArgs = @()
if ($OneFile) { $pyInstallerArgs += "--onefile" } else { $pyInstallerArgs += "--onedir" }
if (-Not $NoConsole) { $pyInstallerArgs += "--console" } else { $pyInstallerArgs += "--noconsole" }

$pyInstallerArgs += "--name"
$pyInstallerArgs += $ExeName

if ($IconPath -and (Test-Path $IconPath)) {
    $pyInstallerArgs += "--icon"
    $pyInstallerArgs += (Resolve-Path $IconPath).Path
    Write-Info "Icône fournie : $IconPath"
} elseif ($IconPath) {
    Write-Info "Icon path fourni mais introuvable : $IconPath (ignoring icon)"
}

# Résoudre le chemin complet du script
$scriptFull = (Resolve-Path $ScriptPath).Path

# Lancer PyInstaller avec gestion correcte des espaces
Write-Info "Lancement de PyInstaller..."
Write-Info ("Commande: " + $pythonExe + " -m PyInstaller " + ($pyInstallerArgs + $scriptFull | ForEach-Object { "`"$_`"" } | Out-String))

& $pythonExe -m PyInstaller @pyInstallerArgs $scriptFull
if ($LASTEXITCODE -ne 0) {
    Write-Err "PyInstaller a échoué (exit code $LASTEXITCODE)"
    exit $LASTEXITCODE
}

# Rassembler l'exécutable final dans release\
$exePath = Join-Path $distDir ($ExeName + ".exe")
if (-Not (Test-Path $exePath)) {
    # PyInstaller peut mettre l'exe dans dist\<name>\<name>.exe
    $possible = Get-ChildItem -Path $distDir -Recurse -Filter ($ExeName + ".exe") -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($possible) { $exePath = $possible.FullName }
}

if (-Not (Test-Path $exePath)) {
    Write-Err "Exécutable introuvable après PyInstaller."
    exit 1
}

Copy-Item $exePath -Destination $outDir -Force
if (Test-Path ".\requirements.txt") { Copy-Item ".\requirements.txt" $outDir -Force }

Write-Ok "Exécutable copié dans $outDir"

Write-Host ""
Write-Host "———————————— Résumé ————————————" -ForegroundColor Cyan
Write-Host "Executable: $(Join-Path (Resolve-Path $outDir).Path (Split-Path $exePath -Leaf))" -ForegroundColor Green
Write-Host "Release folder: $(Resolve-Path $outDir)" -ForegroundColor Green
Write-Host ""
Write-Host "Conseils:" -ForegroundColor Yellow
Write-Host "- Tester l'exécutable dans une VM avant distribution."
Write-Host "- Pour créer un installateur .msi/.exe, utilise Inno Setup."
