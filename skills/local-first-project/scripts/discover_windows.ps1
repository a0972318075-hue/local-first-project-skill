[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^[\p{L}\p{N}][\p{L}\p{N} ._+-]{0,79}\z')]
    [string]$Product,
    [ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}\z')]
    [string]$Command,
    [string]$KnownPath
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$evidence = [System.Collections.Generic.List[object]]::new()
function Add-Evidence($Source, $Status, $Details) {
    $evidence.Add([ordered]@{source=$Source; status=$Status; details=@($Details)})
}
if ($env:OS -ne 'Windows_NT') { throw 'This collector requires Windows.' }

# Literal matching; no evaluation of input, found commands, or shortcut targets.
$needle = [regex]::Escape($Product)
try {
    $matches = @(Get-Process | Where-Object { $_.ProcessName -match $needle } |
        ForEach-Object {
            $processPath = $null
            try { $processPath = $_.Path } catch { }
            [ordered]@{name=$_.ProcessName; path=$processPath}
        })
    Add-Evidence 'process' $(if ($matches.Count) {'found'} else {'not-found'}) $matches
} catch { Add-Evidence 'process' 'error' @($_.Exception.GetType().Name) }

if ($Command) {
    try {
        $commands = @(Get-Command -Name $Command -CommandType Application -ErrorAction SilentlyContinue)
        Add-Evidence 'path' $(if ($commands.Count) {'found'} else {'not-found'}) @($commands | ForEach-Object { $_.Source })
    } catch { Add-Evidence 'path' 'error' @($_.Exception.GetType().Name) }
} else { Add-Evidence 'path' 'unchecked' @('Supply -Command to inspect PATH') }

if ($KnownPath) {
    try {
        $exists = Test-Path -LiteralPath $KnownPath -PathType Leaf
        Add-Evidence 'known-path' $(if ($exists) {'found'} else {'not-found'}) @($KnownPath)
    } catch { Add-Evidence 'known-path' 'error' @($_.Exception.GetType().Name) }
} else { Add-Evidence 'known-path' 'unchecked' @('No known path supplied') }

foreach ($root in @(
    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall',
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall')) {
    try {
        if (-not (Test-Path -LiteralPath $root)) {
            Add-Evidence "registry:$root" 'not-found' @()
            continue
        }
        $items = @(Get-ItemProperty -Path "$root\*" | Where-Object { $_.DisplayName -match $needle } |
            ForEach-Object { [ordered]@{name=$_.DisplayName; version=$_.DisplayVersion; location=$_.InstallLocation} })
        Add-Evidence "registry:$root" $(if ($items.Count) {'found'} else {'not-found'}) $items
    } catch { Add-Evidence "registry:$root" 'error' @($_.Exception.GetType().Name) }
}

foreach ($menu in @([Environment]::GetFolderPath('StartMenu'), [Environment]::GetFolderPath('CommonStartMenu'))) {
    try {
        $shortcuts = @(Get-ChildItem -LiteralPath $menu -Filter '*.lnk' -Recurse |
            Where-Object { $_.BaseName -match $needle } | ForEach-Object { $_.FullName })
        Add-Evidence 'start-menu' $(if ($shortcuts.Count) {'found'} else {'not-found'}) $shortcuts
    } catch { Add-Evidence 'start-menu' 'error' @($_.Exception.GetType().Name) }
}

[ordered]@{
    schema_version=1
    observed_at=[DateTime]::UtcNow.ToString('o')
    product=$Product
    status=$(if (@($evidence | Where-Object { $_.status -eq 'found' }).Count) {'found-unverified'} else {'unknown'})
    evidence=@($evidence.ToArray())
    limitations=@(
        'Candidates are name/path matches, not product identity or functional verification.',
        'Process names may differ from product names; specify Command or KnownPath when known.',
        'No GUI, package-manager, custom-directory, credential or network checks.',
        'Output can contain local installation paths; review before publishing.',
        'No matches does not prove absence. No software was executed or installed.'
    )
} | ConvertTo-Json -Depth 8
