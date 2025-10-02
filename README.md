# Hackathon Project – Network Speed Test (Intro to Computer Networks 2024)

This repository contains my solution for the **Intro to Computer Networks 2024 Hackathon – Speed Test Assignment**.  
The goal of the project was to build a **client-server application** in Python that measures and compares network throughput over **TCP and UDP**, with compatibility across all teams’ implementations .

---

## Overview
- Implemented a **multi-threaded server** that:
  - Listens for clients.
  - Broadcasts UDP “offer” packets once per second.
  - Spawns a new thread to handle each incoming test (TCP or UDP).  

- Implemented a **multi-threaded client** that:
  - Listens for server “offer” packets via UDP broadcast.
  - Connects to the server using both TCP and UDP in parallel.
  - Requests file transfers of configurable size.
  - Measures throughput and packet loss.
  - Displays colorful, user-friendly results.

---

## Packet Formats
- **Offer (server → client)**: includes magic cookie, type, server UDP/TCP ports.  
- **Request (client → server)**: includes magic cookie, type, requested file size.  
- **Payload (server → client)**: includes magic cookie, type, segment info, payload.  

---

## Features
- **User Input** – client asks for file size, number of TCP connections, and number of UDP connections.  
- **Concurrent Transfers** – runs multiple TCP and UDP downloads in parallel using threads.  
- **Performance Metrics** – client measures:
  - Transfer time  
  - Effective speed  
  - UDP packet success rate (%)  
- **Cross-team Compatibility** – follows assignment spec so all clients/servers interoperate.  
- **Error Handling** – timeouts, invalid messages, and cleanup handled gracefully.  
- **ANSI Colors** – colorful terminal output for readability.  

---

## Example Run
Client started, listening for offer requests...
Received offer from 172.1.0.4
Connected to server on TCP port 5000, UDP port 6000
TCP transfer #1 finished, total time: 3.55s, total speed: 5.4 MB/s
UDP transfer #2 finished, total time: 3.55s, total speed: 5.1 MB/s, packet success: 95%
All transfers complete, listening for offer requests...

---

## Skills Gained
- Network programming with Python sockets.
- Designing multi-threaded server/client architectures.
- Implementing and parsing custom packet formats (UDP/TCP).
- Measuring throughput and packet loss in real-world conditions.
- Error handling in unreliable network environments.
- Collaborative software engineering in a hackathon setting.

---

## ▶️ How to Run
```bash

Start the server:
python3 server.py

Start the client:
python3 client.py
