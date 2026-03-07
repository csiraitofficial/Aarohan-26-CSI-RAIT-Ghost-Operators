from scapy.all import sniff, IP, ICMP, TCP
from scapy.arch.windows import get_windows_if_list
import threading
import time

target_ip = "192.168.5.63"

# List of likely ingress interfaces for a local Kali VM or physical network
ifaces_to_monitor = [
    "Ethernet",
    "VMware Network Adapter VMnet1",
    "VMware Network Adapter VMnet8",
    "Wi-Fi",
    "Loopback Pseudo-Interface 1"
]

print(f"Listening for traffic arriving at {target_ip} across multiple adapters...")

def packet_callback(iface_name):
    def cb(pkt):
        if IP in pkt and pkt[IP].dst == target_ip:
            if ICMP in pkt or (TCP in pkt and pkt[TCP].dport == 80):
                print(f"[!] Traffic caught on {iface_name}: {pkt[IP].src} -> {pkt[IP].dst} | {pkt.summary()}")
    return cb

def start_sniffer(iface):
    try:
        sniff(iface=iface, prn=packet_callback(iface), store=0, filter=f"dst host {target_ip}")
    except Exception as e:
        print(f"Failed to bind on {iface}: {e}")

threads = []
for iface in ifaces_to_monitor:
    t = threading.Thread(target=start_sniffer, args=(iface,), daemon=True)
    t.start()
    threads.append(t)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping sniffer.")
