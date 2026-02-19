# WWWIEBUSCH Network Analyzer

<div align="center">
  <img src="https://wwwiebusch.de/logo/full_black_new.png" alt="WWWIEBUSCH Logo" width="400">

  <p><strong>Comprehensive network analysis tool for macOS</strong></p>

  [![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![macOS](https://img.shields.io/badge/macOS-12.0%2B-black.svg)](https://www.apple.com/macos/)
  [![Rich](https://img.shields.io/badge/UI-Rich-purple.svg)](https://github.com/Textualize/rich)
  [![Made by WWWIEBUSCH](https://img.shields.io/badge/made%20by-WWWIEBUSCH-orange.svg)](https://wwwiebusch.com)

  <p>
    <a href="https://wwwiebusch.com">Website</a> •
    <a href="https://wwwiebusch.com/kontakt">Contact</a> •
    <a href="https://wwwiebusch.com/impressum">Legal Notice</a>
  </p>
</div>

---

A comprehensive network analysis tool for macOS that provides deep insights into network interfaces, performance, quality, and connectivity.

## Features

- **Comprehensive Interface Analysis**: Detailed information about all network interfaces
- **WiFi Diagnostics**: Signal strength, channel analysis, SNR, interference detection
- **Network Performance**: Speed tests, latency measurements, packet loss analysis
- **iperf3 Bandwidth Testing**: Upload and download throughput via iperf3 server
- **Health Assessment**: Automated network health scoring with recommendations
- **Dual Mode Operation**: Works both offline (no internet) and online (with internet)
- **Professional UI**: Rich terminal interface with color-coded tables and panels
- **Detailed Logging**: Structured JSON and human-readable logs with optional comment annotation

## Requirements

- macOS 12.0+ (macOS 12.1+ recommended for speed testing)
- Python 3.11 or higher

## Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Make the main script executable:
   ```bash
   chmod +x main.py
   ```

## Usage

### Interactive Mode
Simply run the tool without arguments to interactively select an interface:
```bash
python main.py
```

### Analyze Specific Interface
```bash
python main.py --interface en0
python main.py -i en0
```

### Analyze All Active Interfaces
```bash
python main.py --all
```

### Force Operating Mode
```bash
# Force offline mode (skip internet tests)
python main.py -i en0 --mode offline

# Force online mode
python main.py -i en0 --mode online
```

### Skip WiFi Scanning
```bash
python main.py -i en0 --no-wifi-scan
```

### DNS Reliability Testing
DNS reliability testing is **enabled by default** in online mode. It tests 100 highly reliable domains:
```bash
# DNS test runs automatically
python main.py -i en0

# Skip DNS test to save time
python main.py -i en0 --skip-dns-test
```

The DNS test shows:
- Success rate (percentage of successful DNS lookups across 100 domains)
- Average, minimum, and maximum response times
- List of failed domains (if any)

**Note:** This test takes 1-2 minutes as it queries 100 different domains to provide a comprehensive reliability assessment.

### iperf3 Bandwidth Test
Run a full upload and download bandwidth test against an iperf3 server:
```bash
python main.py -i en0 --iperf3 192.168.1.100
python main.py -i en0 --iperf3 192.168.1.100 --mode online
```
Requires an iperf3 server running on the target IP (default port 5201). Runs in online mode automatically. Results show upload Mbps, download Mbps, and TCP retransmits.

### Annotate Log Files with a Comment
Append a label to log filenames and embed the full comment in the log headers:
```bash
python main.py -i en0 --comment "HomeNetwork"
python main.py -i en0 --comment "test run after router reboot"
```
The first word of the comment is appended to all log filenames (e.g., `network_analysis_20260220_143022_HomeNetwork.log`). The full comment text is written into the log file header.

### Custom Log Location
```bash
python main.py -i en0 --output ~/Desktop/network_analysis.log
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `-i`, `--interface` | Specific interface to analyze (e.g., en0) |
| `-a`, `--all` | Analyze all active interfaces |
| `--mode` | Operating mode: `offline`, `online`, or `auto` (default: auto) |
| `--no-wifi-scan` | Skip WiFi network scanning (faster) |
| `--skip-dns-test` | Skip DNS reliability test (runs by default in online mode, saves 1-2 min) |
| `--iperf3 IP` | Run iperf3 upload+download bandwidth test against the specified server |
| `--comment TEXT` | Annotate logs with a comment; first word is appended to log filenames |
| `--output` | Custom log file path |
| `-v`, `--version` | Show version and exit |

## Understanding the Output

### Interface Information
- **Status**: Active/Inactive status with color coding
- **MAC Address**: Hardware (Ethernet) address
- **IP Addresses**: IPv4 and IPv6 addresses
- **MTU**: Maximum Transmission Unit size
- **Media Type**: Connection type and speed

### Network Metrics
- **Packets In/Out**: Total packets transmitted
- **Bytes In/Out**: Total data transferred (human-readable format)
- **Errors**: Network errors (color-coded: green < 0.1%, yellow < 1%, red > 1%)
- **Collisions**: Network collisions detected

### WiFi Details (if applicable)
- **Signal Strength (RSSI)**:
  - Excellent: -30 to -50 dBm (green)
  - Good: -50 to -60 dBm (cyan)
  - Fair: -60 to -70 dBm (yellow)
  - Weak: -70 to -80 dBm (orange)
  - Very Weak: < -80 dBm (red)

- **SNR (Signal-to-Noise Ratio)**:
  - Excellent: > 40 dB (green)
  - Good: 30-40 dB (yellow)
  - Poor: < 30 dB (red)

- **Channel**: WiFi channel and frequency band (2.4GHz/5GHz/6GHz)
- **TX Rate**: Current transmission rate in Mbps
- **PHY Mode**: WiFi standard (802.11ac = WiFi 5, 802.11ax = WiFi 6)
- **Security**: Authentication and encryption type

### Latency Tests
- **Packet Loss**: Percentage of lost packets (green = 0%, yellow < 1%, red > 1%)
- **Min/Avg/Max**: Minimum, average, and maximum round-trip time
- **Jitter**: Network stability indicator (green < 10ms, yellow < 20ms, red > 20ms)

### Speed Test (Online Mode)
- **Download/Upload**: Measured in Mbps
- **Latency**: Network latency under load
- **Responsiveness**: Round-trips per minute (RPM)

### iperf3 Test (Optional)
- **Upload**: Measured in Mbps (sender direction)
- **Download**: Measured in Mbps (reverse mode)
- **Retransmits**: TCP retransmit count per direction (indicator of packet loss/congestion)

### Health Status
- **Overall Score**: 0-100 scale
  - Excellent: 90-100 (green)
  - Good: 75-89 (cyan)
  - Fair: 60-74 (yellow)
  - Poor: 40-59 (orange)
  - Critical: 0-39 (red)

- **Warnings/Errors**: Specific issues detected
- **Recommendations**: Actionable suggestions to improve network performance

## WiFi Analysis Features

The tool provides comprehensive WiFi diagnostics:

1. **Signal Quality Assessment**: RSSI measurement with quality grading
2. **Interference Detection**: SNR calculation and noise floor measurement
3. **Channel Analysis**: Current channel, width, and band detection
4. **Network Scanning**: View all nearby WiFi networks with signal strength
5. **Performance Testing**: WiFi-specific speed and latency tests
6. **Standards Detection**: Identify WiFi generation (WiFi 4/5/6/6E)
7. **Stability Monitoring**: Jitter and packet loss for real-time applications

## Troubleshooting

### "Command not found: networkQuality"
This command requires macOS 12.1 or later. The tool will automatically skip speed tests on older versions.

### "Permission denied" errors
Some commands may require elevated privileges. Try running with `sudo`:
```bash
sudo python main.py -i en0
```

### "No interfaces found"
Ensure you're running on macOS and have network interfaces configured. Check with:
```bash
ifconfig -a
```

### WiFi information not showing
Verify the interface is actually a WiFi interface:
```bash
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I
```

### Speed test hangs
The networkQuality test can take 30-90 seconds. If it consistently hangs, use `--mode offline` to skip online tests.

## Log Files

Logs are saved in the `./logs/` directory with timestamped filenames:
- `network_analysis_YYYYMMDD_HHMMSS.log` - Structured debug/info log
- `network_analysis_YYYYMMDD_HHMMSS_output.txt` - Plain-text mirror of all console output
- `network_analysis_YYYYMMDD_HHMMSS.json` - Structured JSON data

When `--comment` is used, the first word of the comment is appended to all filenames:
- `network_analysis_YYYYMMDD_HHMMSS_HomeNetwork.log`
- `network_analysis_YYYYMMDD_HHMMSS_HomeNetwork_output.txt`
- `network_analysis_YYYYMMDD_HHMMSS_HomeNetwork.json`

## Common Use Cases

### Diagnose Slow WiFi
```bash
python main.py -i en0
```
Check the WiFi signal strength, SNR, and channel congestion in the scan results.

### Test Internet Speed
```bash
python main.py -i en0 --mode online
```
Includes download/upload speed test and global latency measurements.

### Quick Test Without DNS
```bash
python main.py -i en0 --skip-dns-test
```
Skips the DNS reliability test to save 1-2 minutes. By default, DNS testing is enabled and tests your configured DNS server by performing lookups on 100 highly reliable domains (major tech companies, cloud providers, news sites, etc.) to calculate success rate and average response times.

### Compare Multiple Interfaces
```bash
python main.py --all
```
Useful for comparing WiFi vs Ethernet performance.

### Quick Check Without WiFi Scan
```bash
python main.py -i en0 --no-wifi-scan
```
Faster analysis when you don't need to see nearby networks.

### Monitor Network Over Time
```bash
python main.py -i en0 --output ~/network_logs/test_$(date +%Y%m%d_%H%M%S).log
```
Run periodically to track network performance trends.

### iperf3 Bandwidth Test to Local Server
```bash
python main.py -i en0 --iperf3 192.168.1.100
```
Requires an iperf3 server running on the target: `iperf3 -s`

### Annotated Test Run
```bash
python main.py -i en0 --comment "after_firmware_update"
```
Creates log files like `network_analysis_..._after.log` with the full comment in the header.

## Finding Your Interface Name

Common interface names on macOS:
- `en0` - Usually the primary WiFi interface on MacBooks
- `en1` - Often Ethernet on MacBooks (via adapter)
- `en4`, `en5`, etc. - Additional Ethernet or Thunderbolt interfaces
- `bridge0` - Thunderbolt Bridge
- `awdl0` - Apple Wireless Direct Link (AirDrop)

To list all interfaces:
```bash
networksetup -listallhardwareports
```

Or use the tool's interactive mode to see all available interfaces.

## Technical Details

### Commands Used

**Offline Mode:**
- `networksetup -listallhardwareports` - Interface enumeration
- `ifconfig -a` - Interface details and statistics
- `netstat -i` - Network statistics
- `netstat -rn` - Routing table
- `scutil --dns` - DNS configuration
- `airport -I` - WiFi details
- `airport -s` - WiFi network scan
- `arp -a` - ARP cache
- `ping` - Latency testing

**Online Mode:**
- `networkQuality` - Native macOS speed test
- `iperf3` - Bandwidth testing (optional, requires server)
- `dig` - DNS resolution testing
- External APIs for public IP and geolocation

### Architecture

```
main.py                     # Entry point and orchestration
├── network_analyzer/
│   ├── models.py          # Data structures
│   ├── utils.py           # Utilities and health assessment
│   ├── logger.py          # Logging system
│   ├── ui.py              # Rich terminal UI
│   ├── collectors/
│   │   ├── offline.py     # Local system data collection
│   │   └── online.py      # Internet-based tests
│   └── parsers/
│       ├── ifconfig.py    # Parse ifconfig output
│       ├── netstat.py     # Parse netstat output
│       ├── airport.py     # Parse WiFi data
│       └── system_profiler.py  # Parse system data
```

## License

This project is open source and available for personal and educational use.

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- Type hints are used for function signatures
- New features include appropriate error handling
- Documentation is updated for user-facing changes

## Version History

### v1.1.0
- Added `--iperf3 IP` parameter for upload/download bandwidth testing via iperf3
- Added `--comment TEXT` parameter for log file annotation and filename labeling
- Added `_output.txt` plain-text log mirroring all console output

### v1.0.0
- Initial release
- Comprehensive interface analysis
- WiFi diagnostics and scanning
- Speed testing (macOS 12.1+)
- Health assessment with recommendations
- Dual mode operation (offline/online)
- Structured logging

---

## Contact & Support

**WWWIEBUSCH | IT- & EVENT-SOLUTIONS**

- Website: [wwwiebusch.com](https://wwwiebusch.com)
- Email: [support@wwwiebusch.com](mailto:support@wwwiebusch.com)
- Contact: [wwwiebusch.com/kontakt](https://wwwiebusch.com/kontakt)
- Legal Notice: [wwwiebusch.com/impressum](https://wwwiebusch.com/impressum)

## License

MIT License - Copyright (c) 2026 WWWIEBUSCH | IT- & EVENT-SOLUTIONS (Lauritz Wiebusch)

See [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Made by <a href="https://wwwiebusch.com">WWWIEBUSCH</a></p>
  <p><strong>WWWIEBUSCH | IT- & EVENT-SOLUTIONS</strong></p>
</div>
