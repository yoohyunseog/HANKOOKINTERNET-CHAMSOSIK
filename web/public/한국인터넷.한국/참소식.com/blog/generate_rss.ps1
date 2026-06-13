$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$postsDir = Join-Path $scriptDir "posts"
$indexPath = Join-Path $postsDir "index.json"
$rssPath = Join-Path $postsDir "rss.xml"

$siteTitle = "Chamsosik.com Blog"
$siteUrl = "https://xn--9l4b4xi9r.com/blog/"
$rssUrl = "https://xn--9l4b4xi9r.com/blog/posts/rss.xml"
$siteDescription = "Latest posts from Chamsosik.com."
$author = "Chamsosik.com"
$timezone = [TimeSpan]::FromHours(9)
$culture = [System.Globalization.CultureInfo]::InvariantCulture

function Escape-Xml {
  param([AllowNull()][string]$Value)
  if ($null -eq $Value) { return "" }
  return [System.Security.SecurityElement]::Escape($Value)
}

function Escape-CData {
  param([AllowNull()][string]$Value)
  if ($null -eq $Value) { return "" }
  return $Value.Replace("]]>", "]]]]><![CDATA[>")
}

function Convert-ToAbsoluteUrl {
  param([string]$Href)

  if ($Href -match "^https?://") {
    return $Href
  }

  return $siteUrl + $Href.TrimStart("/")
}

function Convert-ToRssDate {
  param([string]$DateText)

  if ([string]::IsNullOrWhiteSpace($DateText)) {
    return [DateTimeOffset]::Now.ToOffset($timezone)
  }

  $match = [regex]::Match($DateText.Trim(), "^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2}):(\d{2})$")
  if ($match.Success) {
    $year = [int]$match.Groups[1].Value
    $month = [int]$match.Groups[2].Value
    $day = [int]$match.Groups[3].Value
    $hour = [int]$match.Groups[4].Value
    $minute = [int]$match.Groups[5].Value
    $second = [int]$match.Groups[6].Value

    $baseDate = [DateTime]::new($year, $month, $day, 0, 0, 0, [DateTimeKind]::Unspecified)
    if ($hour -ge 24) {
      $baseDate = $baseDate.AddDays([math]::Floor($hour / 24))
      $hour = $hour % 24
    }

    return [DateTimeOffset]::new($baseDate.AddHours($hour).AddMinutes($minute).AddSeconds($second), $timezone)
  }

  return [DateTimeOffset]::Parse($DateText, $culture).ToOffset($timezone)
}

if (-not (Test-Path -LiteralPath $indexPath)) {
  throw "index.json not found: $indexPath"
}

$posts = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($null -eq $posts) {
  throw "No posts found in index.json"
}

$sortedPosts = @($posts) | Sort-Object @{ Expression = { Convert-ToRssDate $_.date }; Descending = $true }
$lastBuildDate = Convert-ToRssDate $sortedPosts[0].date

$builder = [System.Text.StringBuilder]::new()
[void]$builder.AppendLine('<?xml version="1.0" encoding="UTF-8"?>')
[void]$builder.AppendLine('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">')
[void]$builder.AppendLine('  <channel>')
[void]$builder.AppendLine("    <title>$(Escape-Xml $siteTitle)</title>")
[void]$builder.AppendLine("    <link>$(Escape-Xml $siteUrl)</link>")
[void]$builder.AppendLine("    <atom:link href=""$(Escape-Xml $rssUrl)"" rel=""self"" type=""application/rss+xml""/>")
[void]$builder.AppendLine("    <description>$(Escape-Xml $siteDescription)</description>")
[void]$builder.AppendLine('    <language>ko</language>')
[void]$builder.AppendLine('    <copyright>(c) 2026 Chamsosik.com</copyright>')
[void]$builder.AppendLine("    <lastBuildDate>$($lastBuildDate.ToString('ddd, dd MMM yyyy HH:mm:ss', $culture)) +0900</lastBuildDate>")
[void]$builder.AppendLine('    <generator>Chamsosik.com RSS Generator</generator>')
[void]$builder.AppendLine('    <webMaster>admin@chamsosik.com</webMaster>')
[void]$builder.AppendLine('    <ttl>60</ttl>')
[void]$builder.AppendLine('    <image>')
[void]$builder.AppendLine('      <url>https://xn--9l4b4xi9r.com/favicon.svg</url>')
[void]$builder.AppendLine('      <title>Chamsosik.com</title>')
[void]$builder.AppendLine('      <link>https://xn--9l4b4xi9r.com/</link>')
[void]$builder.AppendLine('    </image>')
[void]$builder.AppendLine('')

foreach ($post in $sortedPosts) {
  $title = [string]$post.title
  $excerpt = [string]$post.excerpt
  $category = [string]$post.category
  $link = Convert-ToAbsoluteUrl ([string]$post.href)
  $pubDate = Convert-ToRssDate ([string]$post.date)
  $imageUrl = if ($post.image) { Convert-ToAbsoluteUrl ([string]$post.image) } else { "" }

  $content = "<p>$(Escape-Xml $excerpt)</p>"
  if (-not [string]::IsNullOrWhiteSpace($imageUrl)) {
    $content = "<p><img src=""$(Escape-Xml $imageUrl)"" alt=""$(Escape-Xml $title)"" /></p>$content"
  }

  [void]$builder.AppendLine('    <item>')
  [void]$builder.AppendLine("      <title>$(Escape-Xml $title)</title>")
  [void]$builder.AppendLine("      <link>$(Escape-Xml $link)</link>")
  [void]$builder.AppendLine("      <guid isPermaLink=""true"">$(Escape-Xml $link)</guid>")
  [void]$builder.AppendLine("      <description>$(Escape-Xml $excerpt)</description>")
  [void]$builder.AppendLine("      <content:encoded><![CDATA[$(Escape-CData $content)]]></content:encoded>")
  [void]$builder.AppendLine("      <pubDate>$($pubDate.ToString('ddd, dd MMM yyyy HH:mm:ss', $culture)) +0900</pubDate>")
  [void]$builder.AppendLine("      <category>$(Escape-Xml $category)</category>")
  [void]$builder.AppendLine("      <author>$(Escape-Xml $author)</author>")
  [void]$builder.AppendLine('    </item>')
  [void]$builder.AppendLine('')
}

[void]$builder.AppendLine('  </channel>')
[void]$builder.AppendLine('</rss>')

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($rssPath, $builder.ToString(), $utf8NoBom)

Write-Host "Generated RSS:" $rssPath
Write-Host "Post count:" $sortedPosts.Count
