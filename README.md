# Raw TCP Multiplayer Game

![Gameplay screenshot](assets/game_screenshot.jpg)

**What it is:** A simple two-player 2D space shooter where the server runs all game logic and clients only send input and render the state.

## Core Technical Challenge

This project demonstrates a real-time multiplayer game built **without any networking or concurrency libraries**. The server is fully authoritative, computing all simulation—movement, collisions, enemy waves, and health—while clients only relay input and render frames.  

The goal is to show how a fully functional multiplayer system can be implemented **from first principles**, focusing on networking, synchronization, and deterministic server-driven simulation.

## 🎮 Game Overview & Features

Space Shooter Multiplayer is a **two-player 2D cooperative action game** and an educational, low-level example of networking and multiprocessing. Two clients connect to a Python server over raw TCP; the **server is authoritative** and executes 100% of the simulation (player/enemy movement, collisions, scoring, level progression). Clients are thin Pygame renderers that only send input and draw the server-provided state.

**Core gameplay**
- Two players share a single arena; last player standing wins.
- Real-time controls: four-direction movement + shoot.
- Progressive difficulty: waves scale linearly in size/pressure.
- Health system and explicit win/lose conditions.
- Wave-based progression: destroy all enemies to advance.


## 🏗️ Architecture Overview (Server & Client)

### Server — Computational Core
- Single authoritative process that runs the deterministic tick loop (60 ticks/second).
- Accepts up to two clients; spawns `handle_client(conn, addr)` thread for each connection.
- Maintains authoritative state in shared structures:
  - `data` dictionary (positions, health, level, flags)
  - `enemies`, `lasers_data`, `lasers_data2` lists
- Sends framed JSON messages to each client every tick in a strict, ordered sequence.

### Clients — Thin Graphical Renderers
- Connect to server and perform initial handshake.
- Send input each tick: `user_data` and `keys`.
- Receive four framed messages per tick and rebuild local state.
- Render via Pygame at 60 FPS using authoritative data; **no local game logic** beyond input sampling.

---

## 📡 Networking & Protocol

This section explains how the game achieves deterministic, reliable communication over raw TCP, including message encoding, framing, and per-tick ordering.

### Message Framing

* All messages are **JSON objects encoded in UTF-8**.
* Each message is preceded by a **64-byte ASCII header** containing the payload length as a decimal string, **right-padded with spaces**.

  * Example header: `b'1234                                                           '`
* **Wire format:** `header (64 bytes ASCII)` + `payload (length bytes)`
* **Why:** TCP is a continuous byte stream. Explicit framing ensures the receiver can detect message boundaries and prevents coalescing or fragmentation issues.

### Receiver Implementation

A helper function ensures exactly `n` bytes are read from the socket:

```python
def recvn(sock, n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    return buf

# Example usage
hdr = recvn(sock, 64)
length = int(hdr.decode('ascii').strip())
payload = recvn(sock, length)
obj = json.loads(payload.decode('utf-8'))
```

**Important:** Always use `recvn`. Using `recv` directly without exact-length handling may break framing under normal TCP behavior.

### Per-Tick Message Ordering

Message order is **strictly enforced** to maintain authoritative state synchronization.

**Server → Client (4 messages per tick, exact order):**

1. `data` — authoritative dictionary of players, health, level, flags, and identities
2. `lasers_player1` — JSON array of player 1’s laser positions
3. `lasers_player2` — JSON array of player 2’s laser positions
4. `enemies` — JSON array of enemy positions and colors

**Client → Server (2 messages per tick, exact order):**

1. `user_data` — JSON object: `{ "connection": ..., "ready": ... }`
2. `keys` — serialized boolean array from `pygame.key.get_pressed()`


---

## 🗃️ Data Structures (authoritative representations)

### Authoritative Data Dictionary (Server → Client)

```python
{
    'ready': bool,
    'level': int,
    'user1': tuple, 'user2': tuple,  # (ip, port) or '0.0.0.0' placeholders
    'x1': int, 'y1': int, 'health1': int, 'lost1': bool, 'win1': bool,
    'x2': int, 'y2': int, 'health2': int, 'lost2': bool, 'win2': bool
}
```

### Laser List (per player)

```python
[{'x': <int>, 'y': <int>}, ...]
```

### Enemy List

```python
[{'ex': <int>, 'ey': <int>, 'ecolor': <string>}, ...]
```

---


## 🔀 Multiprocessing & Concurrency

The server uses **multithreading** (thread-per-connection) with **semaphore** protection for shared state. Threads provide straightforward I/O concurrency while semaphores enforce deterministic access to critical regions.

### Concurrency Model

* **Thread per client**: each client has a dedicated thread for blocking socket I/O and coordination with the authoritative tick loop.
* **Shared structures**: `data`, `enemies`, `lasers_data`, `lasers_data2`.
* **Synchronization primitives**: multiple semaphores (`semaphore2`, `semaphore4`, `semaphore5`, `semaphore6`, `semaphore8`, `semaphore10`) protect specific resources:

  * `semaphore2` — enemy spawning & movement updates
  * `semaphore4` — user connection/slot assignment
  * `semaphore5` / `semaphore6` — player-specific laser lists
  * `semaphore8` — match/global state reset
  * `semaphore10` — enemy list mutations
* **Boolean flags**: ensure single-execution operations and prevent repeated initialization under contention.

---

## 🤝 Connection Handshake

1. Client connects to server socket.
2. Client sends initial `'hello'` framed message.
3. Server responds with client's assigned identifier `(ip, port)`.
4. Server assigns client to `user1` or `user2` slot; if full, it responds accordingly.
5. Per-tick communication begins; server tick is authoritative.

---

## ⚙️ Per-Tick Server Actions

* Receive inputs from both clients (blocking or timed reads).
* Update enemies and spawn logic (`semaphore2` / `semaphore10`).
* Advance lasers; remove off-screen lasers (`semaphore5` / `semaphore6`).
* Collision detection: lasers vs enemies, enemies vs players.
* Update player health, set `win`/`lost` flags.
* Progress level when conditions met; spawn new wave.
* Send outgoing framed messages in exact order.

**Note:** Inputs must be processed within tick deadlines to avoid latency; late inputs are handled deterministically.

---

## 🎯 Per-Tick Client Actions

* Sample keyboard state (`pygame.key.get_pressed()`).
* Send two framed messages in order: `user_data`, then `keys`.
* Receive four framed messages from server in exact order.
* Render frame using Pygame; clients do not perform game logic.

---

## 🔌 Disconnection Handling

* All blocking `recv()` calls are wrapped in `try/except`.
* On disconnect, `handle_client_disconnect(conn, addr)`:

  * Clears per-match state
  * Resets `user1` / `user2` slots
  * Clears enemies and laser lists
  * Resets levels, velocities, player health, and flags
  * Closes socket and terminates thread
* Server remains ready for new connections.

---


## 🚀 How to Run

**Prerequisites**
- Python 3.8+ (tested on 3.9)
- Pygame (install: `pip install pygame`)

**Start server**
```bash
python server.py
```

**Start clients** (run twice on two separate terminals or machines)
```bash
python client.py
```

**Network configuration (LAN)**
- Set `SERVER` in both files to the server's LAN IP if running across machines.
- Ensure TCP port **5050** is reachable and not blocked by firewall.



---
