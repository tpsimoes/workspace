"""
correlator.py — 多文件跨层事件关联分析

将多个日志文件的关键事件合并为统一时间线，
并按 correlation-rules.md 中定义的规则识别跨层因果链。

用法：
    python correlator.py <file1> <file2> ... [--window 60]
"""

import re
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, field


# ── 数据结构 ──────────────────────────────────────────────────────────────────
@dataclass
class LogEvent:
    timestamp: datetime
    source: str
    layer: str        # os / middleware / network / app / cluster
    line: str
    is_key: bool = True
    tags: list[str] = field(default_factory=list)


# ── 层级识别 ──────────────────────────────────────────────────────────────────
LAYER_PATTERNS = {
    'os':         re.compile(r'syslog|messages|dmesg|kern|auth|journal|secure', re.I),
    'cluster':    re.compile(r'pacemaker|corosync|crm|stonith|pcmk', re.I),
    'middleware': re.compile(r'nginx|apache|httpd|mysql|mssql|hana|postgresql', re.I),
    'sap':        re.compile(r'dev_w|sapstart|syslog.*sap|hana.*trc', re.I),
    'k8s':        re.compile(r'kubelet|containerd|pod.*log|k8s', re.I),
    'network':    re.compile(r'\.pcap|\.pcapng|tcpdump', re.I),
    'azure':      re.compile(r'activity.*log|azure.*diag|boot.*diag', re.I),
}

def detect_layer(filename: str) -> str:
    for layer, pattern in LAYER_PATTERNS.items():
        if pattern.search(filename):
            return layer
    return 'unknown'


# ── 事件标签提取 ──────────────────────────────────────────────────────────────
TAG_RULES = {
    'oom':        re.compile(r'out of memory|oom.?killer|killed process', re.I),
    'io_error':   re.compile(r'i/o error|buffer i/o|blk_update_request', re.I),
    'tcp_rst':    re.compile(r'connection reset|tcp.*rst', re.I),
    'timeout':    re.compile(r'timed? out|timeout', re.I),
    'fencing':    re.compile(r'stonith|will be fenced|fencing agent', re.I),
    'restart':    re.compile(r'restarting|restarted|restart', re.I),
    'panic':      re.compile(r'kernel panic|panic|oops', re.I),
    'nic_down':   re.compile(r'link.?(is.?)?down|nic.*down|eth.*down', re.I),
    'dns_fail':   re.compile(r'nxdomain|servfail|dns.*fail', re.I),
    'tls_error':  re.compile(r'tls alert|ssl.*error|certificate.*error', re.I),
    'crash':      re.compile(r'crash|core dump|segfault|aborted', re.I),
}

def extract_tags(line: str) -> list[str]:
    return [tag for tag, pattern in TAG_RULES.items() if pattern.search(line)]


# ── 时间戳解析（复用 log_normalizer 逻辑）────────────────────────────────────
TIMESTAMP_PATTERNS = [
    (re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'), '%Y-%m-%dT%H:%M:%S'),
    (re.compile(r'([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'), '%b %d %H:%M:%S'),
    (re.compile(r'(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})'), '%d/%b/%Y:%H:%M:%S'),
    (re.compile(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'), '%Y-%m-%d %H:%M:%S'),
]

CRITICAL_RE = re.compile(
    r'\b(error|fail|fatal|critical|panic|abort|killed|oom|timeout|refused|reset|disconnect|crash)\b',
    re.I
)

def parse_ts(line: str) -> datetime | None:
    for pattern, fmt in TIMESTAMP_PATTERNS:
        m = pattern.search(line)
        if m:
            s = m.group(1).strip()
            if fmt == '%b %d %H:%M:%S':
                s = f"{datetime.now().year} {s}"
                fmt = '%Y %b %d %H:%M:%S'
            try:
                dt = datetime.strptime(s[:19], fmt[:len(fmt)])
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


# ── 文件读取与事件提取 ────────────────────────────────────────────────────────
def load_events(filepath: str) -> list[LogEvent]:
    layer = detect_layer(Path(filepath).name)
    events = []
    for enc in ['utf-8', 'latin-1']:
        try:
            lines = Path(filepath).read_text(encoding=enc).splitlines()
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    else:
        print(f"[WARN] Cannot read: {filepath}", file=sys.stderr)
        return []

    for line in lines:
        if not CRITICAL_RE.search(line):
            continue
        ts = parse_ts(line)
        if not ts:
            continue
        tags = extract_tags(line)
        events.append(LogEvent(
            timestamp=ts,
            source=Path(filepath).name,
            layer=layer,
            line=line.strip(),
            tags=tags
        ))
    return events


# ── 跨层关联规则 ──────────────────────────────────────────────────────────────
CORRELATION_RULES = [
    {
        'id': 'R1',
        'name': 'OOM → 服务中断',
        'trigger_tags': ['oom'],
        'effect_tags':  ['timeout', 'tcp_rst', 'restart'],
        'window_sec':   60,
        'confidence':   'HIGH',
    },
    {
        'id': 'R2',
        'name': '磁盘 I/O 错误 → 数据库写入失败',
        'trigger_tags': ['io_error'],
        'effect_tags':  ['timeout'],
        'window_sec':   120,
        'confidence':   'HIGH',
    },
    {
        'id': 'R3',
        'name': 'NIC Down → 网络连接中断',
        'trigger_tags': ['nic_down'],
        'effect_tags':  ['tcp_rst', 'timeout', 'dns_fail'],
        'window_sec':   30,
        'confidence':   'HIGH',
    },
    {
        'id': 'R4',
        'name': 'Fencing 触发 → 资源切换',
        'trigger_tags': ['fencing'],
        'effect_tags':  ['restart'],
        'window_sec':   300,
        'confidence':   'HIGH',
    },
    {
        'id': 'R5',
        'name': 'Kernel Panic → 系统重启',
        'trigger_tags': ['panic'],
        'effect_tags':  ['restart'],
        'window_sec':   180,
        'confidence':   'HIGH',
    },
    {
        'id': 'R6',
        'name': 'TCP RST / 超时 → 应用层错误',
        'trigger_tags': ['tcp_rst', 'timeout'],
        'effect_tags':  ['timeout'],
        'window_sec':   60,
        'confidence':   'MEDIUM',
    },
]

def find_correlations(events: list[LogEvent]) -> list[dict]:
    found = []
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    for i, trigger_ev in enumerate(sorted_events):
        for rule in CORRELATION_RULES:
            if not any(t in trigger_ev.tags for t in rule['trigger_tags']):
                continue
            window = timedelta(seconds=rule['window_sec'])
            effects = []
            for j in range(i + 1, len(sorted_events)):
                eff = sorted_events[j]
                if eff.timestamp - trigger_ev.timestamp > window:
                    break
                if eff.source == trigger_ev.source and eff.layer == trigger_ev.layer:
                    continue  # 跳过同文件同层，要求跨层
                if any(t in eff.tags for t in rule['effect_tags']):
                    effects.append(eff)

            if effects:
                found.append({
                    'rule': rule,
                    'trigger': trigger_ev,
                    'effects': effects[:3],
                })

    return found


# ── 输出 ──────────────────────────────────────────────────────────────────────
def print_timeline(events: list[LogEvent]) -> None:
    print("\n" + "="*70)
    print("MERGED TIMELINE")
    print("="*70)
    for ev in sorted(events, key=lambda e: e.timestamp):
        tags_str = f" [{', '.join(ev.tags)}]" if ev.tags else ""
        print(f"[{ev.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
              f"[{ev.layer.upper():10}] [{ev.source}]{tags_str}")
        print(f"  {ev.line[:120]}")


def print_correlations(correlations: list[dict]) -> None:
    if not correlations:
        print("\n[No cross-layer correlations found]")
        return
    print("\n" + "="*70)
    print("CROSS-LAYER CORRELATIONS")
    print("="*70)
    for c in correlations:
        rule = c['rule']
        tr = c['trigger']
        print(f"\n[{rule['confidence']}] {rule['id']}: {rule['name']}")
        print(f"  TRIGGER [{tr.timestamp.strftime('%H:%M:%S')}] [{tr.source}] {tr.line[:100]}")
        for eff in c['effects']:
            print(f"  EFFECT  [{eff.timestamp.strftime('%H:%M:%S')}] [{eff.source}] {eff.line[:100]}")


def print_summary(events: list[LogEvent], correlations: list[dict]) -> None:
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    from collections import Counter
    tag_counts = Counter(t for ev in events for t in ev.tags)
    print(f"Total key events: {len(events)}")
    print(f"Tag distribution: {dict(tag_counts.most_common(8))}")
    high = [c for c in correlations if c['rule']['confidence'] == 'HIGH']
    if high:
        print(f"\nHigh-confidence causal chains ({len(high)}):")
        for c in high:
            print(f"  • {c['rule']['name']}")
            print(f"    {c['trigger'].source} → {c['effects'][0].source}")
    else:
        print("\nNo high-confidence causal chains identified.")
    print("\nRecommended next steps:")
    if tag_counts.get('oom', 0) > 0:
        print("  1. Investigate memory pressure: review memory limits and OOM trigger timing")
    if tag_counts.get('io_error', 0) > 0:
        print("  2. Check disk health: run fsck / review SMART data")
    if tag_counts.get('fencing', 0) > 0:
        print("  3. Review cluster fencing configuration and agent credentials")
    if tag_counts.get('tls_error', 0) > 0:
        print("  4. Inspect TLS certificates: expiration, CN/SANs, trust chain")


# ── 主入口 ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Multi-log correlator')
    parser.add_argument('files', nargs='+', help='Log file paths')
    parser.add_argument('--window', type=int, default=60, help='Default correlation window (seconds)')
    args = parser.parse_args()

    all_events = []
    for f in args.files:
        evs = load_events(f)
        print(f"[{f}] Extracted {len(evs)} key events")
        all_events.extend(evs)

    if not all_events:
        print("[INFO] No key events found across all files.")
        return

    correlations = find_correlations(all_events)
    print_timeline(all_events)
    print_correlations(correlations)
    print_summary(all_events, correlations)


if __name__ == '__main__':
    main()
