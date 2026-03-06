"""
Flow Aggregator — aggregates raw packets into bidirectional network flows.

This is a completely NEW module (not in the original NIDS). It enables:
  - NetFlow/IPFIX-style flow records
  - Flow-level feature extraction for ML models
  - Inter-arrival time, duration, packet count, byte stats
"""

import threading
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Deque
from collections import deque
import logging
import statistics

from app.models.schemas import PacketInfo, NetworkFlow

logger = logging.getLogger(__name__)


class FlowAggregator:
    """
    Aggregates raw PacketInfo objects into bidirectional NetworkFlow records.
    
    A flow is identified by the 5-tuple:
        (src_ip, dst_ip, src_port, dst_port, protocol)
    
    Bidirectional: A→B and B→A are the same flow.
    """

    def __init__(self, flow_timeout: float = 120.0, max_flows: int = 100_000):
        self.flow_timeout = flow_timeout  # seconds
        self.max_flows = max_flows

        self._active_flows: Dict[str, _FlowState] = {}
        self._completed_flows: Deque[NetworkFlow] = deque(maxlen=50_000)
        self._lock = threading.Lock()

        self.total_flows_completed = 0
        self.total_packets_processed = 0

    def process_packet(self, packet: PacketInfo):
        """Add a packet to its corresponding flow."""
        flow_key = self._compute_flow_key(packet)
        self.total_packets_processed += 1

        with self._lock:
            if flow_key not in self._active_flows:
                if len(self._active_flows) >= self.max_flows:
                    self._evict_oldest_flow()
                self._active_flows[flow_key] = _FlowState(flow_key, packet)
            else:
                self._active_flows[flow_key].add_packet(packet)

    def flush_expired(self) -> List[NetworkFlow]:
        """Flush flows that have been idle longer than flow_timeout."""
        now = time.time()
        expired_keys = []
        completed = []

        with self._lock:
            for key, state in self._active_flows.items():
                if now - state.last_packet_time > self.flow_timeout:
                    expired_keys.append(key)

            for key in expired_keys:
                state = self._active_flows.pop(key)
                flow = state.to_network_flow()
                self._completed_flows.append(flow)
                completed.append(flow)
                self.total_flows_completed += 1

        return completed

    def get_active_flow_count(self) -> int:
        return len(self._active_flows)

    def get_recent_flows(self, limit: int = 100) -> List[NetworkFlow]:
        with self._lock:
            return list(self._completed_flows)[-limit:]

    def get_stats(self) -> Dict:
        return {
            "active_flows": len(self._active_flows),
            "completed_flows": self.total_flows_completed,
            "total_packets_processed": self.total_packets_processed,
            "flow_timeout_seconds": self.flow_timeout,
        }

    # ----------------------------------------------------------------
    # Internal
    # ----------------------------------------------------------------

    @staticmethod
    def _compute_flow_key(packet: PacketInfo) -> str:
        """Compute a canonical bidirectional flow key."""
        endpoints = sorted([
            (packet.source_ip, packet.source_port or 0),
            (packet.dest_ip, packet.dest_port or 0),
        ])
        raw = f"{endpoints[0][0]}:{endpoints[0][1]}-{endpoints[1][0]}:{endpoints[1][1]}-{packet.protocol}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _evict_oldest_flow(self):
        """Remove the flow with the oldest last_packet_time."""
        if not self._active_flows:
            return
        oldest_key = min(self._active_flows, key=lambda k: self._active_flows[k].last_packet_time)
        state = self._active_flows.pop(oldest_key)
        flow = state.to_network_flow()
        self._completed_flows.append(flow)
        self.total_flows_completed += 1


class _FlowState:
    """Internal mutable state for a flow being built."""

    def __init__(self, flow_id: str, first_packet: PacketInfo):
        self.flow_id = flow_id
        self.source_ip = first_packet.source_ip
        self.dest_ip = first_packet.dest_ip
        self.source_port = first_packet.source_port
        self.dest_port = first_packet.dest_port
        self.protocol = first_packet.protocol

        self.start_time = first_packet.timestamp
        self.end_time = first_packet.timestamp
        self.last_packet_time = time.time()

        # Counters
        self.total_packets = 1
        self.total_bytes = first_packet.packet_length
        self.forward_packets = 1
        self.backward_packets = 0
        self.forward_bytes = first_packet.packet_length
        self.backward_bytes = 0

        # Timing
        self._arrival_times: List[float] = [time.time()]
        self._packet_lengths: List[int] = [first_packet.packet_length]

        # TCP flags
        self.syn_count = 0
        self.fin_count = 0
        self.rst_count = 0
        self.psh_count = 0
        self.ack_count = 0
        self.urg_count = 0
        self._count_flags(first_packet)

    def add_packet(self, packet: PacketInfo):
        now = time.time()
        self.total_packets += 1
        self.total_bytes += packet.packet_length
        self.end_time = packet.timestamp
        self.last_packet_time = now

        self._arrival_times.append(now)
        self._packet_lengths.append(packet.packet_length)

        # Determine direction
        if packet.source_ip == self.source_ip:
            self.forward_packets += 1
            self.forward_bytes += packet.packet_length
        else:
            self.backward_packets += 1
            self.backward_bytes += packet.packet_length

        self._count_flags(packet)

    def _count_flags(self, packet: PacketInfo):
        if not packet.tcp_flags:
            return
        flags = packet.tcp_flags.upper().split(",")
        for f in flags:
            f = f.strip()
            if f == "SYN":
                self.syn_count += 1
            elif f == "FIN":
                self.fin_count += 1
            elif f == "RST":
                self.rst_count += 1
            elif f == "PSH":
                self.psh_count += 1
            elif f == "ACK":
                self.ack_count += 1
            elif f == "URG":
                self.urg_count += 1

    def to_network_flow(self) -> NetworkFlow:
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time != self.start_time else 0.0

        # Inter-arrival times
        iats = []
        for i in range(1, len(self._arrival_times)):
            iats.append(self._arrival_times[i] - self._arrival_times[i - 1])

        mean_iat = statistics.mean(iats) if iats else 0.0
        std_iat = statistics.stdev(iats) if len(iats) >= 2 else 0.0

        return NetworkFlow(
            flow_id=self.flow_id,
            start_time=self.start_time,
            end_time=self.end_time,
            source_ip=self.source_ip,
            dest_ip=self.dest_ip,
            source_port=self.source_port,
            dest_port=self.dest_port,
            protocol=self.protocol,
            total_packets=self.total_packets,
            total_bytes=self.total_bytes,
            forward_packets=self.forward_packets,
            backward_packets=self.backward_packets,
            forward_bytes=self.forward_bytes,
            backward_bytes=self.backward_bytes,
            duration_seconds=round(duration, 4),
            mean_inter_arrival_time=round(mean_iat, 6),
            std_inter_arrival_time=round(std_iat, 6),
            min_packet_length=min(self._packet_lengths) if self._packet_lengths else 0,
            max_packet_length=max(self._packet_lengths) if self._packet_lengths else 0,
            mean_packet_length=round(statistics.mean(self._packet_lengths), 2) if self._packet_lengths else 0.0,
            syn_count=self.syn_count,
            fin_count=self.fin_count,
            rst_count=self.rst_count,
            psh_count=self.psh_count,
            ack_count=self.ack_count,
            urg_count=self.urg_count,
        )
