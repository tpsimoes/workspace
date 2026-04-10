"""
pcap_analyzer.py — 网络抓包文件分析工具

支持 tshark（优先）和 pyshark（备用），自动检测可用工具。

用法：
    python pcap_analyzer.py <file.pcap> [--filter tcp_rst|retrans|dns_fail|tls|all]
"""

import subprocess
import shutil
import sys
import json
import argparse
from pathlib import Path


# ── 工具检测 ──────────────────────────────────────────────────────────────────
def detect_tool() -> str:
    """自动检测可用的分析工具，返回 'tshark' / 'pyshark' / None"""
    if shutil.which("tshark"):
        return "tshark"
    try:
        import pyshark  # noqa: F401  # type: ignore
        return "pyshark"
    except ImportError:
        pass
    return None


# ── tshark 分析模块 ───────────────────────────────────────────────────────────
def tshark_run(pcap_file: str, display_filter: str, fields: list[str]) -> list[dict]:
    """执行 tshark 并返回结构化结果"""
    cmd = ["tshark", "-r", pcap_file, "-Y", display_filter, "-T", "fields"]
    for f in fields:
        cmd += ["-e", f]
    cmd += ["-E", "separator=|", "-E", "quote=n"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        rows = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|")
            rows.append(dict(zip(fields, parts)))
        return rows
    except subprocess.TimeoutExpired:
        print("[ERROR] tshark timed out", file=sys.stderr)
        return []


def tshark_basic_info(pcap_file: str) -> None:
    """输出 pcap 基本信息"""
    print("\n[Basic Info]")
    subprocess.run(["tshark", "-r", pcap_file, "-q", "-z", "io,stat,0"], timeout=30)


def tshark_tcp_rst(pcap_file: str) -> None:
    print("\n[TCP RST Events]")
    rows = tshark_run(pcap_file, "tcp.flags.reset==1",
                      ["frame.time", "ip.src", "ip.dst", "tcp.srcport", "tcp.dstport"])
    if not rows:
        print("  None found.")
        return
    print(f"  Count: {len(rows)}")
    for r in rows[:20]:
        print(f"  {r.get('frame.time','')} | {r.get('ip.src','')}:{r.get('tcp.srcport','')} → "
              f"{r.get('ip.dst','')}:{r.get('tcp.dstport','')}")


def tshark_retransmissions(pcap_file: str) -> None:
    print("\n[TCP Retransmissions]")
    rows = tshark_run(pcap_file, "tcp.analysis.retransmission",
                      ["frame.time", "ip.src", "ip.dst", "tcp.stream"])
    if not rows:
        print("  None found.")
        return
    print(f"  Total retransmissions: {len(rows)}")
    streams = {}
    for r in rows:
        s = r.get("tcp.stream", "?")
        streams[s] = streams.get(s, 0) + 1
    top = sorted(streams.items(), key=lambda x: x[1], reverse=True)[:5]
    print("  Top retransmission streams:")
    for stream, count in top:
        print(f"    Stream {stream}: {count} retransmissions")


def tshark_dns_failures(pcap_file: str) -> None:
    print("\n[DNS Failures (rcode > 0)]")
    rows = tshark_run(pcap_file, "dns.flags.rcode > 0",
                      ["frame.time", "ip.src", "dns.qry.name", "dns.flags.rcode"])
    RCODE_MAP = {"1": "FormErr", "2": "ServFail", "3": "NXDomain",
                 "4": "NotImp", "5": "Refused"}
    if not rows:
        print("  None found.")
        return
    for r in rows[:20]:
        rcode = r.get("dns.flags.rcode", "?")
        print(f"  {r.get('frame.time','')} | {r.get('ip.src','')} queried "
              f"'{r.get('dns.qry.name','')}' → {RCODE_MAP.get(rcode, rcode)}")


def tshark_tls_alerts(pcap_file: str) -> None:
    print("\n[TLS Alerts]")
    rows = tshark_run(pcap_file, "tls.alert_message",
                      ["frame.time", "ip.src", "ip.dst", "tls.alert_message.desc"])
    if not rows:
        print("  None found.")
        return
    for r in rows[:20]:
        print(f"  {r.get('frame.time','')} | {r.get('ip.src','')} → {r.get('ip.dst','')} "
              f"Alert: {r.get('tls.alert_message.desc','')}")


def tshark_top_talkers(pcap_file: str) -> None:
    print("\n[Top TCP Conversations]")
    subprocess.run(["tshark", "-r", pcap_file, "-q", "-z", "conv,tcp"], timeout=30)


# ── pyshark 分析模块 ──────────────────────────────────────────────────────────
def pyshark_analyze(pcap_file: str) -> None:
    import pyshark  # type: ignore

    print("\n[pyshark Analysis]")
    cap = pyshark.FileCapture(pcap_file, keep_packets=False)

    stats = {"total": 0, "tcp_rst": 0, "retrans": 0, "dns_fail": 0, "tls_alert": 0}
    rst_examples, dns_fail_examples, tls_examples = [], [], []

    for pkt in cap:
        stats["total"] += 1
        try:
            if hasattr(pkt, 'tcp'):
                if pkt.tcp.flags_reset == '1':
                    stats["tcp_rst"] += 1
                    if len(rst_examples) < 5:
                        rst_examples.append(
                            f"  {pkt.sniff_time} | {pkt.ip.src}:{pkt.tcp.srcport} → {pkt.ip.dst}:{pkt.tcp.dstport}")
                if hasattr(pkt.tcp, 'analysis_retransmission'):
                    stats["retrans"] += 1
            if hasattr(pkt, 'dns') and hasattr(pkt.dns, 'flags_rcode'):
                if int(pkt.dns.flags_rcode) > 0:
                    stats["dns_fail"] += 1
                    if len(dns_fail_examples) < 5:
                        dns_fail_examples.append(
                            f"  {pkt.sniff_time} | {pkt.ip.src} → {getattr(pkt.dns, 'qry_name', '?')} rcode={pkt.dns.flags_rcode}")
            if hasattr(pkt, 'tls') and hasattr(pkt.tls, 'alert_message'):
                stats["tls_alert"] += 1
                if len(tls_examples) < 5:
                    tls_examples.append(f"  {pkt.sniff_time} | Alert: {pkt.tls.alert_message}")
        except AttributeError:
            continue

    cap.close()

    print(f"  Total packets: {stats['total']}")
    print(f"  TCP RST: {stats['tcp_rst']}")
    if rst_examples:
        for e in rst_examples: print(e)
    print(f"  TCP Retransmissions: {stats['retrans']}")
    print(f"  DNS Failures: {stats['dns_fail']}")
    if dns_fail_examples:
        for e in dns_fail_examples: print(e)
    print(f"  TLS Alerts: {stats['tls_alert']}")
    if tls_examples:
        for e in tls_examples: print(e)


# ── 主入口 ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='pcap analyzer')
    parser.add_argument('pcap', help='Path to pcap/pcapng file')
    parser.add_argument('--filter', default='all',
                        choices=['all', 'tcp_rst', 'retrans', 'dns_fail', 'tls'],
                        help='Analysis type')
    args = parser.parse_args()

    if not Path(args.pcap).exists():
        print(f"[ERROR] File not found: {args.pcap}", file=sys.stderr)
        sys.exit(1)

    tool = detect_tool()
    if not tool:
        print("[ERROR] Neither tshark nor pyshark is available.")
        print("Install tshark: sudo apt install tshark")
        print("Install pyshark: pip install pyshark")
        sys.exit(1)

    print(f"[INFO] Using tool: {tool}")
    print(f"[INFO] Analyzing: {args.pcap}")

    if tool == "tshark":
        tshark_basic_info(args.pcap)
        if args.filter in ('all', 'tcp_rst'):
            tshark_tcp_rst(args.pcap)
        if args.filter in ('all', 'retrans'):
            tshark_retransmissions(args.pcap)
        if args.filter in ('all', 'dns_fail'):
            tshark_dns_failures(args.pcap)
        if args.filter in ('all', 'tls'):
            tshark_tls_alerts(args.pcap)
        if args.filter == 'all':
            tshark_top_talkers(args.pcap)
    else:
        pyshark_analyze(args.pcap)


if __name__ == '__main__':
    main()
