# Club3: The Ivy & Ho Anniversary Protocol 🥂

**A serverless, decentralized, conflict-free shared space.**

> *"Two nodes, one network, zero servers."*

**Club3** is a Python library created to celebrate the **3rd Anniversary of Ivy & Ho**. It creates a shared, synchronized dictionary across a local network. It allows devices to discover each other instantly and stay in perfect sync without a central server—just like a strong partnership.

---

## 💖 The Philosophy

Under the hood, this project is built on a **CRDT (Conflict-free Replicated Data Type)** using a "Last-Write-Wins" register.

* **Resilience:** If we disagree (concurrent updates), the system converges to a single truth without crashing.
* **Forgiveness:** It accepts the newest update, understanding that the state of things changes over time.
* **Connection:** It uses UDP Multicast, meaning it doesn't need a "manager" or a "server." It just needs the two of us on the same network.

---

## 🚀 Features

* **Serverless Sync:** Uses UDP Multicast (`224.1.1.1`) to find peers automatically.
* **Real-Time:** Changes on one laptop appear on the other instantly.
* **Modern Async API:** Supports `async for` loops to trigger UI updates cleanly.
* **Smart Discovery:** Includes "Thundering Herd" suppression—when a new device joins, only one peer volunteers to sync data, keeping the network quiet.
* **Thread-Safe:** Built with `threading.Lock` to handle background network traffic while you interact with the data.

---

## 📦 Installation

No external dependencies required. Just standard Python 3.
```shell
pip install ivy-ho-club3
```

---

## 💻 Usage

### 1. The Simple "Hello"

Open Python on **Computer A**:

```python
from ivy_ho import Club3

# Connect to the space
space = Club3()

# Write a note
space['anniversary'] = "Happy 3rd Year!"
space['dinner_plans'] = "Sushi at 7pm"
```

Open Python on Computer B:

```python
from ivy_ho import Club3

space = Club3()

# It syncs automatically!
print(space['anniversary']) 
# Output: "Happy 3rd Year!"
```

### 2. The Reactive Dashboard (Async)

Use this to build a UI or a script that reacts whenever the other person types.

```python
import asyncio
from ivy_ho import Club3

async def main():
    club = Club3()
    print(f"❤️ Connected as Node: {club._node_id}")

    # This loop pauses until Ivy or Ho changes something
    async for key, value in club.watch():
        print(f"✨ New Update: [{key}] is now -> {value}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Disconnected.")
```

---

## ⚙️ Under the Hood
For the curious engineers:

UDP Multicast: We bind to 0.0.0.0 and join group 224.224.224.1. This broadcasts packets to everyone on the LAN.

Packet Structure: We use pickle to serialize data, sending up to 65,535 bytes (the max UDP packet size).

Thundering Herd Suppression: When a new node sends OP_SYNC_REQ, existing nodes wait a random 0.1-0.5s. The first to wake up broadcasts an OP_SYNC_CLAIM, silencing the others. This ensures we don't flood the network with duplicate data.

---

## 🥂 Dedication
To Ivy & Ho,

Here is to 3 years of:

Fixing bugs/issues together.

Merging our lives without conflicts.

Staying synchronized, no matter the latency.

Happy Anniversary!

---

v3.0.1 - Built with Python & Love.