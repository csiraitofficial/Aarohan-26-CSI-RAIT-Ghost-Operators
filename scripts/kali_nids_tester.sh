#!/bin/bash
# 🐉 GHOST OPERATORS: KALI LINUX NIDS STRESS TESTER
# Use this script from a Kali Linux machine to verify NIDS detection.

# --- CONFIGURATION ---
TARGET_IP="10.177.71.232" # Your Raspberry Pi IP
SCAN_DELAY=0.1

echo "=================================================="
echo "🐉 KALI LINUX NIDS TESTER - GHOST OPERATORS"
echo "=================================================="
echo "Target NIDS Appliance: $TARGET_IP"
echo "--------------------------------------------------"

# 1. Reconnaissance Detection Test (Nmap)
echo "[*] Testing RECONNAISSANCE Detection (Nmap Stealth Scan)..."
nmap -sS -T4 -p 22,80,443,8000 $TARGET_IP > /dev/null
echo "✅ Scan complete. Check NIDS for 'Reconnaissance' alert."
sleep 2

# 2. DoS / Syn-Flood Detection Test (Hping3)
if command -v hping3 &> /dev/null; then
    echo "[*] Testing DOS Detection (SYN Flood - 5 Seconds)..."
    sudo hping3 -S -p 80 --flood --rand-source -c 1000 $TARGET_IP &> /dev/null &
    HPING_PID=$!
    sleep 5
    sudo kill $HPING_PID &> /dev/null
    echo "✅ Flood complete. Check NIDS for 'DDoS' or 'Resource Exhaustion' alerts."
else
    echo "[!] hping3 not found. Skipping SYN Flood test."
fi
sleep 2

# 3. Web Attack Detection Test (DPI / SQLi / XSS)
echo "[*] Testing WEB ATTACK Detection (DPI Engine)..."
echo "  - SQL Injection..."
curl -s "http://$TARGET_IP:8000/api/v1/search?id=1' OR '1'='1" > /dev/null
echo "  - XSS Payload..."
curl -s "http://$TARGET_IP:8000/api/v1/user?name=<script>alert('pwned')</script>" > /dev/null
echo "  - Path Traversal..."
curl -s "http://$TARGET_IP:8000/../../etc/passwd" > /dev/null
echo "✅ Web attacks sent. Check NIDS for 'Initial Access' alerts."
sleep 2

# 4. Brute Force Detection Test
echo "[*] Testing BRUTE FORCE Detection (Simulated)..."
for i in {1..10}; do
    curl -s -X POST -d '{"username":"admin","password":"wrong-password-'$i'"}' "http://$TARGET_IP:8000/api/v1/auth/login" > /dev/null
done
echo "✅ Brute force attempts sent. Check NIDS for 'Credential Access' alerts."

echo "--------------------------------------------------"
echo "🏁 ALL TESTS COMPLETE."
echo "Check your NIDS Dashboard or 'sudo python3 pi_launcher.py' logs for results."
echo "=================================================="
