# 🍓 Raspberry Pi Deployment Guide — NIDS Appliance

Running the Advanced NIDS on a Raspberry Pi transforms it into a dedicated **Hardware Security Appliance**.

## 1. Hardware Requirements
- **Recommended**: Raspberry Pi 4 Model B (4GB/8GB) or Raspberry Pi 5.
- **MicroSD**: Class 10, 32GB+ (high endurance recommended).
- **Cooling**: Active cooling (fan) is essential as NIDS/ML processing is CPU-intensive.
- **Network**: Gigabit Ethernet is preferred. For inline IPS, you may need a second USB 3.0 Gigabit Ethernet adapter.

## 2. Software Preparation
The system runs best on **Raspberry Pi OS (64-bit)** or **Ubuntu Server (64-bit)**.

### Install Dependencies
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv libpcap-dev mongodb redis-server
```

## 3. Deployment Methods

### Method A: Docker (Easiest)
Since we have a `docker-compose.yml`, it's the most portable way.
1. **Install Docker**: `curl -sSL https://get.docker.com | sh`
2. **Build and Run**:
   ```bash
   docker-compose up -d --build
   ```
   *Note: Our Dockerfile uses Python 3.11, which is compatible with ARM64 architecture.*

### Method B: Manual Setup
1. **Clone the project**:
   ```bash
   git clone <repo-url>
   cd Aarohan-26-CSI-RAIT-Ghost-Operators/backend
   ```
2. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Edit `.env` and set `INTERFACE=eth0` (or `wlan0`).

## 4. Raspberry Pi Specific Optimizations

### 🚀 Performance Tuning
1. **Headless Mode**: Run the Pi without a monitor (CLI only) to save RAM.
2. **Core Isolation**: The Orchestrator uses `CaptureWorkers`. On a Pi 4/5, set `CAPTURE_WORKERS=2` to leave cores available for the ML Engine.
3. **Interface Offloading**: Disable Generic Receive Offload (GRO) to ensure Scapy sees individual packets:
   ```bash
   sudo ethtool -K eth0 gro off
   ```

### 🛡️ Promiscuous Mode
To monitor all traffic on the network segment, the interface must be in promiscuous mode:
```bash
sudo ip link set eth0 promisc on
```

### ⚡ Hardware-Specific Detection
- **MLEngine**: On Pi, it is recommended to use the `isolation_forest` or `random_forest` models. Deep Learning models (CNN/LSTM) may be slow unless using a **Coral Edge TPU** or optimizing with **OpenVINO**.

## 5. Inline IPS Mode (Bridge)
To use the Pi as a firewall (IPS), you need two network interfaces:
1. Create a bridge `br0` between `eth0` and `eth1`.
2. Traffic flows through the Pi, and the `IPSManager` can drop malicious packets instantly.

---

> [!TIP]
> **Power Supply**: Ensure you use the official Raspberry Pi power adapter. Low voltage can cause packet drops and disk corruption during high-traffic analysis.
