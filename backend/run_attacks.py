import asyncio
import aiohttp
import time
import random
from datetime import datetime

TARGET_URL = "http://localhost:8000"

# Attack Payloads designed to trigger specific NIDS Signature Rules
ATTACK_VECTORS = {
    "sql_injection": [
        "/?id=1' OR '1'='1",
        "/?search=admin'--",
        "/?user=1; DROP TABLE users",
        "/?q=1 UNION ALL SELECT NULL,NULL,NULL"
    ],
    "xss": [
        "/?q=<script>alert(1)</script>",
        "/?name=<img src=x onerror=alert('XSS')>",
        "/?onload=javascript:eval('malicious')"
    ],
    "directory_traversal": [
        "/?file=../../../etc/passwd",
        "/?path=..\\..\\windows\\system32\\cmd.exe",
        "/?doc=../../../../var/log/messages"
    ],
    "command_injection": [
        "/?cmd=1; cat /etc/passwd",
        "/?ping=127.0.0.1 | whoami",
        "/?exec=ls -la"
    ]
}

async def send_attack(session, category, payload):
    url = f"{TARGET_URL}{payload}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NIDS-Test-Simulator",
        "X-Forwarded-For": f"192.168.1.{random.randint(100, 250)}" # Spoof IPs for testing
    }
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🗡️  Sending {category.upper()} payload: {url}")
        async with session.get(url, headers=headers, timeout=2) as response:
            await response.text()
            return True
    except Exception as e:
        # We expect connection errors if the NIDS blocks us!
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛡️  Blocked or Connection failed (Good!): {e}")
        return False

async def simulate_flood(session):
    print("\n--- 🌊 INITIATING HTTP FLOOD (Denial of Service) ---")
    tasks = []
    # Send 100 requests as fast as possible to trigger rate limiting / flood rules
    for _ in range(100):
        tasks.append(send_attack(session, "http_flood", "/?q=flood_test"))
    await asyncio.gather(*tasks)
    print("--- 🏁 FLOOD COMPLETE ---\n")

async def run_simulation():
    print("==================================================")
    print("🛡️  Ghost Operators NIDS - Live Attack Simulator")
    print(f"🎯 Target: {TARGET_URL}")
    print("==================================================\n")
    
    async with aiohttp.ClientSession() as session:
        # 1. Test Single Attacks (Signatures)
        for category, payloads in ATTACK_VECTORS.items():
            print(f"\n--- 🧪 Testing Category: {category.upper()} ---")
            for payload in payloads:
                await send_attack(session, category, payload)
                await asyncio.sleep(0.5) # Slight delay between tests
        
        # 2. Test Flood (Behavioral / State)
        await asyncio.sleep(2)
        await simulate_flood(session)

    print("\n✅ Simulation completed. Check the NIDS terminal and 'check_all_alerts.py'!")

if __name__ == "__main__":
    asyncio.run(run_simulation())
