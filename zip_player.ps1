if ($args.Count -eq 0) {
    Write-Host "Usage: zip_with_rename.ps1 <file_path> [zipName]" -ForegroundColor Red
    exit 1
}

$filePath = $args[0]
if (-Not (Test-Path $filePath)) {
    Write-Host "The file does not exist." -ForegroundColor Red
    exit 1
}

if ($args.Count -gt 1) {
    $fileName = $args[1]
} else {
    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($filePath)
}
$fileExtension = [System.IO.Path]::GetExtension($filePath)

if (-Not ($fileExtension -eq ".py")) {
    Write-Host "The file extension must be .py" -ForegroundColor Red
    exit 1
}

$fileDirectory = [System.IO.Path]::GetDirectoryName($filePath)
$tempFolder = New-Item -ItemType Directory -Path "$env:TEMP\temp_zip_folder"

$renamedFilePath = "$tempFolder\my_player$fileExtension"
Copy-Item -Path $filePath -Destination $renamedFilePath

$zipPath = "$fileDirectory\$fileName.zip"
Compress-Archive -Path $renamedFilePath -DestinationPath $zipPath -Force

Remove-Item -Recurse -Force $tempFolder

Write-Host "File zipped successfully: $zipPath" -ForegroundColor Green
