#!/usr/bin/env python3
"""WWWIEBUSCH Network Analyzer - Main entry point."""

import argparse
import sys
import time
from pathlib import Path

from network_analyzer import __version__
from network_analyzer.logger import NetworkAnalyzerLogger
from network_analyzer.utils import check_internet_connectivity, assess_network_health
from network_analyzer.ui import (
    show_banner,
    select_interface,
    show_interface_details,
    show_network_metrics,
    show_wifi_details,
    show_ping_results,
    show_speed_test_results,
    show_iperf3_results,
    show_health_status,
    show_progress,
    show_wifi_scan,
    show_dns_reliability,
    print_info,
    print_success,
    print_warning,
    print_error,
    set_logger,
    console
)
from network_analyzer.collectors.offline import (
    get_all_interfaces,
    get_interface_metrics,
    get_wifi_info,
    get_wifi_scan,
    get_routing_info,
    get_dns_servers,
    get_dhcp_info,
    get_network_dns_servers,
    run_ping_test
)
from network_analyzer.collectors.online import (
    get_public_ip,
    get_geolocation,
    run_speed_test,
    run_global_ping_tests,
    run_iperf3_test,
    check_connectivity,
    test_dns_reliability
)


def parse_arguments():
    """Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="WWWIEBUSCH Network Analyzer - Comprehensive network analysis tool for macOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                  Interactive mode
  %(prog)s -i en0                           Analyze specific interface
  %(prog)s --all                            Analyze all interfaces
  %(prog)s -i en0 --mode offline            Force offline mode
  %(prog)s -i en0 --no-wifi-scan            Skip WiFi scanning
  %(prog)s -i en0 --iperf3 192.168.1.100   Run iperf3 bandwidth test
  %(prog)s -i en0 --comment "HomeNetwork"  Annotate log files
        """
    )

    parser.add_argument(
        '-i', '--interface',
        help='Specific interface to analyze (e.g., en0)'
    )

    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Analyze all active interfaces'
    )

    parser.add_argument(
        '--mode',
        choices=['offline', 'online', 'auto'],
        default='auto',
        help='Operating mode (default: auto)'
    )

    parser.add_argument(
        '--no-wifi-scan',
        action='store_true',
        help='Skip WiFi network scanning'
    )

    parser.add_argument(
        '--skip-dns-test',
        action='store_true',
        help='Skip DNS reliability test (runs by default in online mode)'
    )

    parser.add_argument(
        '--output',
        help='Custom log file path'
    )

    parser.add_argument(
        '--iperf3',
        metavar='IP',
        help='Run iperf3 bandwidth test against the specified server IP'
    )

    parser.add_argument(
        '--comment',
        metavar='TEXT',
        help='Annotate log files with a comment (first word appended to filename)'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    return parser.parse_args()


def analyze_interface(
    interface_info,
    mode: str,
    skip_wifi_scan: bool,
    skip_dns_test: bool,
    logger: NetworkAnalyzerLogger,
    iperf3_ip: str = None
):
    """Analyze a single interface.

    Args:
        interface_info: InterfaceInfo object
        mode: Operating mode
        skip_wifi_scan: Whether to skip WiFi scanning
        skip_dns_test: Whether to skip DNS reliability test
        logger: Logger instance
        iperf3_ip: Optional iperf3 server IP for bandwidth testing
    """
    console.print()

    # Get DHCP and routing info early
    dhcp_info = get_dhcp_info(interface_info.name)
    routing_info = get_routing_info()
    gateway = routing_info.get('default_gateway')

    # Show interface details with full network info
    show_interface_details(interface_info, dhcp_info, gateway)
    logger.log_section('interface', {
        'name': interface_info.name,
        'hardware_port': interface_info.hardware_port,
        'mac': interface_info.mac_address,
        'ipv4': interface_info.ipv4_address,
        'status': interface_info.status
    })

    # Get network metrics
    console.print()
    with show_progress("Collecting network statistics...") as progress:
        task = progress.add_task("Collecting...", total=None)
        metrics = get_interface_metrics(interface_info.name)
        progress.update(task, completed=100)

    if metrics:
        show_network_metrics(metrics)
        logger.log_section('metrics', {
            'packets_in': metrics.packets_in,
            'packets_out': metrics.packets_out,
            'errors_in': metrics.errors_in,
            'errors_out': metrics.errors_out,
            'bytes_in': metrics.bytes_in,
            'bytes_out': metrics.bytes_out
        })
    else:
        print_warning("Could not retrieve network metrics")

    # WiFi-specific analysis
    wifi_info = None
    console.print()
    with show_progress("Checking WiFi status...") as progress:
        task = progress.add_task("Checking...", total=None)
        wifi_info = get_wifi_info(interface_info.name)
        progress.update(task, completed=100)

    if wifi_info:
        show_wifi_details(wifi_info)
        logger.log_section('wifi', {
            'ssid': wifi_info.ssid,
            'bssid': wifi_info.bssid,
            'channel': wifi_info.channel,
            'rssi': wifi_info.rssi,
            'snr': wifi_info.snr,
            'tx_rate': wifi_info.tx_rate,
            'phy_mode': wifi_info.phy_mode
        })

        # WiFi scan
        if not skip_wifi_scan:
            console.print()
            with show_progress("Scanning WiFi networks...") as progress:
                task = progress.add_task("Scanning...", total=None)
                networks = get_wifi_scan()
                progress.update(task, completed=100)

            if networks:
                show_wifi_scan(networks, limit=15)
                logger.log_section('wifi_scan', [
                    {
                        'ssid': n.ssid,
                        'channel': n.channel,
                        'rssi': n.rssi
                    } for n in networks[:15]
                ])

    # Network info already shown in interface details panel above

    # Offline ping tests
    ping_results = []
    if interface_info.status == "active":
        console.print()
        print_info("Running latency tests...")

        # Test gateway if available
        if gateway:
            with show_progress(f"Pinging gateway {gateway}...") as progress:
                task = progress.add_task("Pinging...", total=None)
                result = run_ping_test(gateway, count=10)
                if result:
                    ping_results.append(result)
                progress.update(task, completed=100)

    # Online mode tests
    speed_result = None
    if mode == 'online':
        console.print()
        print_info("Running online tests...")

        # Public IP and geolocation
        with show_progress("Getting public IP...") as progress:
            task = progress.add_task("Fetching...", total=None)
            public_ip = get_public_ip()
            if public_ip:
                print_success(f"Public IP: {public_ip.get('ip', 'Unknown')}")

                # Get geolocation
                geo = get_geolocation()
                if geo:
                    location = f"{geo.get('city', '')}, {geo.get('region', '')}, {geo.get('country', '')}"
                    print_info(f"Location: {location}")
                    print_info(f"ISP: {geo.get('isp', 'Unknown')}")
            progress.update(task, completed=100)

        # Global ping tests
        console.print()
        with show_progress("Testing global connectivity...") as progress:
            task = progress.add_task("Testing...", total=None)
            online_pings = run_global_ping_tests()
            ping_results.extend(online_pings)
            progress.update(task, completed=100)

        if ping_results:
            show_ping_results(ping_results)
            logger.log_section('ping_results', [
                {
                    'host': r.host,
                    'packet_loss': r.packet_loss,
                    'avg_rtt': r.avg_rtt,
                    'jitter': r.jitter
                } for r in ping_results
            ])

        # Speed test
        console.print()
        print_info("Running speed test (this may take up to 60 seconds)...")
        with show_progress("Testing network speed...") as progress:
            task = progress.add_task("Testing...", total=None)
            speed_result = run_speed_test(interface_info.name)
            progress.update(task, completed=100)

        if speed_result:
            show_speed_test_results(speed_result)
            logger.log_section('speed_test', {
                'download_mbps': speed_result.download_mbps,
                'upload_mbps': speed_result.upload_mbps,
                'latency_ms': speed_result.latency_ms,
                'responsiveness': speed_result.responsiveness
            })
        else:
            print_warning("Speed test not available (requires macOS 12.1+)")

        # iperf3 bandwidth test (if server IP provided)
        if iperf3_ip:
            console.print()
            print_info(f"Running iperf3 bandwidth test to {iperf3_ip}...")
            with show_progress("Running iperf3 test...") as progress:
                task = progress.add_task("Testing...", total=None)
                iperf3_result = run_iperf3_test(iperf3_ip)
                progress.update(task, completed=100)

            show_iperf3_results(iperf3_result)
            logger.log_section('iperf3', {
                'server': iperf3_result.server,
                'upload_mbps': iperf3_result.upload_mbps,
                'download_mbps': iperf3_result.download_mbps,
                'upload_retransmits': iperf3_result.upload_retransmits,
                'download_retransmits': iperf3_result.download_retransmits,
                'duration_s': iperf3_result.duration_s,
                'error': iperf3_result.error
            })

        # DNS reliability test (runs by default in online mode)
        if not skip_dns_test:
            console.print()
            print_info("Testing DNS server reliability with 100 domains (this may take 1-2 minutes)...")

            # Get network DNS servers (from DHCP, not local 127.x)
            network_dns = get_network_dns_servers(interface_info.name)
            configured_dns = network_dns[0] if network_dns else None

            # Note: Some routers advertise themselves as DNS via DHCP but block
            # direct DNS queries. We test system default which uses the actual
            # working DNS path (which may be forwarded through the router).
            if configured_dns:
                print_info(f"Network DNS: {configured_dns} (from DHCP)")
                print_info("Testing via system DNS resolver (may use upstream servers)")

            with show_progress("Testing DNS reliability...") as progress:
                task = progress.add_task("Testing...", total=None)

                # Use system default DNS (None) as it handles router forwarding
                dns_result = test_dns_reliability(dns_server=None, num_domains=100)
                progress.update(task, completed=100)

            show_dns_reliability(dns_result)
            logger.log_section('dns_reliability', dns_result)

    elif ping_results:
        show_ping_results(ping_results)

    # Health assessment
    console.print()
    health = assess_network_health(
        interface_info,
        metrics,
        wifi_info,
        ping_results,
        speed_result
    )

    show_health_status(health)
    logger.log_section('health', {
        'overall': health.overall,
        'score': health.score,
        'warnings': health.warnings,
        'errors': health.errors
    })


def main():
    """Main application entry point."""
    args = parse_arguments()

    # Initialize logger
    log_dir = str(Path(args.output).parent) if args.output else "./logs"
    logger = NetworkAnalyzerLogger(log_dir, comment=args.comment)

    # Set logger for UI dual output
    set_logger(logger)

    start_time = time.time()

    try:
        # Determine mode
        mode = args.mode
        if mode == 'auto':
            mode = 'online' if check_internet_connectivity() else 'offline'

        # Show banner
        show_banner(mode, args.interface)
        logger.log_section('session', {
            'mode': mode,
            'interface': args.interface,
            'version': __version__,
            'comment': args.comment or '',
            'iperf3_server': args.iperf3 or ''
        })

        # Get all interfaces
        print_info("Detecting network interfaces...")
        interfaces = get_all_interfaces()

        if not interfaces:
            print_error("No network interfaces found!")
            return 1

        # Filter active interfaces if --all flag is used
        if args.all:
            active_interfaces = [i for i in interfaces if i.status == "active"]
            if not active_interfaces:
                print_error("No active interfaces found!")
                return 1

            print_success(f"Found {len(active_interfaces)} active interface(s)")
            for iface in active_interfaces:
                analyze_interface(iface, mode, args.no_wifi_scan, args.skip_dns_test, logger, args.iperf3)
                console.print("\n" + "="*80 + "\n")

        else:
            # Select interface
            if args.interface:
                # Find specified interface
                selected = next(
                    (i for i in interfaces if i.name == args.interface),
                    None
                )
                if not selected:
                    print_error(f"Interface '{args.interface}' not found!")
                    print_info("Available interfaces:")
                    for iface in interfaces:
                        console.print(f"  - {iface.name} ({iface.hardware_port})")
                    return 1
            else:
                # Interactive selection
                selected = select_interface(interfaces)
                if not selected:
                    return 1

            # Analyze selected interface
            analyze_interface(selected, mode, args.no_wifi_scan, args.skip_dns_test, logger, args.iperf3)

        # Summary
        elapsed = time.time() - start_time
        console.print()
        print_success(f"Analysis completed in {elapsed:.1f} seconds")

        # Save logs
        logger.save_json()
        print_info(f"Logs saved to:")
        print_info(f"  - Detailed: {logger.get_log_path()}")
        print_info(f"  - Output: {logger.text_log_file}")
        print_info(f"  - JSON: {logger.get_log_path().replace('.log', '.json')}")

        return 0

    except KeyboardInterrupt:
        console.print()
        print_warning("Analysis interrupted by user")
        return 130

    except Exception as e:
        console.print()
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
