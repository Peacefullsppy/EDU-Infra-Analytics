# Executar no host Windows com Hyper-V e PowerShell com módulo Hyper-V instalado.
# Exporta IDs únicos, nome e estado das VMs em formato aceito pela API /api/hyperv/import.
param([string]$OutputPath = ".\hyperv-inventory.json")
$ErrorActionPreference = 'Stop'
Import-Module Hyper-V -ErrorAction Stop
$vms = @(Get-VM | ForEach-Object {
    [PSCustomObject]@{
        vm_id = $_.VMId.ToString()
        name = $_.Name
        state = $_.State.ToString()
    }
})
if ($vms.Count -eq 0) { Write-Warning 'Nenhuma VM encontrada.' }
ConvertTo-Json -InputObject $vms -Depth 4 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host "Inventário exportado para $OutputPath ($($vms.Count) VM(s))."
