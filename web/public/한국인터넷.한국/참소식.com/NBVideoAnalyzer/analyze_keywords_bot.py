from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


BASE_DIR = Path(__file__).resolve().parent
KEYWORD_DIR = BASE_DIR / "keywords"
RESULT_DIR = BASE_DIR / "analysis_results"
KEYWORD_FILE_SUFFIX = "_keywords.json"
MAX_CATEGORY_FILES = 10
SETTINGS_PATH = BASE_DIR / "settings.json"

# Current year for date analysis
CURRENT_YEAR = datetime.now().year
# Reference years for N/B analysis (older content gets lower values)
MIN_REFERENCE_YEAR = 1990
MIN_REFERENCE_DATETIME = datetime(MIN_REFERENCE_YEAR, 1, 1, tzinfo=timezone.utc)
UPLOAD_DATE_KEYS = (
    "publishedAt",
    "uploadDate",
    "uploadedAt",
    "published_at",
    "upload_date",
    "uploaded_at",
)


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        settings = {}
    else:
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            settings = {}

    env_map = {
        "YOUTUBE_SEARCH_ENABLED": "youtubeSearchEnabled",
        "YOUTUBE_SEARCH_RESULTS": "youtubeSearchResults",
        "YOUTUBE_MAX_KEYWORDS": "youtubeMaxKeywords",
        "YOUTUBE_SEARCH_TIMEOUT_SECONDS": "youtubeSearchTimeoutSeconds",
    }
    for env_name, setting_name in env_map.items():
        value = os.environ.get(env_name)
        if value is None:
            continue
        if setting_name == "youtubeSearchEnabled":
            settings[setting_name] = value.strip().lower() in {"1", "true", "yes", "on"}
        else:
            try:
                settings[setting_name] = int(value)
            except ValueError:
                settings[setting_name] = value

    return settings


def search_youtube_videos(query: str, max_results: int = 5, timeout: int = 60) -> list[dict]:
    max_results = max(1, min(int(max_results or 5), 50))
    print(f"[YOUTUBE] Start search: query=\"{query}\" limit={max_results}", flush=True)
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        f"ytsearch{max_results}:{query}",
        "--dump-single-json",
        "--skip-download",
        "--no-warnings",
        "--ignore-errors",
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        print(f"[YOUTUBE] Search failed or empty: query=\"{query}\" returnCode={completed.returncode}", flush=True)
        if completed.stderr.strip():
            print(f"[YOUTUBE] stderr: {completed.stderr.strip()[:500]}", flush=True)
        return []

    data = json.loads(completed.stdout)
    videos = []
    for item in data.get("entries", []) or []:
        if not item:
            continue

        view_count = item.get("view_count")
        timestamp = item.get("timestamp")
        upload_date = item.get("upload_date")
        published_at = (
            datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
            if isinstance(timestamp, (int, float))
            else upload_date
        )
        videos.append(
            {
                "videoId": item.get("id"),
                "title": item.get("title", ""),
                "channelTitle": item.get("channel") or item.get("uploader") or "",
                "publishedAt": published_at,
                "uploadDate": upload_date,
                "timestamp": timestamp,
                "viewCount": int(view_count) if isinstance(view_count, int) else 0,
                "url": item.get("webpage_url") or item.get("url") or "",
            }
        )

    print(f"[YOUTUBE] Finished search: query=\"{query}\" videos={len(videos)}", flush=True)
    for index, video in enumerate(videos, start=1):
        print(
            "[VIDEO] "
            f"{index}/{len(videos)} "
            f"id={video.get('videoId')} "
            f"views={video.get('viewCount')} "
            f"uploaded={video.get('uploadDate') or video.get('publishedAt')} "
            f"title=\"{video.get('title')}\"",
            flush=True,
        )
    return videos


def extract_years_from_keyword(keyword: str) -> list[int]:
    """Extract years from keyword (e.g., '2024 드라마', '아바타3', '듄2', '1987')."""
    years = []
    
    # Direct year patterns: 2024, 2025, 1990, 1987, etc.
    year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', keyword)
    years.extend([int(y) for y in year_matches])
    
    # Special date patterns: 12.12, 5.18, 4.19, etc. (historical events)
    special_dates = {
        '12.12': 1979,  # 12.12 군사반란
        '5.18': 1980,   # 광주민주화운동
        '4.19': 1960,   # 4.19 혁명
        '6.25': 1950,   # 한국전쟁
        '3.1': 1919,    # 3.1 운동
        '8.15': 1945,   # 광복절
    }
    for date_str, year in special_dates.items():
        if date_str in keyword:
            years.append(year)
    
    # Sequel numbers: 아바타3, 듄2, 존윅4, etc. -> convert to years
    sequel_pattern = r'([가-힣A-Za-z]+)([2-9])$'
    sequel_matches = re.findall(sequel_pattern, keyword)
    for name, num in sequel_matches:
        # Sequel number roughly corresponds to year progression
        # e.g., 아바타2 (2022), 아바타3 (2024+) -> estimate year
        estimated_year = CURRENT_YEAR - (5 - int(num))  # Rough estimate
        years.append(max(estimated_year, MIN_REFERENCE_YEAR))
    
    # Version numbers: 시즌2, 2기, 3화, Part 2, etc.
    version_patterns = [
        (r'시즌(\d+)', 2020),      # 시즌2 -> ~2022
        (r'(\d+)기', 2015),        # 2기 -> ~2017
        (r'(\d+)화', 2010),        # 3화 -> ~2013
        (r'Part\s*(\d+)', 2018),   # Part 2 -> ~2020
        (r'파트(\d+)', 2018),       # 파트2 -> ~2020
        (r'(\d+)부', 2015),         # 2부 -> ~2017
        (r'(\d+)편', 2015),         # 2편 -> ~2017
    ]
    for pattern, base_year in version_patterns:
        matches = re.findall(pattern, keyword)
        for num in matches:
            estimated_year = base_year + (int(num) - 1) * 2
            years.append(min(estimated_year, CURRENT_YEAR + 5))
    
    # DDR4, DDR5, RTX4090, RTX4080, etc. - tech versions
    tech_patterns = [
        (r'DDR(\d+)', 2000),       # DDR4 -> ~2014
        (r'RTX\s*(\d+)', 2018),     # RTX4090 -> ~2022
        (r'GTX\s*(\d+)', 2010),     # GTX1080 -> ~2016
    ]
    for pattern, base_year in tech_patterns:
        matches = re.findall(pattern, keyword)
        for num_str in matches:
            num = int(num_str)
            if pattern.startswith('DDR'):
                estimated_year = base_year + (num - 1) * 5
            elif 'RTX' in pattern or 'GTX' in pattern:
                # RTX4090 -> 40 series = 2022, 30 series = 2020
                series = num // 100
                estimated_year = base_year + series * 2
            else:
                estimated_year = base_year + num
            years.append(min(estimated_year, CURRENT_YEAR + 2))
    
    return years


def year_to_nb_value(year: int) -> float:
    """Convert year to N/B analyzable value. Newer = higher value."""
    # Normalize year to positive value for N/B analysis
    # Years closer to current year get higher values
    year_diff = CURRENT_YEAR - year
    # Convert to positive scale: newer content = higher value
    # Base value of 1000 + (years from reference)
    normalized_value = 1000 + (year - MIN_REFERENCE_YEAR) * 10
    return float(normalized_value)


def analyze_date(keyword: str) -> dict:
    """Analyze date/year information in keyword."""
    years = extract_years_from_keyword(keyword)
    
    if not years:
        return {
            "hasDate": False,
            "years": [],
            "yearCount": 0,
            "newestYear": None,
            "dateScore": 0.0,
            "dateNbMax": 0.0,
            "dateNbMin": 0.0,
            "recencyScore": 0.0,
        }
    
    # Convert years to N/B values
    year_values = [year_to_nb_value(y) for y in years]
    
    # Calculate N/B for years
    nb_max = bit_max_nb(year_values) if year_values else 0.0
    nb_min = bit_min_nb(year_values) if year_values else 0.0
    
    newest_year = max(years)
    # Recency score: 0-100, where 100 = current year
    recency_score = max(0, 100 - (CURRENT_YEAR - newest_year) * 5)
    
    return {
        "hasDate": True,
        "years": years,
        "yearCount": len(years),
        "newestYear": newest_year,
        "dateScore": round(sum(year_values) / len(year_values), 2) if year_values else 0.0,
        "dateNbMax": round(nb_max, 6),
        "dateNbMin": round(nb_min, 6),
        "recencyScore": round(recency_score, 2),
    }


def initialize_arrays(length: int) -> dict[str, list[float]]:
    return {
        "BIT_START_A50": [0.0] * length,
        "BIT_START_A100": [0.0] * length,
        "BIT_START_B50": [0.0] * length,
        "BIT_START_B100": [0.0] * length,
        "BIT_START_NBA100": [0.0] * length,
    }


def calculate_bit(nb: list[float], bit: float = 5.5, reverse: bool = False) -> float:
    if len(nb) < 2:
        return bit / 100

    bit_nb = bit
    max_value = max(nb)
    min_value = min(nb)
    count_size = 50
    total_range_count = count_size * len(nb)

    negative_range = abs(min_value) if min_value < 0 else 0
    positive_range = max_value if max_value > 0 else 0

    negative_increment = negative_range / (total_range_count - 1)
    positive_increment = positive_range / (total_range_count - 1)
    arrays = initialize_arrays(total_range_count)

    count = 0
    total_sum = 0.0

    for value in nb:
        for _ in range(count_size):
            bit_end = 1
            if value < 0:
                a50 = min_value + negative_increment * (count + 1)
                b50 = a50 - negative_increment * 2
                b100 = a50 + negative_increment
            else:
                a50 = min_value + positive_increment * (count + 1)
                b50 = a50 - positive_increment * 2
                b100 = a50 + positive_increment

            a100 = (count + 1) * bit_nb / total_range_count
            nba100 = a100 / (len(nb) - bit_end)

            arrays["BIT_START_A50"][count] = a50
            arrays["BIT_START_A100"][count] = a100
            arrays["BIT_START_B50"][count] = b50
            arrays["BIT_START_B100"][count] = b100
            arrays["BIT_START_NBA100"][count] = nba100
            count += 1

        total_sum += value

    if reverse:
        arrays["BIT_START_NBA100"].reverse()

    nb50 = 0.0
    for value in nb:
        for index in range(len(arrays["BIT_START_NBA100"])):
            if arrays["BIT_START_B50"][index] <= value <= arrays["BIT_START_B100"][index]:
                nb50 += arrays["BIT_START_NBA100"][min(index, len(arrays["BIT_START_NBA100"]) - 1)]
                break

    average_ratio = (total_sum / (len(nb) * abs(max_value or 1))) * 100
    nb50 = min((nb50 / 100) * average_ratio, bit_nb)

    if len(nb) == 2:
        return bit - nb50

    return nb50


def bit_max_nb(nb: list[float], bit: float = 5.5) -> float:
    result = calculate_bit(nb, bit, False)
    return result if math.isfinite(result) and -100 <= result <= 100 else 0.0


def bit_min_nb(nb: list[float], bit: float = 5.5) -> float:
    result = calculate_bit(nb, bit, True)
    return result if math.isfinite(result) and -100 <= result <= 100 else 0.0


def parse_upload_datetime(value: object) -> datetime | None:
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass

    for pattern in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            sample = text[:8] if pattern == "%Y%m%d" else text[:10]
            return datetime.strptime(sample, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def upload_datetime_to_nb_value(uploaded_at: datetime) -> float:
    microseconds_since_reference = max(
        int((uploaded_at - MIN_REFERENCE_DATETIME).total_seconds() * 1_000_000),
        0,
    )
    return float(microseconds_since_reference)


def first_upload_date_value(entry: dict) -> object | None:
    for key in UPLOAD_DATE_KEYS:
        value = entry.get(key)
        if value:
            return value
    return None


def collect_upload_dates(entry: object) -> list[object]:
    if not isinstance(entry, dict):
        return []

    dates = [value for key in UPLOAD_DATE_KEYS if (value := entry.get(key))]
    videos = entry.get("videos")
    if isinstance(videos, list):
        for video in videos:
            if isinstance(video, dict):
                value = first_upload_date_value(video)
                if value:
                    dates.append(value)

    return dates


def collect_view_counts(videos: list[dict]) -> list[float]:
    values = []
    for video in videos:
        view_count = video.get("viewCount") if isinstance(video, dict) else None
        if isinstance(view_count, (int, float)) and view_count > 0:
            values.append(float(view_count))
    return values


def analyze_upload_dates(upload_dates: list[object]) -> dict:
    parsed_dates = [parsed for value in upload_dates if (parsed := parse_upload_datetime(value))]

    if not parsed_dates:
        return {
            "hasUploadDate": False,
            "uploadDates": [],
            "uploadDateMicroseconds": [],
            "uploadDateCount": 0,
            "newestUploadDate": None,
            "oldestUploadDate": None,
            "uploadDateScore": 0.0,
            "uploadDateNbMax": 0.0,
            "uploadDateNbMin": 0.0,
            "recencyScore": 0.0,
            "hasDate": False,
            "dateScore": 0.0,
            "dateNbMax": 0.0,
            "dateNbMin": 0.0,
        }

    upload_values = [upload_datetime_to_nb_value(uploaded_at) for uploaded_at in parsed_dates]
    nb_max = bit_max_nb(upload_values)
    nb_min = bit_min_nb(upload_values)
    newest_upload_date = max(parsed_dates)
    oldest_upload_date = min(parsed_dates)
    days_old = max((datetime.now(timezone.utc) - newest_upload_date).days, 0)
    recency_score = max(0, 100 - (days_old / 30) * 5)
    upload_date_score = round(sum(upload_values) / len(upload_values), 2)

    return {
        "hasUploadDate": True,
        "uploadDates": sorted({uploaded_at.isoformat() for uploaded_at in parsed_dates}),
        "uploadDateMicroseconds": [int(value) for value in upload_values],
        "uploadDateCount": len(parsed_dates),
        "newestUploadDate": newest_upload_date.isoformat(),
        "oldestUploadDate": oldest_upload_date.isoformat(),
        "uploadDateScore": upload_date_score,
        "uploadDateNbMax": round(nb_max, 6),
        "uploadDateNbMin": round(nb_min, 6),
        "recencyScore": round(recency_score, 2),
        "hasDate": True,
        "dateScore": upload_date_score,
        "dateNbMax": round(nb_max, 6),
        "dateNbMin": round(nb_min, 6),
    }


def word_nb_unicode_format(text: str) -> list[int]:
    ranges = [
        ((0xAC00, 0xD7AF), 1000000),
        ((0x3040, 0x309F), 2000000),
        ((0x30A0, 0x30FF), 3000000),
        ((0x4E00, 0x9FFF), 4000000),
        ((0x0410, 0x044F), 5000000),
        ((0x0041, 0x007A), 6000000),
        ((0x0590, 0x05FF), 7000000),
        ((0x00C0, 0x00FD), 8000000),
        ((0x0E00, 0x0E7F), 9000000),
    ]

    values = []
    for char in text:
        code = ord(char)
        prefix = 0
        for (start, end), candidate_prefix in ranges:
            if start <= code <= end:
                prefix = candidate_prefix
                break
        values.append(prefix + code)
    return values


def identify_language(text: str) -> str:
    counts = Counter()
    for char in text:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7AF:
            counts["Korean"] += 100
        elif 0x3040 <= code <= 0x309F or 0x30A0 <= code <= 0x30FF:
            counts["Japanese"] += 10
        elif 0x4E00 <= code <= 0x9FFF:
            counts["Chinese"] += 10
        elif 0x0041 <= code <= 0x005A or 0x0061 <= code <= 0x007A:
            counts["English"] += 1
        elif char.strip():
            counts["Others"] += 1

    if not counts:
        return "None"
    return counts.most_common(1)[0][0]


def normalize_keyword(keyword: str) -> str:
    lowered = keyword.lower().strip()
    return re.sub(r"\s+", " ", lowered)


def keyword_tokens(keyword: str) -> set[str]:
    return set(re.findall(r"[0-9A-Za-z가-힣ぁ-んァ-ン一-龥]+", keyword.lower()))


def jaccard_similarity(left: str, right: str) -> float:
    left_tokens = keyword_tokens(left)
    right_tokens = keyword_tokens(right)
    if not left_tokens and not right_tokens:
        return 100.0
    union = left_tokens | right_tokens
    if not union:
        return 0.0
    return round((len(left_tokens & right_tokens) / len(union)) * 100, 2)


def make_analysis_keyword(category: str, keyword: str) -> str:
    return f"{category} {keyword}".strip()


def make_query_variants(category: str, keyword: str) -> list[str]:
    if category == "괴물딴지":
        suffixes = ["미스터리", "실화", "사건", "괴담", "분석"]
    elif category == "애니메이션":
        suffixes = ["리뷰", "분석", "결말", "해석", "명장면"]
    else:
        suffixes = ["분석", "리뷰", "이슈"]

    analysis_keyword = make_analysis_keyword(category, keyword)
    return [analysis_keyword] + [f"{analysis_keyword} {suffix}" for suffix in suffixes]


def analyze_keyword(
    category: str,
    keyword: str,
    upload_dates: list[object] | None = None,
    videos: list[dict] | None = None,
) -> dict:
    analysis_keyword = make_analysis_keyword(category, keyword)
    unicode_values = word_nb_unicode_format(analysis_keyword)
    videos = videos or []
    
    view_values = collect_view_counts(videos)
    if view_values:
        view_nb_max = bit_max_nb(view_values)
        view_nb_min = bit_min_nb(view_values)
        view_source = "youtubeViewCount"
    else:
        view_nb_max = bit_max_nb([float(value) for value in unicode_values])
        view_nb_min = bit_min_nb([float(value) for value in unicode_values])
        view_source = "keywordUnicodeFallback"
    view_nb_gap = view_nb_max - view_nb_min
    
    video_upload_dates = collect_upload_dates({"videos": videos}) if videos else []
    date_analysis = analyze_upload_dates((upload_dates or []) + video_upload_dates)
    date_nb_max = float(date_analysis.get("dateNbMax", 0.0) or 0.0)
    date_nb_min = float(date_analysis.get("dateNbMin", 0.0) or 0.0)

    # Final N/B used by the dashboard: view N/B + upload/date N/B.
    combined_nb_max = view_nb_max + date_nb_max
    combined_nb_min = view_nb_min + date_nb_min
    combined_nb_gap = combined_nb_max - combined_nb_min
    
    no_space = analysis_keyword.replace(" ", "")

    return {
        "keyword": keyword,
        "analysisKeyword": analysis_keyword,
        "normalizedKeyword": normalize_keyword(analysis_keyword),
        "language": identify_language(analysis_keyword),
        "characterCount": len(analysis_keyword),
        "characterCountNoSpace": len(no_space),
        "wordCount": len(analysis_keyword.split()),
        "unicodeValues": unicode_values,
        "viewAnalysis": {
            "nbMax": round(view_nb_max, 6),
            "nbMin": round(view_nb_min, 6),
            "nbGap": round(view_nb_gap, 6),
            "source": view_source,
            "viewCounts": [int(value) for value in view_values],
        },
        "dateAnalysis": date_analysis,
        "videos": videos,
        "combinedAnalysis": {
            "nbMax": round(combined_nb_max, 6),
            "nbMin": round(combined_nb_min, 6),
            "nbGap": round(combined_nb_gap, 6),
        },
        "nbMax": round(combined_nb_max, 6),
        "nbMin": round(combined_nb_min, 6),
        "nbGap": round(combined_nb_gap, 6),
        "combinedScore": round(combined_nb_gap, 6),
        "queryVariants": make_query_variants(category, keyword),
    }


def print_keyword_analysis_log(result: dict) -> None:
    videos = result.get("videos") or []
    view_analysis = result.get("viewAnalysis") or {}
    date_analysis = result.get("dateAnalysis") or {}
    print(
        "[NB] "
        f"keyword=\"{result.get('analysisKeyword')}\" "
        f"videos={len(videos)} "
        f"viewSource={view_analysis.get('source')} "
        f"dateMicroseconds={len(date_analysis.get('uploadDateMicroseconds') or [])} "
        f"viewNbMax={view_analysis.get('nbMax')} "
        f"viewNbMin={view_analysis.get('nbMin')} "
        f"dateNbMax={date_analysis.get('dateNbMax')} "
        f"dateNbMin={date_analysis.get('dateNbMin')} "
        f"finalNbMax={result.get('nbMax')} "
        f"finalNbMin={result.get('nbMin')} "
        f"gap={result.get('nbGap')}",
        flush=True,
    )


def normalize_keyword_entry(entry: object) -> dict | None:
    if isinstance(entry, dict):
        keyword = str(
            entry.get("keyword")
            or entry.get("query")
            or entry.get("title")
            or entry.get("analysisKeyword")
            or ""
        ).strip()
        if not keyword:
            return None
        return {
            "keyword": keyword,
            "uploadDates": collect_upload_dates(entry),
        }

    keyword = str(entry).strip()
    if not keyword:
        return None
    return {
        "keyword": keyword,
        "uploadDates": [],
    }


def should_fetch_youtube(index: int, settings: dict) -> bool:
    if not settings.get("youtubeSearchEnabled", True):
        return False

    max_keywords = settings.get("youtubeMaxKeywords")
    if max_keywords in (None, "", 0):
        return True

    try:
        return index < int(max_keywords)
    except (TypeError, ValueError):
        return True


def analyze_file(path: Path, settings: dict) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    category = data.get("category", path.stem)
    keywords = data.get("keywords", [])

    if not isinstance(keywords, list):
        raise ValueError(f"{path.name}: keywords must be a list")

    keyword_entries = [
        normalized
        for keyword in keywords
        if (normalized := normalize_keyword_entry(keyword))
    ]
    clean_keywords = [entry["keyword"] for entry in keyword_entries]
    normalized_counts = Counter(normalize_keyword(keyword) for keyword in clean_keywords)
    duplicate_keywords = [
        keyword for keyword, count in normalized_counts.items() if count > 1
    ]

    keyword_results = []
    youtube_errors = []
    youtube_result_count = int(settings.get("youtubeSearchResults", 5) or 5)
    youtube_timeout = int(settings.get("youtubeSearchTimeoutSeconds", 60) or 60)
    search_target_count = sum(
        1 for index, _ in enumerate(keyword_entries) if should_fetch_youtube(index, settings)
    )
    print(
        "[FILE] "
        f"source={path.name} "
        f"category=\"{category}\" "
        f"keywords={len(keyword_entries)} "
        f"youtubeSearch={bool(settings.get('youtubeSearchEnabled', True))} "
        f"searchTargets={search_target_count} "
        f"resultsPerKeyword={youtube_result_count}",
        flush=True,
    )
    for index, entry in enumerate(keyword_entries):
        videos = []
        should_search = should_fetch_youtube(index, settings)
        if should_search:
            query = make_analysis_keyword(category, entry["keyword"])
            try:
                print(
                    "[KEYWORD] "
                    f"{index + 1}/{len(keyword_entries)} "
                    f"category=\"{category}\" "
                    f"keyword=\"{entry['keyword']}\" "
                    f"query=\"{query}\"",
                    flush=True,
                )
                videos = search_youtube_videos(query, youtube_result_count, youtube_timeout)
                fallback_query = str(entry["keyword"]).strip()
                if not videos and fallback_query and fallback_query != query:
                    print(
                        "[YOUTUBE] "
                        f"No videos for query=\"{query}\"; retry query=\"{fallback_query}\"",
                        flush=True,
                    )
                    videos = search_youtube_videos(
                        fallback_query, youtube_result_count, youtube_timeout
                    )
            except Exception as error:
                youtube_errors.append({"keyword": entry["keyword"], "error": str(error)})
                print(
                    "[ERROR] "
                    f"category=\"{category}\" "
                    f"keyword=\"{entry['keyword']}\" "
                    f"message=\"{error}\"",
                    flush=True,
                )
        result = analyze_keyword(category, entry["keyword"], entry["uploadDates"], videos)
        if should_search or videos:
            print_keyword_analysis_log(result)
        keyword_results.append(result)
    similar_pairs = []
    for index, left in enumerate(clean_keywords):
        for right in clean_keywords[index + 1 :]:
            score = jaccard_similarity(left, right)
            if score >= 50:
                similar_pairs.append(
                    {
                        "left": left,
                        "right": right,
                        "similarity": score,
                    }
                )

    nb_max_values = [item["nbMax"] for item in keyword_results]
    nb_min_values = [item["nbMin"] for item in keyword_results]
    keyword_lengths = [item["characterCountNoSpace"] for item in keyword_results]
    average_nb_max = round(mean(nb_max_values), 6) if nb_max_values else 0
    average_nb_min = round(mean(nb_min_values), 6) if nb_min_values else 0
    average_nb_gap = round(average_nb_max - average_nb_min, 6)
    
    # Upload-date analysis summary
    keywords_with_dates = [item for item in keyword_results if item["dateAnalysis"]["hasUploadDate"]]
    all_upload_dates = []
    for item in keyword_results:
        all_upload_dates.extend(item["dateAnalysis"]["uploadDates"])
    upload_date_counts = dict(Counter(all_upload_dates))
    newest_upload_date = max(all_upload_dates) if all_upload_dates else None
    oldest_upload_date = min(all_upload_dates) if all_upload_dates else None
    avg_recency_score = round(mean([item["dateAnalysis"]["recencyScore"] for item in keywords_with_dates]), 2) if keywords_with_dates else 0.0
    avg_combined_score = round(mean([item["combinedScore"] for item in keyword_results]), 6) if keyword_results else 0.0
    
    # Upload-date N/B values
    date_nb_max_values = [item["dateAnalysis"]["dateNbMax"] for item in keywords_with_dates]
    date_nb_min_values = [item["dateAnalysis"]["dateNbMin"] for item in keywords_with_dates]

    print(
        "[SUMMARY] "
        f"category=\"{category}\" "
        f"keywords={len(keyword_results)} "
        f"searched={search_target_count} "
        f"withUploadDates={len(keywords_with_dates)} "
        f"avgCombined={avg_combined_score} "
        f"errors={len(youtube_errors)}",
        flush=True,
    )

    return {
        "sourceFile": path.name,
        "category": category,
        "description": data.get("description", ""),
        "keywordCount": len(clean_keywords),
        "duplicateKeywords": duplicate_keywords,
        "youtubeSearch": {
            "enabled": bool(settings.get("youtubeSearchEnabled", True)),
            "requestedResultsPerKeyword": youtube_result_count,
            "searchedKeywordCount": sum(
                1 for index, _ in enumerate(keyword_entries) if should_fetch_youtube(index, settings)
            ),
            "errors": youtube_errors,
        },
        "summary": {
            "averageKeywordLength": round(mean(keyword_lengths), 2) if keyword_lengths else 0,
            "viewAnalysis": {
                "averageNbMax": average_nb_max,
                "averageNbMin": average_nb_min,
                "maxNbGap": average_nb_gap,
            },
            "dateAnalysis": {
                "keywordsWithDates": len(keywords_with_dates),
                "keywordsWithoutDates": len(clean_keywords) - len(keywords_with_dates),
                "uploadDateDistribution": upload_date_counts,
                "newestUploadDate": newest_upload_date,
                "oldestUploadDate": oldest_upload_date,
                "yearDistribution": {},
                "newestYear": None,
                "oldestYear": None,
                "averageRecencyScore": avg_recency_score,
                "averageDateNbMax": round(mean(date_nb_max_values), 6) if date_nb_max_values else 0,
                "averageDateNbMin": round(mean(date_nb_min_values), 6) if date_nb_min_values else 0,
            },
            "languageCounts": dict(Counter(item["language"] for item in keyword_results)),
            "averageCombinedScore": avg_combined_score,
        },
        "similarKeywordPairs": similar_pairs,
        "keywords": keyword_results,
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    keyword_files = sorted(KEYWORD_DIR.glob(f"*{KEYWORD_FILE_SUFFIX}"))[:MAX_CATEGORY_FILES]

    print("[START] NB Video Analyzer", flush=True)
    print(
        "[CONFIG] "
        f"youtubeSearchEnabled={bool(settings.get('youtubeSearchEnabled', True))} "
        f"resultsPerKeyword={int(settings.get('youtubeSearchResults', 5) or 5)} "
        f"maxKeywordsPerCategory={settings.get('youtubeMaxKeywords')} "
        f"timeoutSeconds={int(settings.get('youtubeSearchTimeoutSeconds', 60) or 60)}",
        flush=True,
    )
    print(
        "[CONFIG] "
        f"base=\"{BASE_DIR}\" "
        f"keywordDir=\"{KEYWORD_DIR}\" "
        f"keywordFiles={len(keyword_files)}",
        flush=True,
    )

    analyzed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    categories = [analyze_file(path, settings) for path in keyword_files]

    result = {
        "analyzedAt": analyzed_at,
        "baseDirectory": str(BASE_DIR),
        "keywordDirectory": str(KEYWORD_DIR),
        "sourceFiles": [path.name for path in keyword_files],
        "categoryCount": len(categories),
        "totalKeywordCount": sum(category["keywordCount"] for category in categories),
        "youtubeSearch": {
            "enabled": bool(settings.get("youtubeSearchEnabled", True)),
            "resultsPerKeyword": int(settings.get("youtubeSearchResults", 5) or 5),
            "maxKeywordsPerCategory": settings.get("youtubeMaxKeywords"),
        },
        "categories": categories,
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dated_result_path = RESULT_DIR / f"keyword_analysis_{timestamp}.json"
    latest_result_path = RESULT_DIR / "latest_keyword_analysis.json"

    output = json.dumps(result, ensure_ascii=False, indent=2)
    dated_result_path.write_text(output, encoding="utf-8")
    latest_result_path.write_text(output, encoding="utf-8")

    print(f"[DONE] analyzedKeywords={result['totalKeywordCount']} categories={result['categoryCount']}", flush=True)
    print(f"[SAVE] {dated_result_path}", flush=True)
    print(f"[SAVE] {latest_result_path}", flush=True)


if __name__ == "__main__":
    main()
