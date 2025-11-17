# Raw TCP Multiplayer Game

![Gameplay screenshot](assets/game_screenshot.jpg)

A minimal **two-player 2D space shooter** built over **raw TCP**, with no external networking or concurrency libraries.
The **server is fully authoritative**—it runs the entire simulation—while clients only send input and render what the server sends.

---

## 🚀 What This Project Demonstrates

This game is an educational example of how to build a real-time multiplayer system **from scratch**, focusing on:

* Manual TCP framing
* Deterministic server-driven simulation
* Basic concurrency using only Python threads and semaphores
* A clean separation between an authoritative server and thin clients

---

## 🎮 Game Overview

Two players share a small arena and fight off waves of enemies.
The server handles all simulation; clients are lightweight Pygame front-ends.

**Gameplay features**

* Cooperative 2-player arena shooter
* 4-direction movement + shooting
* Progressive wave difficulty
* Player health, win/lose detection
* Last player standing wins

**Role of each component**

* **Server:** Runs the tick loop, updates all entities, validates input, resolves collisions, and sends state every frame.
* **Client:** Sends input each tick and renders the authoritative game state.

---

## 🏗️ Architecture Summary

### Server (Authoritative Core)

* Runs a 60 Hz deterministic tick loop.
* Accepts up to two clients (thread per client).
* Stores authoritative state:

  * Player positions/health/flags
  * Enemy list
  * Laser lists per player
  * Level/wave information
* Sends four JSON-framed messages each tick in a strict order.

### Client (Thin Renderer)

* Connects, handshakes, and identifies as player 1 or 2.
* Sends input every tick (`user_data` then `keys`).
* Receives the four server messages in order and rebuilds local state.
* Renders using Pygame; no gameplay logic is executed locally.

---

## 📡 Networking & Protocol

### Message Format

All messages are **JSON encoded in UTF-8**, framed with:

* A **64-byte ASCII header** containing the payload length (right-padded with spaces)
* Followed by the payload bytes

Example header (length = 1234):

```
b'1234                                                           '
```

This prevents issues with TCP’s stream nature (coalescing/fragmentation).

### Safe Receive Function

```python
def recvn(sock, n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    return buf
```

Always use `recvn`—plain `recv()` is unsafe for structured protocols.

### Per-Tick Message Ordering

**Server → Client (4 messages):**

1. `data` — base authoritative dictionary
2. `lasers_player1`
3. `lasers_player2`
4. `enemies`

**Client → Server (2 messages):**

1. `user_data` — connection info & ready state
2. `keys` — Pygame keyboard state array

Strict ordering ensures deterministic synchronization.

---

## 🗃️ Authoritative Data Structures

### Main Data Dictionary

```python
{
    'ready': bool,
    'level': int,
    'user1': tuple, 'user2': tuple,
    'x1': int, 'y1': int, 'health1': int, 'lost1': bool, 'win1': bool,
    'x2': int, 'y2': int, 'health2': int, 'lost2': bool, 'win2': bool
}
```

### Lasers

```python
[{'x': int, 'y': int}, ...]
```

### Enemies

```python
[{'ex': int, 'ey': int, 'ecolor': str}, ...]
```

---

## 🔀 Concurrency Model

The server uses:

* **One thread per client** for socket I/O
* **Semaphores** to protect shared state
* **Boolean flags** to guard once-only operations

Key semaphore responsibilities:

* Enemy updates / spawning
* Player slot assignment
* Laser list updates
* Match reset and global state changes

This keeps the simulation consistent while allowing I/O concurrency.

---

## 🤝 Connection Handshake

1. Client connects and sends `'hello'`.
2. Server replies with identifier `(ip, port)`.
3. Server assigns the client to `user1` or `user2`.
4. Once both are ready, per-tick communication begins.

---

## ⚙️ What the Server Does Every Tick

* Reads input from both clients
* Updates enemies, lasers, collisions, health
* Checks wave completion and spawns next wave
* Sets win/loss flags
* Sends four JSON-framed messages in order

Late or missing inputs are handled deterministically.

---

## 🎯 What the Client Does Every Tick

* Sample keyboard state
* Send `user_data` → `keys` in order
* Receive the four server messages
* Render the frame using Pygame

All gameplay behavior is server-driven.

---

## 🔌 Disconnections

If a client disconnects:

* Player slots reset
* Enemies/lasers cleared
* Level and health reset
* Flags cleared
* Thread terminates

The server immediately becomes ready for new players.

---

## 🚀 Running the Game

### Requirements

* Python 3.8+
* Pygame (`pip install pygame`)

### Start the Server

```bash
python server.py
```

### Start Two Clients

(Separate terminals or machines)

```bash
python client.py
```

### LAN Setup

* Set `SERVER` in client/server files to the server’s LAN IP.
* Ensure TCP port **5050** is reachable.

---
