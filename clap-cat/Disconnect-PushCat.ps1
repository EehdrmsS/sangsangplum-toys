# Run after closing PushCat, from the original app folder.
$includeFile = (Join-Path $PSScriptRoot 'pushcat.gitconfig').Replace('\', '/')
git config --global --fixed-value --unset-all include.path $includeFile
if ($LASTEXITCODE -in 0, 5) {
    Write-Host 'PushCat Git connection removed.'
} else {
    Write-Error 'Could not remove the PushCat connection. Check Git installation and config permissions.'
}
