param(
    [string]$Folder = ".\\test_images3",
    [string]$ApiBaseUrl = "http://localhost:8000",
    [string]$DeviceCode = "CAM-01",
    [string]$DeviceToken = "stvis-device-demo-token",
    [int]$Limit = 13,
    [switch]$Recurse,
    [int]$DelayMs = 0,
    [string]$ExternalRefPrefix = "bulk-test"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Net.Http

function Get-MimeType {
    param([string]$Path)

    switch ([System.IO.Path]::GetExtension($Path).ToLowerInvariant()) {
        ".jpg" { return "image/jpeg" }
        ".jpeg" { return "image/jpeg" }
        ".png" { return "image/png" }
        ".bmp" { return "image/bmp" }
        ".webp" { return "image/webp" }
        default { return "application/octet-stream" }
    }
}

function New-HttpClient {
    $handler = [System.Net.Http.HttpClientHandler]::new()
    $client = [System.Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(60)
    $client.DefaultRequestHeaders.Add("X-Device-Code", $DeviceCode)
    $client.DefaultRequestHeaders.Add("X-Device-Token", $DeviceToken)
    return $client
}

$resolvedFolder = Resolve-Path -LiteralPath $Folder -ErrorAction Stop
$searchOption = if ($Recurse.IsPresent) { [System.IO.SearchOption]::AllDirectories } else { [System.IO.SearchOption]::TopDirectoryOnly }
$allowedExtensions = @(".jpg", ".jpeg", ".png", ".bmp", ".webp")

$files = [System.IO.Directory]::EnumerateFiles($resolvedFolder.Path, "*.*", $searchOption) |
    Where-Object { $allowedExtensions -contains [System.IO.Path]::GetExtension($_).ToLowerInvariant() } |
    Select-Object -First $Limit

if (-not $files) {
    Write-Error "No image files found in '$($resolvedFolder.Path)'."
}

$endpoint = "$($ApiBaseUrl.TrimEnd('/'))/api/v1/ingest/events"
$client = New-HttpClient

$successCount = 0
$failureCount = 0

Write-Host "Uploading $(@($files).Count) image(s) to $endpoint" -ForegroundColor Cyan

foreach ($file in $files) {
    $content = $null
    $fileStream = $null

    try {
        $fileInfo = Get-Item -LiteralPath $file
        $mimeType = Get-MimeType -Path $fileInfo.FullName
        $fileStream = [System.IO.File]::OpenRead($fileInfo.FullName)
        $streamContent = [System.Net.Http.StreamContent]::new($fileStream)
        $streamContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse($mimeType)

        $content = [System.Net.Http.MultipartFormDataContent]::new()
        $content.Add($streamContent, "evidence", $fileInfo.Name)
        $content.Add([System.Net.Http.StringContent]::new((Get-Date).ToUniversalTime().ToString("o")), "captured_at")
        $content.Add([System.Net.Http.StringContent]::new("$ExternalRefPrefix-$($fileInfo.BaseName)"), "external_ref")

        $response = $client.PostAsync($endpoint, $content).GetAwaiter().GetResult()
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()

        if ($response.IsSuccessStatusCode) {
            $parsed = $body | ConvertFrom-Json
            $successCount++
            Write-Host ("[OK] {0} -> event_id={1} status={2}" -f $fileInfo.Name, $parsed.event_id, $parsed.status) -ForegroundColor Green
        } else {
            $failureCount++
            Write-Host ("[FAIL] {0} -> HTTP {1} {2}" -f $fileInfo.Name, [int]$response.StatusCode, $body) -ForegroundColor Red
        }
    }
    catch {
        $failureCount++
        Write-Host ("[FAIL] {0} -> {1}" -f $file, $_.Exception.Message) -ForegroundColor Red
    }
    finally {
        if ($fileStream) {
            $fileStream.Dispose()
        }
        if ($content) {
            $content.Dispose()
        }
    }

    if ($DelayMs -gt 0) {
        Start-Sleep -Milliseconds $DelayMs
    }
}

$client.Dispose()

Write-Host ""
Write-Host ("Done. Success={0}, Failed={1}" -f $successCount, $failureCount) -ForegroundColor Yellow
