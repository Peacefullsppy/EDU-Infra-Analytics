# Executar no host Hyper-V após login na API e aceite dos Termos e Condições.
# Segurança: informe o JWT em prompt; jamais salve credenciais no script/controle de versão.
param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][int]$LaboratoryId
)
$ErrorActionPreference = 'Stop'
$ApiUrl = $ApiUrl.TrimEnd('/')
$uri = [Uri]$ApiUrl
if ($uri.Scheme -ne 'https' -and $uri.Host -notin @('127.0.0.1','localhost')) { throw 'HTTPS obrigatório fora de localhost.' }
Import-Module Hyper-V -ErrorAction Stop
$vms = @(Get-VM | ForEach-Object { @{ vm_id = $_.VMId.ToString(); name = $_.Name; state = $_.State.ToString() } })
if ($vms.Count -eq 0) { Write-Host 'Nenhuma VM; nada foi enviado.'; exit 0 }
$secure = Read-Host -AsSecureString 'JWT do usuário autorizado (Bearer)'
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try { $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
$body = @{ laboratory_id = $LaboratoryId; vms = $vms } | ConvertTo-Json -Depth 6
try {
  $result = Invoke-RestMethod -Uri "$ApiUrl/api/hyperv/import" -Method Post -ContentType 'application/json' -Headers @{Authorization="Bearer $token"} -Body $body
  Write-Host "Inventário sincronizado: criadas=$($result.created) atualizadas=$($result.updated)"
} finally { Remove-Variable token -ErrorAction SilentlyContinue }
