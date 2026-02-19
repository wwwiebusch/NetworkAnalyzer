"""Terminal UI components using Rich library."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.layout import Layout
from rich import box
from typing import Optional, List
from network_analyzer.models import (
    InterfaceInfo,
    NetworkMetrics,
    WiFiInfo,
    PingResult,
    SpeedTestResult,
    HealthStatus,
    NetworkScan,
    IperfResult
)
from network_analyzer.utils import format_bytes
from io import StringIO

console = Console()
_logger_instance = None


def set_logger(logger):
    """Set the logger instance for dual output.

    Args:
        logger: NetworkAnalyzerLogger instance
    """
    global _logger_instance
    _logger_instance = logger


def _log_output(renderable):
    """Log the output to file in plain text format.

    Args:
        renderable: Rich renderable object
    """
    if _logger_instance:
        # Create a console that writes to string
        string_io = StringIO()
        temp_console = Console(file=string_io, width=80, legacy_windows=False)
        temp_console.print(renderable)
        text = string_io.getvalue()
        _logger_instance.write_output(text.rstrip())


def show_banner(mode: str, interface: Optional[str] = None):
    """Display application banner.

    Args:
        mode: Operating mode (online/offline)
        interface: Selected interface name
    """
    from network_analyzer import __version__
    import datetime

    title = "WWWIEBUSCH Network Analyzer"
    subtitle = f"v{__version__} | Mode: {mode.upper()}"
    if interface:
        subtitle += f" | Interface: {interface}"

    subtitle += f"\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    panel = Panel(
        Text(subtitle, justify="center"),
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        box=box.DOUBLE
    )

    console.print()
    console.print(panel)
    _log_output(panel)
    console.print()

    # Log to file
    _log_output(panel)


def select_interface(interfaces: list[InterfaceInfo]) -> Optional[InterfaceInfo]:
    """Interactive interface selection.

    Args:
        interfaces: List of available interfaces

    Returns:
        Selected InterfaceInfo or None
    """
    if not interfaces:
        console.print("[red]No network interfaces found![/red]")
        return None

    # Display interfaces table
    table = Table(title="Available Network Interfaces", box=box.ROUNDED)
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Interface", style="bold")
    table.add_column("Hardware Port", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("IP Address", style="blue")

    for idx, iface in enumerate(interfaces, 1):
        status_color = "green" if iface.status == "active" else "dim"
        ip_addr = iface.ipv4_address or "No IP"

        table.add_row(
            str(idx),
            iface.name,
            iface.hardware_port,
            f"[{status_color}]{iface.status}[/{status_color}]",
            ip_addr
        )

    console.print(table)
    _log_output(table)
    console.print()

    # Prompt for selection
    choice = Prompt.ask(
        "Select interface",
        choices=[str(i) for i in range(1, len(interfaces) + 1)],
        default="1"
    )

    return interfaces[int(choice) - 1]


def show_interface_details(info: InterfaceInfo, dhcp_info: Optional[dict] = None, gateway: Optional[str] = None):
    """Display interface information with full network details.

    Args:
        info: InterfaceInfo object
        dhcp_info: Optional DHCP configuration dictionary
        gateway: Optional gateway/router address
    """
    from network_analyzer.parsers.dhcp import format_lease_time

    status_symbol = "✓" if info.status == "active" else "✗"
    status_color = "green" if info.status == "active" else "red"

    details = f"""[bold]Status[/bold]      [{status_color}]{status_symbol} {info.status.title()}[/{status_color}]
[bold]MAC Address[/bold] {info.mac_address}
[bold]IPv4[/bold]        {info.ipv4_address or 'Not assigned'}"""

    if info.netmask:
        details += f"/{info.netmask}"

    # Gateway/Router
    if gateway:
        details += f"\n[bold]Gateway[/bold]     {gateway}"
    elif dhcp_info and dhcp_info.get('router'):
        details += f"\n[bold]Gateway[/bold]     {dhcp_info['router']}"

    # Subnet Mask (already shown in CIDR, but show separately if available)
    if dhcp_info and dhcp_info.get('subnet_mask'):
        details += f"\n[bold]Subnet Mask[/bold] {dhcp_info['subnet_mask']}"

    # DHCP Status
    if dhcp_info:
        details += f"\n[bold]DHCP[/bold]        ✓ Enabled"
        if dhcp_info.get('server'):
            details += f"\n[bold]DHCP Server[/bold] {dhcp_info['server']}"
        if dhcp_info.get('domain_name'):
            details += f"\n[bold]Domain[/bold]      {dhcp_info['domain_name']}"
        if dhcp_info.get('lease_time'):
            lease_str = format_lease_time(dhcp_info['lease_time'])
            details += f"\n[bold]Lease Time[/bold]  {lease_str}"
    else:
        details += f"\n[bold]DHCP[/bold]        ✗ Static/Manual"

    # DNS Servers from DHCP/Network
    if dhcp_info and dhcp_info.get('dns_servers'):
        dns_list = ', '.join(dhcp_info['dns_servers'])
        details += f"\n[bold]DNS Servers[/bold] {dns_list}"

    # IPv6 addresses
    if info.ipv6_addresses:
        details += f"\n[bold]IPv6[/bold]        {info.ipv6_addresses[0]}"
        for ipv6 in info.ipv6_addresses[1:]:
            details += f"\n                {ipv6}"

    # MTU and Media
    if info.mtu:
        details += f"\n[bold]MTU[/bold]         {info.mtu}"

    if info.media_type:
        details += f"\n[bold]Media[/bold]       {info.media_type}"

    panel = Panel(
        details,
        title=f"[bold]Interface: {info.name} ({info.hardware_port})[/bold]",
        border_style="blue",
        box=box.ROUNDED
    )

    console.print(panel)
    _log_output(panel)


def show_network_metrics(metrics: NetworkMetrics):
    """Display network metrics.

    Args:
        metrics: NetworkMetrics object
    """
    table = Table(title="Network Statistics", box=box.ROUNDED, show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    total_packets = metrics.packets_in + metrics.packets_out
    total_errors = metrics.errors_in + metrics.errors_out

    error_rate = (total_errors / total_packets * 100) if total_packets > 0 else 0
    error_color = "green" if error_rate < 0.1 else "yellow" if error_rate < 1 else "red"

    table.add_row("Packets In", f"{metrics.packets_in:,}")
    table.add_row("Packets Out", f"{metrics.packets_out:,}")
    table.add_row("Bytes In", format_bytes(metrics.bytes_in))
    table.add_row("Bytes Out", format_bytes(metrics.bytes_out))
    table.add_row("Errors In", f"[{error_color}]{metrics.errors_in:,}[/{error_color}]")
    table.add_row("Errors Out", f"[{error_color}]{metrics.errors_out:,}[/{error_color}]")
    table.add_row("Collisions", f"{metrics.collisions:,}")

    console.print(table)
    _log_output(table)


def show_wifi_details(wifi: WiFiInfo):
    """Display WiFi connection details.

    Args:
        wifi: WiFiInfo object
    """
    # Signal quality color coding
    signal_quality = wifi.signal_quality
    if signal_quality == "excellent":
        signal_color = "green"
        signal_symbol = "✓"
    elif signal_quality == "good":
        signal_color = "cyan"
        signal_symbol = "✓"
    elif signal_quality == "fair":
        signal_color = "yellow"
        signal_symbol = "⚠"
    else:
        signal_color = "red"
        signal_symbol = "✗"

    # SNR quality
    snr_color = "green" if wifi.snr > 40 else "yellow" if wifi.snr > 30 else "red"

    details = f"""[bold]SSID[/bold]        {wifi.ssid}
[bold]BSSID[/bold]       {wifi.bssid}
[bold]Channel[/bold]     {wifi.channel} ({wifi.band}"""

    if wifi.channel_width:
        details += f", {wifi.channel_width}MHz"
    details += ")"

    details += f"""
[bold]Signal[/bold]      [{signal_color}]{wifi.rssi} dBm {signal_symbol} {signal_quality.title()}[/{signal_color}]
[bold]Noise[/bold]       {wifi.noise} dBm
[bold]SNR[/bold]         [{snr_color}]{wifi.snr} dB[/{snr_color}]
[bold]TX Rate[/bold]     {wifi.tx_rate} Mbps"""

    if wifi.phy_mode:
        details += f"\n[bold]PHY Mode[/bold]    {wifi.phy_mode}"

    if wifi.security:
        details += f"\n[bold]Security[/bold]    {wifi.security}"

    if wifi.mcs_index >= 0:
        details += f"\n[bold]MCS Index[/bold]   {wifi.mcs_index}"

    panel = Panel(
        details,
        title="[bold]WiFi Details[/bold]",
        border_style="magenta",
        box=box.ROUNDED
    )

    console.print(panel)
    _log_output(panel)


def show_ping_results(results: list[PingResult]):
    """Display ping test results.

    Args:
        results: List of PingResult objects
    """
    table = Table(title="Latency Tests", box=box.ROUNDED)
    table.add_column("Host", style="bold")
    table.add_column("Loss", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Avg", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Jitter", justify="right")

    for result in results:
        # Color coding for latency
        if result.avg_rtt < 20:
            avg_color = "green"
        elif result.avg_rtt < 50:
            avg_color = "cyan"
        elif result.avg_rtt < 100:
            avg_color = "yellow"
        else:
            avg_color = "red"

        # Color coding for packet loss
        if result.packet_loss == 0:
            loss_color = "green"
        elif result.packet_loss < 1:
            loss_color = "yellow"
        else:
            loss_color = "red"

        # Color coding for jitter
        jitter_color = "green" if result.jitter < 10 else "yellow" if result.jitter < 20 else "red"

        table.add_row(
            result.host,
            f"[{loss_color}]{result.packet_loss:.1f}%[/{loss_color}]",
            f"{result.min_rtt:.1f} ms",
            f"[{avg_color}]{result.avg_rtt:.1f} ms[/{avg_color}]",
            f"{result.max_rtt:.1f} ms",
            f"[{jitter_color}]{result.jitter:.1f} ms[/{jitter_color}]"
        )

    console.print(table)
    _log_output(table)


def show_speed_test_results(result: SpeedTestResult):
    """Display speed test results.

    Args:
        result: SpeedTestResult object
    """
    # Color coding for speeds
    def speed_color(mbps: float) -> str:
        if mbps > 100:
            return "green"
        elif mbps > 50:
            return "cyan"
        elif mbps > 10:
            return "yellow"
        else:
            return "red"

    # Color coding for latency
    if result.latency_ms < 20:
        lat_color = "green"
    elif result.latency_ms < 50:
        lat_color = "yellow"
    else:
        lat_color = "red"

    dl_color = speed_color(result.download_mbps)
    ul_color = speed_color(result.upload_mbps)

    details = f"""[bold]Download[/bold]    [{dl_color}]{result.download_mbps:.1f} Mbps[/{dl_color}]
[bold]Upload[/bold]      [{ul_color}]{result.upload_mbps:.1f} Mbps[/{ul_color}]
[bold]Latency[/bold]     [{lat_color}]{result.latency_ms:.1f} ms[/{lat_color}]"""

    if result.responsiveness:
        details += f"\n[bold]Response[/bold]    {result.responsiveness} RPM"

    panel = Panel(
        details,
        title="[bold]Speed Test[/bold]",
        border_style="green",
        box=box.ROUNDED
    )

    console.print(panel)
    _log_output(panel)


def show_health_status(health: HealthStatus):
    """Display health assessment.

    Args:
        health: HealthStatus object
    """
    # Status symbol and color
    if health.overall == "excellent":
        symbol = "✓"
        color = "green"
    elif health.overall == "good":
        symbol = "✓"
        color = "cyan"
    elif health.overall == "fair":
        symbol = "⚠"
        color = "yellow"
    elif health.overall == "poor":
        symbol = "⚠"
        color = "bright_yellow"
    else:
        symbol = "✗"
        color = "red"

    details = f"[bold]Overall[/bold]     [{color}]{symbol} {health.overall.upper()} (Score: {health.score}/100)[/{color}]\n"

    if health.errors:
        details += "\n[bold red]✗ Errors:[/bold red]\n"
        for error in health.errors:
            details += f"  • {error}\n"

    if health.warnings:
        details += "\n[bold yellow]⚠ Warnings:[/bold yellow]\n"
        for warning in health.warnings:
            details += f"  • {warning}\n"

    if health.recommendations:
        details += "\n[bold blue]ℹ Recommendations:[/bold blue]\n"
        for rec in health.recommendations:
            details += f"  • {rec}\n"

    if not health.errors and not health.warnings and not health.recommendations:
        details += "\n[bold green]ℹ All checks passed![/bold green]\n"
        details += "  • No issues detected\n"

    panel = Panel(
        details.rstrip(),
        title="[bold]Health Status[/bold]",
        border_style=color,
        box=box.DOUBLE
    )

    console.print(panel)
    _log_output(panel)


def show_progress(description: str):
    """Create and return a progress context manager.

    Args:
        description: Progress description

    Returns:
        Progress context manager
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
        transient=True
    )


def show_wifi_scan(networks: list[NetworkScan], limit: int = 20):
    """Display WiFi scan results.

    Args:
        networks: List of NetworkScan objects
        limit: Maximum number of networks to display
    """
    if not networks:
        console.print("[yellow]No networks found in scan[/yellow]")
        return

    table = Table(title=f"WiFi Networks (showing {min(len(networks), limit)} of {len(networks)})", box=box.ROUNDED)
    table.add_column("SSID", style="bold")
    table.add_column("BSSID", style="dim")
    table.add_column("Channel", justify="right")
    table.add_column("Signal", justify="right")
    table.add_column("Security")

    for network in networks[:limit]:
        # Signal color coding
        if network.rssi >= -50:
            signal_color = "green"
        elif network.rssi >= -60:
            signal_color = "cyan"
        elif network.rssi >= -70:
            signal_color = "yellow"
        else:
            signal_color = "red"

        table.add_row(
            network.ssid,
            network.bssid,
            str(network.channel),
            f"[{signal_color}]{network.rssi} dBm[/{signal_color}]",
            network.security
        )

    console.print(table)
    _log_output(table)


def print_info(message: str):
    """Print info message."""
    console.print(f"[blue]ℹ {message}[/blue]")
    if _logger_instance:
        _logger_instance.write_output(f"ℹ {message}")


def print_success(message: str):
    """Print success message."""
    console.print(f"[green]✓ {message}[/green]")
    if _logger_instance:
        _logger_instance.write_output(f"✓ {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[yellow]⚠ {message}[/yellow]")
    if _logger_instance:
        _logger_instance.write_output(f"⚠ {message}")


def print_error(message: str):
    """Print error message."""
    console.print(f"[red]✗ {message}[/red]")
    if _logger_instance:
        _logger_instance.write_output(f"✗ {message}")


def show_iperf3_results(result: IperfResult):
    """Display iperf3 bandwidth test results.

    Args:
        result: IperfResult object
    """
    if result.error:
        panel = Panel(
            f"[red]✗ Test failed: {result.error}[/red]",
            title=f"[bold]iperf3 — {result.server}[/bold]",
            border_style="red",
            box=box.ROUNDED
        )
        console.print(panel)
        _log_output(panel)
        return

    def speed_color(mbps: float) -> str:
        if mbps >= 900:
            return "green"
        elif mbps >= 100:
            return "cyan"
        elif mbps >= 10:
            return "yellow"
        else:
            return "red"

    dl_color = speed_color(result.download_mbps)
    ul_color = speed_color(result.upload_mbps)

    retrans_note = ""
    if result.upload_retransmits > 0 or result.download_retransmits > 0:
        retrans_note = (
            f"\n[bold]Retransmits[/bold] "
            f"↑ {result.upload_retransmits}  ↓ {result.download_retransmits}"
        )

    details = (
        f"[bold]Server[/bold]      {result.server}\n"
        f"[bold]Duration[/bold]    {result.duration_s}s per direction\n"
        f"[bold]Download[/bold]    [{dl_color}]{result.download_mbps:.1f} Mbps[/{dl_color}]\n"
        f"[bold]Upload[/bold]      [{ul_color}]{result.upload_mbps:.1f} Mbps[/{ul_color}]"
        f"{retrans_note}"
    )

    panel = Panel(
        details,
        title="[bold]iperf3 Bandwidth Test[/bold]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(panel)
    _log_output(panel)


def show_dns_reliability(dns_result: dict):
    """Display DNS reliability test results.

    Args:
        dns_result: DNS reliability test dictionary
    """
    success_rate = dns_result.get('success_rate', 0)

    # Color coding for success rate
    if success_rate >= 99:
        rate_color = "green"
        symbol = "✓"
    elif success_rate >= 95:
        rate_color = "cyan"
        symbol = "✓"
    elif success_rate >= 90:
        rate_color = "yellow"
        symbol = "⚠"
    else:
        rate_color = "red"
        symbol = "✗"

    # Color coding for average response time
    avg_time = dns_result.get('avg_response_time')
    if avg_time is not None:
        if avg_time < 20:
            time_color = "green"
        elif avg_time < 50:
            time_color = "cyan"
        elif avg_time < 100:
            time_color = "yellow"
        else:
            time_color = "red"
        avg_time_str = f"[{time_color}]{avg_time:.1f} ms[/{time_color}]"
    else:
        avg_time_str = "N/A"

    details = f"""[bold]DNS Server[/bold]     {dns_result.get('dns_server', 'Unknown')}
[bold]Total Queries[/bold]  {dns_result.get('total_queries', 0)}
[bold]Successful[/bold]     {dns_result.get('successful', 0)}
[bold]Failed[/bold]         {dns_result.get('failed', 0)}
[bold]Success Rate[/bold]   [{rate_color}]{symbol} {success_rate:.1f}%[/{rate_color}]
[bold]Avg Response[/bold]   {avg_time_str}"""

    if dns_result.get('min_response_time') is not None:
        details += f"\n[bold]Min Response[/bold]   {dns_result.get('min_response_time')} ms"
    if dns_result.get('max_response_time') is not None:
        details += f"\n[bold]Max Response[/bold]   {dns_result.get('max_response_time')} ms"

    failures = dns_result.get('failures', [])
    if failures:
        details += f"\n\n[bold yellow]Failed Domains:[/bold yellow]"
        # Show first 5 failures
        for domain in failures[:5]:
            details += f"\n  • {domain}"
        if len(failures) > 5:
            details += f"\n  ... and {len(failures) - 5} more"

    panel = Panel(
        details,
        title="[bold]DNS Reliability Test[/bold]",
        border_style=rate_color,
        box=box.ROUNDED
    )

    console.print(panel)
    _log_output(panel)
