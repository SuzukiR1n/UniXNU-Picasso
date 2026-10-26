param(
    [string]$Fastboot = 'fastboot',
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\inputs')
)
$ErrorActionPreference = 'Stop'
$null = Get-Command $Fastboot -ErrorAction Stop
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$record = [ordered]@{
    captured_at = (Get-Date).ToString('o')
    mode = 'read-only fastboot getvar'
    variables = [ordered]@{}
}
# Avoid getvar all and serialno: only collect the facts needed for this board.
foreach ($variable in @('product', 'unlocked', 'secure', 'max-download-size',
                        'partition-size:boot', 'partition-size:recovery',
                        'partition-size:dtbo', 'partition-size:userdata')) {
    $answer = & $Fastboot getvar $variable 2>&1
    $record.variables[$variable] = ($answer | ForEach-Object { "$_" }) -join "`n"
}
$path = Join-Path $OutputDirectory 'fastboot-info.json'
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding UTF8
Write-Output $path
