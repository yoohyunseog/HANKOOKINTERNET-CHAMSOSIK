$ErrorActionPreference = 'Stop'

$baseUrl = 'http://localhost:3000'
$endpoint = "$baseUrl/api/trend-ai"

$payload = @{
    limit = 3
    model = 'llama3'
} | ConvertTo-Json

Write-Host "POST $endpoint" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType 'application/json' -Body $payload
    Write-Host "✅ Success: $($response.count) items" -ForegroundColor Green
    $response.results | Select-Object -First 1 | ForEach-Object {
        Write-Host "- Keyword: $($_.keyword)"
        Write-Host "- Question: $($_.question)"
        Write-Host "- Title: $($_.generated.title)"
        Write-Host "- Summary: $($_.generated.summary)"
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message
    }
}
