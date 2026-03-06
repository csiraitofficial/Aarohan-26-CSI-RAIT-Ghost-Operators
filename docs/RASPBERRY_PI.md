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
sudo apt install -y python3-pip python3-venv libpcap-dev mongodb redis-server ethtool
```

## 3. Industrial-Grade Configuration
The system now enforces strict security. You **MUST** set these in your `.env` file on the Pi:

```bash
API_HOST=0.0.0.0
API_PORT=8000
INTERFACE=eth0  # Or wlan0
NIDS_ADMIN_PASSWORD=your_secure_password  # Do NOT use 'admin123'
NIDS_ADMIN_EMAIL=admin@yourdomain.net
IPS_ENABLED=true
IPS_AUTO_BLOCK=true
MONGODB_HOST=localhost
```

---

## 4. Raspberry Pi Specific Optimizations

### 🚀 Performance Tuning
1.  **Headless Mode**: Run the Pi without a monitor (CLI only) to save RAM.
2.  **Multi-Core Optimization**: Since the Orchestrator is now **Thread-Safe**, use `CAPTURE_WORKERS=4` on a Pi 4 or 5 to utilize all cores.
3.  **Failsafe "Fast-Path"**: On a Pi 3 or Zero, the system automatically activates a Fast-Path (skipping heavy ML) if the CPU is overloaded, ensuring signatures still catch critical threats.
4.  **Interface Offloading**: Disable Generic Receive Offload (GRO) to ensure Scapy sees individual packets:
    ```bash
    sudo ethtool -K eth0 gro off
    ```

### 🛡️ Promiscuous Mode
To monitor all traffic on the network segment, the interface must be in promiscuous mode:
```bash
sudo ip link set eth0 promisc on
```

---

## 5. Verification (Brutal Pi Testing)
Once the backend is running on the Pi (IP: `10.177.71.32`), run the verification script from your control machine:

```bash
chmod +x scripts/brutal_pi_tester.sh
./scripts/brutal_pi_tester.sh
```

---

> [!TIP]
> **Power Supply**: Ensure you use the official Raspberry Pi power adapter. Low voltage can cause packet drops and disk corruption during high-traffic analysis.
