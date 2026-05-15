# Distributed Proxy Network

A multithreaded Client–Proxy–Server architecture built using raw Python socket programming.  
This project implements HTTP communication over TCP, UDP-based QoS analysis, proxy caching, and concurrent connection handling without using any web frameworks or high-level networking libraries.

---

## Features

- TCP-based HTTP communication
- UDP Echo & QoS measurement
- Proxy forwarding mechanism
- Cache HIT / MISS system
- Multithreaded concurrent connections
- RTT, Jitter, Throughput, and Packet Loss analysis
- Manual socket implementation using Python
- Wireshark-compatible network traffic analysis

---

## Architecture

```text
Client  --->  Proxy Server  --->  Web Server
   |              |                  |
 TCP/UDP        TCP Proxy         TCP/UDP
```

### Components

- `client.py`
  - Sends HTTP requests through the proxy
  - Performs UDP QoS testing

- `proxy.py`
  - Handles request forwarding
  - Implements caching mechanism
  - Supports concurrent clients using multithreading

- `webserver.py`
  - Serves HTTP responses
  - Provides UDP echo service
  - Handles multiple simultaneous connections

---

## Technologies

- Python 3
- Socket Programming
- TCP / UDP Protocol
- Multithreading
- Wireshark

---

## Project Structure

```bash
distributed-proxy-network/
│
├── client.py
├── proxy.py
├── webserver.py
├── index.html
└── README.md
```

---

## How to Run

### 1. Start Web Server

```bash
python webserver.py
```

### 2. Start Proxy Server

```bash
python proxy.py
```

### 3. Run Client

#### TCP Mode

```bash
python client.py --mode tcp
```

#### UDP QoS Mode

```bash
python client.py --mode udp
```

---

## QoS Metrics

The UDP module measures:

- RTT (Min / Avg / Max)
- Packet Loss
- Jitter
- Throughput

Example output:

```text
Ping 1: RTT = 12.4 ms
Ping 2: RTT = 10.8 ms
Ping 3: Request timed out

--- Statistics ---
Min RTT: 10.8 ms
Avg RTT: 11.6 ms
Max RTT: 12.4 ms
Packet Loss: 10%
Jitter: 1.2 ms
```

---

## Cache Mechanism

### Cache MISS
- Proxy forwards request to the web server
- Response is stored locally

### Cache HIT
- Proxy serves cached response directly
- Faster response time with reduced server load

---

## Multithreading

Both the proxy server and web server use a thread-per-connection model to handle multiple simultaneous clients efficiently.

---

## Network Analysis

Wireshark can be used to inspect:

- TCP three-way handshake
- HTTP request/response flow
- UDP echo packets
- Concurrent socket connections
- Packet retransmissions

Suggested filter:

```text
tcp.port == 8000 || tcp.port == 8080 || udp.port == 9000
```

---

## Learning Objectives

This project demonstrates:

- Low-level socket programming
- TCP vs UDP communication behavior
- Proxy server architecture
- HTTP protocol implementation
- Concurrent networking systems
- Basic Quality of Service (QoS) analysis

---

## Disclaimer

This project is built for educational purposes and focuses on understanding networking fundamentals through manual socket implementation.

---
