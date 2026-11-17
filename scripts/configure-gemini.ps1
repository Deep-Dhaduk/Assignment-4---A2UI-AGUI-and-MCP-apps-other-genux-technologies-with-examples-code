$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectRoot '.env'
$secret = Read-Host 'Paste your Gemini API key (hidden; saved only in ignored .env)' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    if ([string]::IsNullOrWhiteSpace($key) -or $key -match '[\r\n]') {
        throw 'A nonempty, single-line API key is required.'
    }
    $config = "GEMINI_API_KEY=$key`nMODEL=gemini-2.5-flash`n"
    [IO.File]::WriteAllText($envPath, $config, [Text.UTF8Encoding]::new($false))
    Write-Host 'Gemini key saved locally. No API request was made.'
    Write-Host 'Confirm this model has free quota in your AI Studio project before running live demos.'
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    $key = $null
    $config = $null
}
