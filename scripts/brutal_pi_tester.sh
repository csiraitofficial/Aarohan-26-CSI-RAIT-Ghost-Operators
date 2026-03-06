#!/bin/bash
# 🌋 BRUTAL-PI-TESTER: {O.S.I.R.I.S} NIDS Verification Script
# This script simulates the "Grey Hat" attacks we just patched.

# IP of the Raspberry Pi NIDS
TARGET_IP="10.177.71.232" 

echo "🔥 STARTING BRUTAL VERIFICATION ON PI..."

# 1. Test Fragmented Stream Bypass (DPI Reassembly)
echo "[1/3] Testing Fragmented SQLi Bypass Defense..."
# Send 'UNI' then 'ON SELECT' separately.
# Without reassembly, this bypasses basic regex.
echo -n "UNI" | nc -w 1 $TARGET_IP 80
echo -n "ON SELECT" | nc -w 1 $TARGET_IP 80
echo ">> Check logs for 'DPI match [REASSEMBLED_STREAM]'"

# 2. Test Metamorphic Sled Detection
echo "[2/3] Testing Metamorphic Sled Detection..."
# Sending a sequence of repeated INC EAX instructions (404040...)
# A basic NIDS only looks for 909090.
python3 -c "print('\x40'*32)" | nc -w 1 $TARGET_IP 80
echo ">> Check logs for 'Metamorphic Sled Detected'"

# 3. Test Concurrency Load (Thread-Safety)
echo "[3/3] Testing Concurrency Stress (Fast-Path)..."
for i in {1..20}; do
  (echo "GET /admin/config.php HTTP/1.1" | nc -w 1 $TARGET_IP 80 &)
done
echo ">> Check logs for 'Correlation: 5+ alerts' and 'IPS Blocked'"

echo "✅ TEST SEQUENCE COMPLETE. REVIEW LOGS ON PI."
