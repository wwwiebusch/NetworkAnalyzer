"""Data models for network analysis."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InterfaceInfo:
    """Network interface information."""
    name: str
    hardware_port: str
    mac_address: str
    ipv4_address: Optional[str] = None
    ipv6_addresses: list[str] = field(default_factory=list)
    netmask: Optional[str] = None
    status: str = "inactive"
    media_type: str = ""
    mtu: int = 0


@dataclass
class NetworkMetrics:
    """Network interface metrics."""
    interface: str
    packets_in: int = 0
    packets_out: int = 0
    errors_in: int = 0
    errors_out: int = 0
    collisions: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    drop_rate: float = 0.0


@dataclass
class WiFiInfo:
    """WiFi connection information."""
    ssid: str
    bssid: str
    channel: int
    rssi: int
    noise: int
    snr: int
    tx_rate: int
    mcs_index: int = -1
    phy_mode: str = ""
    security: str = ""
    channel_width: int = 0

    @property
    def signal_quality(self) -> str:
        """Get signal quality category."""
        if self.rssi >= -50:
            return "excellent"
        elif self.rssi >= -60:
            return "good"
        elif self.rssi >= -70:
            return "fair"
        elif self.rssi >= -80:
            return "weak"
        else:
            return "very weak"

    @property
    def band(self) -> str:
        """Get frequency band."""
        if self.channel <= 14:
            return "2.4GHz"
        elif self.channel <= 177:
            return "5GHz"
        else:
            return "6GHz"


@dataclass
class PingResult:
    """Ping test results."""
    host: str
    packets_sent: int
    packets_received: int
    packet_loss: float
    min_rtt: float = 0.0
    avg_rtt: float = 0.0
    max_rtt: float = 0.0
    stddev_rtt: float = 0.0

    @property
    def jitter(self) -> float:
        """Calculate jitter from stddev."""
        return self.stddev_rtt


@dataclass
class HealthStatus:
    """Network health assessment."""
    overall: str
    score: int
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    @staticmethod
    def from_score(score: int) -> str:
        """Map score to status."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"


@dataclass
class SpeedTestResult:
    """Network speed test results."""
    download_mbps: float = 0.0
    upload_mbps: float = 0.0
    latency_ms: float = 0.0
    responsiveness: int = 0
    protocol: str = ""


@dataclass
class NetworkScan:
    """WiFi network scan entry."""
    ssid: str
    bssid: str
    channel: int
    rssi: int
    security: str


@dataclass
class IperfResult:
    """iperf3 bandwidth test result."""
    server: str
    upload_mbps: float = 0.0
    download_mbps: float = 0.0
    upload_retransmits: int = 0
    download_retransmits: int = 0
    duration_s: int = 10
    error: Optional[str] = None
