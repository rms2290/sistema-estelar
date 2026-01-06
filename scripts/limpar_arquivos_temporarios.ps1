# Script para limpar arquivos temporários do projeto
# Uso: .\scripts\limpar_arquivos_temporarios.ps1

Write-Host "=== Limpando Arquivos Temporarios ===" -ForegroundColor Cyan

$arquivosParaRemover = @(
    "test_server_error.log",
    "test_server.log",
    "server_error.txt",
    "server_output.txt",
    "backup_db_20251126_082039.sqlite3"
)

$removidos = 0
$naoEncontrados = 0

foreach ($arquivo in $arquivosParaRemover) {
    $caminho = Join-Path $PSScriptRoot "..\$arquivo"
    if (Test-Path $caminho) {
        Remove-Item $caminho -Force
        Write-Host "  [OK] Removido: $arquivo" -ForegroundColor Green
        $removidos++
    } else {
        Write-Host "  [INFO] Nao encontrado: $arquivo" -ForegroundColor Gray
        $naoEncontrados++
    }
}

Write-Host "`n=== Resumo ===" -ForegroundColor Cyan
Write-Host "  Arquivos removidos: $removidos" -ForegroundColor Green
Write-Host "  Arquivos nao encontrados: $naoEncontrados" -ForegroundColor Gray

Write-Host "`nNota: Arquivos em logs/ nao foram removidos (podem ser uteis para debug)" -ForegroundColor Yellow
Write-Host "Para limpar logs tambem, execute: Remove-Item logs\*.log, logs\*.txt -Force" -ForegroundColor Yellow


