# VPN Cloud Project - Quick Start Script (Windows PowerShell)

$ErrorActionPreference = 'Stop'

Write-Host "=========================================="
Write-Host "VPN Cloud Project - Quick Start (Windows)"
Write-Host "=========================================="
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed or not in PATH"
    Write-Host "Install Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/"
    exit 1
}

$dockerInfo = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Desktop is not running"
    Write-Host "Start Docker Desktop, then run this script again"
    exit 1
}

Write-Host "✓ Docker is available"
Write-Host ""

if (-not (Test-Path "certs")) {
    New-Item -ItemType Directory -Path "certs" | Out-Null
}

if (-not (Test-Path "certs/privkey.pem") -or -not (Test-Path "certs/fullchain.pem")) {
    Write-Host "Generating self-signed certificate for localhost..."

    $cert = New-SelfSignedCertificate `
        -DnsName "localhost" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddDays(365)

    $pfxPath = Join-Path $PWD "certs\localhost.pfx"
    $pemPath = Join-Path $PWD "certs\fullchain.pem"
    $keyPath = Join-Path $PWD "certs\privkey.pem"
    $password = ConvertTo-SecureString -String "vpncloud" -Force -AsPlainText

    Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password | Out-Null

    if (Get-Command openssl -ErrorAction SilentlyContinue) {
        openssl pkcs12 -in $pfxPath -clcerts -nokeys -out $pemPath -passin pass:vpncloud 2>$null
        openssl pkcs12 -in $pfxPath -nocerts -nodes -out $keyPath -passin pass:vpncloud 2>$null
        Remove-Item $pfxPath -Force
        Write-Host "✓ SSL certificates generated in certs/"
    } else {
        Write-Host "❌ openssl not found in PATH"
        Write-Host "Install OpenSSL or create certs/fullchain.pem and certs/privkey.pem manually"
        exit 1
    }
} else {
    Write-Host "✓ SSL certificates already exist"
}

Write-Host ""
Write-Host "Building and starting containers..."
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker compose failed"
    exit 1
}

Write-Host ""
Write-Host "✓ VPN Cloud Project is starting"
Write-Host "Web UI: https://localhost"
Write-Host "Default login: student1 / password123"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  docker compose logs -f"
Write-Host "  docker compose down"
