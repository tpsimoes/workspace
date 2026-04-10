"""
log_normalizer.py — 日志关键事件提取与时间戳标准化

用法：
    python log_normalizer.py <logfile> [--type auto|syslog|nginx|k8s|sap]
    python log_normalizer.py <logfile1> <logfile2> ... --merge
"""

import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ── 关键词过滤 ───────────────────────────────────────────────────────────────
CRITICAL_KEYWORDS = re.compile(
    r'\b(error|fail|failed|failure|fatal|critical|panic|abort|killed|'
    r'oom|out of memory|segfault|segmentation fault|core dumped|'
    r'timeout|timed out|refused|unreachable|reset|disconnect|'
    r'exception|traceback|crash|emergency|alert|crit)\b',
    re.IGNORECASE
)

CONTEXT_LINES = 5  # 关键行前后各保留的行数


# ── 时间戳解析器 ──────────────────────────────────────────────────────────────
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-03-07T14:23:01.123Z
    (re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)'),
     '%Y-%m-%dT%H:%M:%S'),
    # syslog: Mar  7 14:23:01
    (re.compile(r'([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'),
     '%b %d %H:%M:%S'),
    # common log: 07/Mar/2024:14:23:01 +0000
    (re.compile(r'(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2}\s[+-]\d{4})'),
     '%d/%b/%Y:%H:%M:%S %z'),
    # 2024-03-07 14:23:01
    (re.compile(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'),
     '%Y-%m-%d %H:%M:%S'),
]


def parse_timestamp(line: str) -> datetime | None:
    for pattern, fmt in TIMESTAMP_PATTERNS:
        m = pattern.search(line)
        if m:
            ts_str = m.group(1).strip()
            # 补充年份（syslog 格式无年份，使用当前年）
            if fmt == '%b %d %H:%M:%S':
                ts_str = f"{datetime.now().year} {ts_str}"
                fmt = '%Y %b %d %H:%M:%S'
            try:
                dt = datetime.strptime(ts_str[:19], fmt[:len(fmt)])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                continue
    return None


# ── 关键行提取 ────────────────────────────────────────────────────────────────
def extract_key_lines(lines: list[str]) -> list[dict]:
    """提取关键行及其上下文，去重合并重叠窗口"""
    key_indices = set()
    for i, line in enumerate(lines):
        if CRITICAL_KEYWORDS.search(line):
            for j in range(max(0, i - CONTEXT_LINES), min(len(lines), i + CONTEXT_LINES + 1)):
                key_indices.add(j)

    results = []
    prev_idx = -2
    block = []

    for idx in sorted(key_indices):
        if idx > prev_idx + 1 and block:
            results.append({'lines': block, 'start_idx': block[0]['idx']})
            block = []
        block.append({
            'idx': idx,
            'line': lines[idx].rstrip(),
            'is_key': bool(CRITICAL_KEYWORDS.search(lines[idx])),
            'timestamp': parse_timestamp(lines[idx])
        })
        prev_idx = idx

    if block:
        results.append({'lines': block, 'start_idx': block[0]['idx']})

    return results


# ── 文件读取 ──────────────────────────────────────────────────────────────────
def read_file_safe(path: str) -> list[str]:
    """尝试多种编码读取文件"""
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try:
            return Path(path).read_text(encoding=enc).splitlines()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    print(f"[WARN] Cannot read file: {path}", file=sys.stderr)
    return []


# ── 输出格式化 ────────────────────────────────────────────────────────────────
def format_blocks(blocks: list[dict], source: str) -> str:
    output = [f"\n{'='*60}", f"Source: {source}", f"{'='*60}"]
    for block in blocks:
        output.append(f"\n--- Lines {block['start_idx']+1}+ ---")
        for entry in block['lines']:
            marker = ">>>" if entry['is_key'] else "   "
            ts_str = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC') if entry['timestamp'] else '(no timestamp)'
            output.append(f"{marker} [{ts_str}] {entry['line']}")
    return '\n'.join(output)


# ── 主入口 ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Log key event extractor')
    parser.add_argument('files', nargs='+', help='Log file paths')
    parser.add_argument('--merge', action='store_true', help='Merge and sort all key events by timestamp')
    args = parser.parse_args()

    all_events = []

    for filepath in args.files:
        lines = read_file_safe(filepath)
        if not lines:
            continue
        blocks = extract_key_lines(lines)
        print(f"\n[{filepath}] Total lines: {len(lines)}, Key blocks: {len(blocks)}")

        if args.merge:
            for block in blocks:
                for entry in block['lines']:
                    if entry['is_key'] and entry['timestamp']:
                        all_events.append({
                            'timestamp': entry['timestamp'],
                            'source': filepath,
                            'line': entry['line']
                        })
        else:
            print(format_blocks(blocks, filepath))

    if args.merge and all_events:
        print(f"\n{'='*60}")
        print("MERGED TIMELINE (UTC)")
        print('='*60)
        for ev in sorted(all_events, key=lambda x: x['timestamp']):
            print(f"[{ev['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] [{ev['source']}] {ev['line'][:120]}")


if __name__ == '__main__':
    main()
