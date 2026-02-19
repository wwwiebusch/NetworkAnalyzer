"""Online network data collection (requires internet)."""

import re
import json
import requests
from typing import Optional
from network_analyzer.utils import (
    execute_command,
    check_internet_connectivity,
    supports_network_quality
)
from network_analyzer.models import SpeedTestResult, PingResult, IperfResult
import logging

logger = logging.getLogger(__name__)


def get_public_ip() -> Optional[dict]:
    """Get public IP address and basic info.

    Returns:
        Dictionary with IP info or None
    """
    try:
        response = requests.get(
            "https://api.ipify.org?format=json",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get public IP: {e}")
        return None


def get_geolocation(ip: Optional[str] = None) -> Optional[dict]:
    """Get geolocation information for IP.

    Args:
        ip: IP address (None for current public IP)

    Returns:
        Dictionary with geolocation data or None
    """
    try:
        url = f"http://ip-api.com/json/{ip}" if ip else "http://ip-api.com/json/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country'),
                'region': data.get('regionName'),
                'city': data.get('city'),
                'isp': data.get('isp'),
                'org': data.get('org'),
                'lat': data.get('lat'),
                'lon': data.get('lon')
            }
    except Exception as e:
        logger.error(f"Failed to get geolocation: {e}")

    return None


def run_speed_test(interface: str) -> Optional[SpeedTestResult]:
    """Run networkQuality speed test (macOS 12.1+).

    Args:
        interface: Interface name to test

    Returns:
        SpeedTestResult object or None
    """
    if not supports_network_quality():
        logger.warning("networkQuality not available (requires macOS 12.1+)")
        return None

    try:
        # Run networkQuality with configuration
        stdout, stderr, code = execute_command(
            ["networkQuality", "-I", interface, "-v"],
            timeout=90
        )

        if code != 0:
            logger.error(f"networkQuality failed: {stderr}")
            return None

        # Parse output - look for summary lines
        result = SpeedTestResult()

        # Download capacity (Downlink)
        dl_match = re.search(r'Downlink capacity:\s*([\d.]+)\s*Mbps', stdout)
        if dl_match:
            result.download_mbps = float(dl_match.group(1))

        # Upload capacity (Uplink)
        ul_match = re.search(r'Uplink capacity:\s*([\d.]+)\s*Mbps', stdout)
        if ul_match:
            result.upload_mbps = float(ul_match.group(1))

        # Responsiveness (may have "Low" or "High" label, extract the RPM number)
        resp_match = re.search(r'Responsiveness:.*?(\d+)\s*RPM', stdout, re.DOTALL)
        if resp_match:
            result.responsiveness = int(resp_match.group(1))

        # Idle latency (extract milliseconds from RPM line)
        lat_match = re.search(r'Idle Latency:.*?(\d+)\s*RPM\s*\(([\d.]+)\s*milliseconds\)', stdout, re.DOTALL)
        if lat_match:
            result.latency_ms = float(lat_match.group(2))

        return result

    except Exception as e:
        logger.error(f"Failed to run speed test: {e}")
        return None


def run_global_ping_tests() -> list[PingResult]:
    """Run ping tests to multiple global hosts.

    Returns:
        List of PingResult objects
    """
    from network_analyzer.collectors.offline import run_ping_test

    hosts = [
        ("8.8.8.8", "Google DNS"),
        ("1.1.1.1", "Cloudflare DNS"),
        ("9.9.9.9", "Quad9 DNS")
    ]

    results = []
    for ip, name in hosts:
        logger.info(f"Pinging {name} ({ip})...")
        result = run_ping_test(ip, count=10)
        if result:
            results.append(result)

    return results


def test_dns_resolution(domains: Optional[list[str]] = None) -> dict:
    """Test DNS resolution performance.

    Args:
        domains: List of domains to test (None for defaults)

    Returns:
        Dictionary with resolution times
    """
    if domains is None:
        domains = ["google.com", "cloudflare.com", "github.com"]

    results = {}

    for domain in domains:
        try:
            stdout, _, code = execute_command(
                ["dig", "+stats", domain],
                timeout=10
            )

            if code == 0:
                # Parse query time
                match = re.search(r'Query time:\s*(\d+)\s*msec', stdout)
                if match:
                    results[domain] = int(match.group(1))
                else:
                    results[domain] = None
        except Exception as e:
            logger.error(f"Failed to resolve {domain}: {e}")
            results[domain] = None

    return results


def test_dns_reliability(dns_server: Optional[str] = None, num_domains: int = 100) -> dict:
    """Test DNS server reliability with multiple domain lookups.

    Args:
        dns_server: Specific DNS server to test (None for system default)
        num_domains: Number of test domains (default: 100)

    Returns:
        Dictionary with reliability metrics
    """
    # 150+ highly reliable domains for comprehensive testing
    test_domains = [
        # Major tech companies
        "google.com", "facebook.com", "youtube.com", "amazon.com", "microsoft.com",
        "apple.com", "netflix.com", "twitter.com", "instagram.com", "linkedin.com",
        "adobe.com", "oracle.com", "salesforce.com", "zoom.us", "cisco.com",
        "intel.com", "nvidia.com", "amd.com", "ibm.com", "dell.com",
        "hp.com", "samsung.com", "sony.com", "toshiba.com", "lenovo.com",

        # Cloud providers & CDNs
        "cloudflare.com", "aws.amazon.com", "azure.microsoft.com", "cloud.google.com",
        "digitalocean.com", "heroku.com", "netlify.com", "vercel.com", "fastly.com",
        "akamai.com",

        # Social media & communication
        "whatsapp.com", "telegram.org", "discord.com", "slack.com", "teams.microsoft.com",
        "snapchat.com", "tiktok.com", "pinterest.com", "tumblr.com", "mastodon.social",

        # Development & tech
        "github.com", "gitlab.com", "bitbucket.org", "stackoverflow.com", "npmjs.com",
        "pypi.org", "docker.com", "kubernetes.io", "apache.org", "mozilla.org",
        "w3.org", "ietf.org", "jquery.com", "nodejs.org", "python.org",

        # E-commerce
        "ebay.com", "walmart.com", "target.com", "bestbuy.com", "shopify.com",
        "etsy.com", "aliexpress.com", "alibaba.com", "rakuten.com", "wayfair.com",

        # News & media
        "cnn.com", "bbc.com", "nytimes.com", "reuters.com", "bloomberg.com",
        "wsj.com", "theguardian.com", "forbes.com", "techcrunch.com", "wired.com",
        "theverge.com", "arstechnica.com", "engadget.com", "mashable.com",

        # Entertainment & streaming
        "spotify.com", "soundcloud.com", "twitch.tv", "vimeo.com", "dailymotion.com",
        "hulu.com", "disneyplus.com", "hbomax.com", "primevideo.com", "crunchyroll.com",

        # Productivity & services
        "dropbox.com", "box.com", "onedrive.live.com", "notion.so", "trello.com",
        "asana.com", "monday.com", "atlassian.com", "evernote.com", "grammarly.com",

        # Finance & banking
        "paypal.com", "stripe.com", "square.com", "coinbase.com", "visa.com",
        "mastercard.com", "americanexpress.com", "bankofamerica.com", "chase.com",

        # Education & reference
        "wikipedia.org", "wikimedia.org", "khanacademy.org", "coursera.org",
        "udemy.com", "edx.org", "mit.edu", "stanford.edu", "harvard.edu",
        "archive.org", "dictionary.com", "imdb.com",

        # Search & browsers
        "bing.com", "yahoo.com", "duckduckgo.com", "yandex.com", "baidu.com",
        "brave.com", "opera.com", "vivaldi.com",

        # Content & blogging
        "medium.com", "wordpress.com", "blogger.com", "substack.com", "ghost.org",

        # Gaming
        "steampowered.com", "epicgames.com", "ea.com", "blizzard.com", "roblox.com",
        "minecraft.net", "playstation.com", "xbox.com", "nintendo.com",

        # Travel & maps
        "google.com", "maps.google.com", "booking.com", "airbnb.com", "expedia.com",
        "tripadvisor.com", "uber.com", "lyft.com",

        # Government & organizations
        "usa.gov", "whitehouse.gov", "nasa.gov", "who.int", "un.org",
        "europa.eu", "gov.uk", "canada.ca",

        # Security & privacy
        "protonmail.com", "signal.org", "lastpass.com", "1password.com", "bitwarden.com"
    ]

    # Limit to requested number
    test_domains = test_domains[:num_domains]

    successful = 0
    failed = 0
    response_times = []
    failures = []

    for domain in test_domains:
        try:
            cmd = ["dig", "+time=3", "+tries=1"]

            # Use specific DNS server if provided
            if dns_server:
                cmd.append(f"@{dns_server}")

            cmd.append(domain)

            stdout, stderr, code = execute_command(cmd, timeout=5)

            if code == 0 and "ANSWER SECTION" in stdout:
                successful += 1

                # Parse query time
                match = re.search(r'Query time:\s*(\d+)\s*msec', stdout)
                if match:
                    response_times.append(int(match.group(1)))
            else:
                failed += 1
                failures.append(domain)

        except Exception as e:
            failed += 1
            failures.append(domain)
            logger.debug(f"DNS lookup failed for {domain}: {e}")

    total = successful + failed
    success_rate = (successful / total * 100) if total > 0 else 0

    result = {
        'total_queries': total,
        'successful': successful,
        'failed': failed,
        'success_rate': success_rate,
        'failures': failures,
        'dns_server': dns_server or 'system default'
    }

    if response_times:
        result['avg_response_time'] = sum(response_times) / len(response_times)
        result['min_response_time'] = min(response_times)
        result['max_response_time'] = max(response_times)
    else:
        result['avg_response_time'] = None
        result['min_response_time'] = None
        result['max_response_time'] = None

    return result


def run_iperf3_test(server: str, duration: int = 10, port: int = 5201) -> IperfResult:
    """Run iperf3 bandwidth test to a server.

    Runs both upload and download (reverse) tests.

    Args:
        server: iperf3 server IP or hostname
        duration: Test duration in seconds per direction
        port: iperf3 server port (default 5201)

    Returns:
        IperfResult with upload and download measurements
    """
    result = IperfResult(server=server, duration_s=duration)

    def parse_mbps(stdout: str) -> tuple[float, int]:
        """Return (Mbps, retransmits) from iperf3 JSON output."""
        try:
            data = json.loads(stdout)
            end = data.get('end', {})
            # sender summary for upload, receiver summary for download (reverse)
            sent = end.get('sum_sent', end.get('sum', {}))
            mbps = sent.get('bits_per_second', 0) / 1_000_000
            retrans = sent.get('retransmits', 0)
            return round(mbps, 2), retrans
        except Exception:
            # Fallback: parse plain text
            match = re.search(r'([\d.]+)\s+Mbits/sec.*?(sender|receiver)', stdout)
            if match:
                return float(match.group(1)), 0
            return 0.0, 0

    # Upload test
    try:
        stdout, stderr, code = execute_command(
            ["iperf3", "-c", server, "-p", str(port), "-t", str(duration), "-J"],
            timeout=duration + 30
        )
        if code == 0:
            result.upload_mbps, result.upload_retransmits = parse_mbps(stdout)
        else:
            error_msg = stderr.strip() or "Upload test failed"
            logger.error(f"iperf3 upload failed: {error_msg}")
            result.error = error_msg
            return result
    except Exception as e:
        logger.error(f"iperf3 upload error: {e}")
        result.error = str(e)
        return result

    # Download test (reverse mode)
    try:
        stdout, stderr, code = execute_command(
            ["iperf3", "-c", server, "-p", str(port), "-t", str(duration), "-R", "-J"],
            timeout=duration + 30
        )
        if code == 0:
            result.download_mbps, result.download_retransmits = parse_mbps(stdout)
        else:
            logger.error(f"iperf3 download failed: {stderr.strip()}")
    except Exception as e:
        logger.error(f"iperf3 download error: {e}")

    return result


def check_connectivity() -> dict:
    """Comprehensive internet connectivity check.

    Returns:
        Dictionary with connectivity status
    """
    return {
        'internet_available': check_internet_connectivity(),
        'dns_working': test_dns_working(),
        'http_working': test_http_working()
    }


def test_dns_working() -> bool:
    """Test if DNS resolution works.

    Returns:
        True if DNS working, False otherwise
    """
    try:
        stdout, _, code = execute_command(
            ["dig", "+short", "google.com"],
            timeout=5
        )
        return code == 0 and bool(stdout.strip())
    except Exception:
        return False


def test_http_working() -> bool:
    """Test if HTTP requests work.

    Returns:
        True if HTTP working, False otherwise
    """
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def check_reachability(host: str) -> bool:
    """Check if a host is reachable using scutil.

    Args:
        host: Hostname or IP

    Returns:
        True if reachable, False otherwise
    """
    try:
        stdout, _, code = execute_command(
            ["scutil", "-r", host],
            timeout=5
        )
        return code == 0 and "Reachable" in stdout
    except Exception:
        return False
