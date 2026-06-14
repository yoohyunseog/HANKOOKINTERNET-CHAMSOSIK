$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$postsDir = Join-Path $scriptDir "posts"
$indexPath = Join-Path $postsDir "index.json"
$sampleBytes = 262144
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

Add-Type -AssemblyName System.Web

function Read-HtmlSample {
  param([string]$Path)

  $bytesToRead = [Math]::Min($sampleBytes, (Get-Item -LiteralPath $Path).Length)
  $buffer = New-Object byte[] $bytesToRead
  $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
  try {
    [void]$stream.Read($buffer, 0, $bytesToRead)
  } finally {
    $stream.Dispose()
  }

  return [System.Text.Encoding]::UTF8.GetString($buffer)
}

function Decode-Html {
  param([AllowNull()][string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
  return [System.Web.HttpUtility]::HtmlDecode($Value).Trim()
}

function Strip-Html {
  param([AllowNull()][string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
  $text = [regex]::Replace($Value, "<script[\s\S]*?</script>", " ", "IgnoreCase")
  $text = [regex]::Replace($text, "<style[\s\S]*?</style>", " ", "IgnoreCase")
  $text = [regex]::Replace($text, "<[^>]+>", " ")
  $text = [regex]::Replace($text, "\s+", " ")
  return Decode-Html $text
}

function Get-MetaContent {
  param(
    [string]$Html,
    [string]$Key
  )

  $escaped = [regex]::Escape($Key)
  $patterns = @(
    "<meta\b(?=[^>]*(?:name|property)=['""]$escaped['""])[^>]*content=['""]([^'""]*)['""][^>]*>",
    "<meta\b(?=[^>]*content=['""]([^'""]*)['""])[^>]*(?:name|property)=['""]$escaped['""][^>]*>"
  )

  foreach ($pattern in $patterns) {
    $match = [regex]::Match($Html, $pattern, "IgnoreCase")
    if ($match.Success) {
      return Decode-Html $match.Groups[1].Value
    }
  }

  return ""
}

function Get-TagText {
  param(
    [string]$Html,
    [string]$TagName
  )

  $match = [regex]::Match($Html, "<$TagName\b[^>]*>([\s\S]*?)</$TagName>", "IgnoreCase")
  if ($match.Success) {
    return Strip-Html $match.Groups[1].Value
  }
  return ""
}

function Get-FirstParagraph {
  param([string]$Html)
  $match = [regex]::Match($Html, "<p\b[^>]*>([\s\S]*?)</p>", "IgnoreCase")
  if ($match.Success) {
    return Strip-Html $match.Groups[1].Value
  }
  return ""
}

function Limit-Text {
  param(
    [AllowNull()][string]$Value,
    [int]$MaxLength
  )

  if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
  $text = [regex]::Replace($Value.Trim(), "\s+", " ")
  if ($text.Length -le $MaxLength) { return $text }
  return $text.Substring(0, $MaxLength).TrimEnd() + "..."
}

function Convert-ToBlogRelativePath {
  param(
    [string]$HtmlPath,
    [string]$Ref
  )

  if ([string]::IsNullOrWhiteSpace($Ref)) { return "" }

  $clean = Decode-Html $Ref
  try { $clean = [System.Uri]::UnescapeDataString($clean) } catch { }
  $clean = $clean -replace "\\", "/"

  if ($clean -match "^https?://[^/]+/blog/(.+)$") {
    return $Matches[1]
  }

  if ($clean -match "^https?://") {
    return $clean
  }

  $htmlDir = Split-Path -Parent $HtmlPath
  $candidate = if ([System.IO.Path]::IsPathRooted($clean)) {
    Join-Path $scriptDir $clean.TrimStart("/", "\")
  } else {
    Join-Path $htmlDir ($clean -replace "/", [System.IO.Path]::DirectorySeparatorChar)
  }

  try {
    $full = [System.IO.Path]::GetFullPath($candidate)
    $blogRoot = [System.IO.Path]::GetFullPath($scriptDir)
    if ($full.StartsWith($blogRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
      return $full.Substring($blogRoot.Length).TrimStart("\", "/") -replace "\\", "/"
    }
  } catch {
    return $clean.TrimStart("/")
  }

  return $clean.TrimStart("/")
}

function Get-PostDate {
  param(
    [string]$Html,
    [System.IO.FileInfo]$File
  )

  $date = Get-MetaContent $Html "article:published_time"
  if ([string]::IsNullOrWhiteSpace($date)) {
    $timeMatch = [regex]::Match($Html, "<time\b[^>]*datetime=['""]([^'""]+)['""]", "IgnoreCase")
    if ($timeMatch.Success) { $date = $timeMatch.Groups[1].Value }
  }
  if ([string]::IsNullOrWhiteSpace($date)) {
    $nameMatch = [regex]::Match($File.Name, "^(\d{4})-(\d{2})-(\d{2})")
    if ($nameMatch.Success) { $date = $nameMatch.Groups[0].Value }
  }

  if (-not [string]::IsNullOrWhiteSpace($date)) {
    $clean = $date.Trim()
    if ($clean -match "^(\d{4}-\d{2}-\d{2})$") {
      return "$clean $($File.LastWriteTime.ToString("HH:mm:ss"))"
    }
    if ($clean -match "^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::(\d{2}))?") {
      $seconds = if ($Matches[3]) { $Matches[3] } else { "00" }
      return "$($Matches[1]) $($Matches[2]):$seconds"
    }
  }

  return $File.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
}

function Guess-Category {
  param(
    [string]$Html,
    [string]$Title,
    [string]$Href
  )

  $category = Get-MetaContent $Html "article:section"
  if (-not [string]::IsNullOrWhiteSpace($category)) { return $category }

  $categoryMatch = [regex]::Match($Html, "<span[^>]*class=['""][^'""]*(?:post-category|category)[^'""]*['""][^>]*>([\s\S]*?)</span>", "IgnoreCase")
  if ($categoryMatch.Success) {
    $category = Strip-Html $categoryMatch.Groups[1].Value
    if (-not [string]::IsNullOrWhiteSpace($category)) { return $category }
  }

  $combined = "$Title $Href"
  if ($combined -match "maplestory|메이플") { return "게임 업데이트" }
  if ($combined -match "adsense|애드센스|revenue") { return "수익형 콘텐츠 분석" }
  if ($combined -match "ufo|jesus|예수|신앙") { return "신앙 기록" }
  if ($combined -match "coupang|쿠팡|backdoor|security|보안") { return "보안 분석" }
  if ($combined -match "market|bitcoin|gold|dollar|시장|증시") { return "시장 분석" }
  if ($combined -match "robot|humanoid|로봇|휴머노이드") { return "기술 전환" }

  return "블로그"
}

function Get-Image {
  param(
    [string]$Html,
    [string]$HtmlPath,
    [string]$Title,
    [string]$Href
  )

  $image = Get-MetaContent $Html "og:image"
  if ([string]::IsNullOrWhiteSpace($image)) {
    $match = [regex]::Match($Html, "<img\b[^>]*src=['""]([^'""]+)['""]", "IgnoreCase")
    if ($match.Success) { $image = $match.Groups[1].Value }
  }

  $relative = Convert-ToBlogRelativePath $HtmlPath $image
  if (-not [string]::IsNullOrWhiteSpace($relative) -and $relative -notmatch "^https?://") {
    $imagePath = Join-Path $scriptDir ($relative -replace "/", [System.IO.Path]::DirectorySeparatorChar)
    if (Test-Path -LiteralPath $imagePath) {
      return $relative
    }
  }

  $combined = "$Title $Href"
  if ($combined -match "maplestory|메이플") { return "assets/2026-06-13-maplestory-summer-showcase-overdrive.png" }
  if ($combined -match "ufo|jesus|예수|신앙") { return "assets/2026-06-13-ufo-jesus-peace-poster.svg" }
  if ($combined -match "backdoor|백도어") { return "assets/backdoor-state-level.png" }
  if ($combined -match "coupang|쿠팡") { return "assets/coupang-privilege-backdoor-analysis.png" }
  if ($combined -match "robot|humanoid|로봇|휴머노이드") { return "assets/latest-humanoid-robots-2026-cover.png" }

  return $relative
}

if (-not (Test-Path -LiteralPath $postsDir)) {
  throw "posts folder not found: $postsDir"
}

$htmlFiles = Get-ChildItem -LiteralPath $postsDir -Recurse -Filter "*.html" -File |
  Where-Object { $_.FullName -notmatch "\\masonry-bit\\" }

$posts = foreach ($file in $htmlFiles) {
  $html = Read-HtmlSample $file.FullName
  $href = $file.FullName.Substring($scriptDir.Length).TrimStart("\", "/") -replace "\\", "/"

  $title = Get-MetaContent $html "og:title"
  if ([string]::IsNullOrWhiteSpace($title)) { $title = Get-TagText $html "title" }
  if ($title -match "\s+\|\s+") { $title = ($title -split "\s+\|\s+")[0] }
  if ([string]::IsNullOrWhiteSpace($title)) { $title = [System.IO.Path]::GetFileNameWithoutExtension($file.Name) }

  $excerpt = Get-MetaContent $html "description"
  if ([string]::IsNullOrWhiteSpace($excerpt)) { $excerpt = Get-MetaContent $html "og:description" }
  if ([string]::IsNullOrWhiteSpace($excerpt)) { $excerpt = Get-FirstParagraph $html }

  $date = Get-PostDate $html $file
  $category = Guess-Category $html $title $href
  $image = Get-Image $html $file.FullName $title $href

  [pscustomobject]@{
    title = Limit-Text $title 120
    excerpt = Limit-Text $excerpt 220
    date = $date
    category = $category
    href = $href
    image = $image
    views = 0
  }
}

$sorted = @($posts) | Sort-Object @{ Expression = { [datetime]::ParseExact($_.date, "yyyy-MM-dd HH:mm:ss", $null) }; Descending = $true }, title
$json = $sorted | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($indexPath, $json + [Environment]::NewLine, $utf8NoBom)

Write-Host "Generated index.json:" $indexPath
Write-Host "Post count:" $sorted.Count
