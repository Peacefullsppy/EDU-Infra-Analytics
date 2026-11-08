# Executar dentro de cada VM Windows, em PowerShell. Tarefa inicia no login do usuário.
param(
    [Parameter(Mandatory=$true)][string]$PythonExe,
    [Parameter(Mandatory=$true)][string]$AgentPath,
    [string]$TaskName = "EDUInfraAgent"
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $PythonExe)) { throw "Python não encontrado: $PythonExe" }
if (-not (Test-Path $AgentPath)) { throw "Agente não encontrado: $AgentPath" }
$action = New-ScheduledTaskAction -Execute $PythonExe -Argument ('"' + $AgentPath + '"') -WorkingDirectory (Split-Path -Parent $AgentPath)
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ("$env:USERDOMAIN\$env:USERNAME")
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description 'Agente EDU-Infra Analytics (coleta métricas somente da VM local)' -Force | Out-Null
Write-Host "Tarefa '$TaskName' registrada. Teste manualmente: & '$PythonExe' '$AgentPath' --once"
