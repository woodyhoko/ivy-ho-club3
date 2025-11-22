import socket
import struct
import pickle
import threading
import time
import uuid
import asyncio
import random
from collections import UserDict

# --- Protocol Constants ---
OP_UPDATE = 1      # "Here is a data change"
OP_SYNC_REQ = 2    # "I am new, please send data"
OP_SYNC_CLAIM = 3  # "I will handle the sync for this user"

class Club3(UserDict):
    def __init__(self, port=55516, group='224.224.224.1'):
        super().__init__()
        # set initial contents without triggering network broadcasts
        self.data.update({
            'club_name': ["Club 3"],
            'club_owner': ["Ivy", "Ho"],
            'message': ["Happy 3rd Anniversary!"],
        })
        self.port = port
        self.group = group
        self._node_id = uuid.uuid4().int
        self._metadata = {} 
        self._lock = threading.Lock()
        self._observers = set()
        
        # To track who we are currently syncing so we don't overlap
        self._handled_requests = set() 

        # --- Network Setup ---
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.bind(('0.0.0.0', port))
        except Exception:
            self._sock.bind(('', port))

        mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

        # Announce existence immediately
        self._request_sync()

    def _request_sync(self):
        # We include a specific Request ID so people know what they are claiming
        req_id = uuid.uuid4().int
        packet = pickle.dumps({'op': OP_SYNC_REQ, 'req_id': req_id, 'id': self._node_id})
        self._send_packet(packet)

    def __setitem__(self, key, value):
        ts = time.time()
        with self._lock:
            super().__setitem__(key, value)
            self._metadata[key] = ts
        
        self._broadcast_update(key, value, ts)
        self._notify_observers(key, value)

    def _broadcast_update(self, key, value, ts):
        packet = pickle.dumps({
            'op': OP_UPDATE,
            'k': key, 'v': value, 'ts': ts, 'id': self._node_id
        })
        self._send_packet(packet)

    def _send_packet(self, data):
        try:
            self._sock.sendto(data, (self.group, self.port))
        except OSError: pass

    def _listen_loop(self):
        while self._running:
            try:
                data, _ = self._sock.recvfrom(65535)
                p = pickle.loads(data)
                
                if p['id'] == self._node_id: continue 

                op = p['op']

                if op == OP_UPDATE:
                    key, val, remote_ts = p['k'], p['v'], p['ts']
                    with self._lock:
                        local_ts = self._metadata.get(key, 0)
                        if remote_ts > local_ts:
                            super().__setitem__(key, val)
                            self._metadata[key] = remote_ts
                            self._notify_observers(key, val)

                elif op == OP_SYNC_REQ:
                    # Start the "Volunteer Lottery" in a background thread
                    # so we don't block the main listener
                    threading.Thread(target=self._try_to_volunteer, args=(p['req_id'],), daemon=True).start()

                elif op == OP_SYNC_CLAIM:
                    # Someone else claimed this request ID!
                    # Add to our list so the volunteer thread knows to back off
                    self._handled_requests.add(p['req_id'])

            except Exception as e:
                if self._running: print(f"Net Error: {e}")

    def _try_to_volunteer(self, req_id):
        """
        The 'Suppression' Logic.
        Wait a random time. If no one claimed it, claim it and send data.
        """
        # 1. Wait random time (prioritize stability over speed here)
        time.sleep(random.uniform(0.1, 0.5))

        # 2. Check if someone else already claimed it while we were sleeping
        if req_id in self._handled_requests:
            # Clean up memory and give up
            self._handled_requests.discard(req_id)
            return 

        # 3. No one claimed it? I WILL DO IT.
        # Broadcast the claim so others stop waiting
        claim_packet = pickle.dumps({'op': OP_SYNC_CLAIM, 'req_id': req_id, 'id': self._node_id})
        self._send_packet(claim_packet)

        # 4. Send the data
        with self._lock:
            snapshot = list(self.items())

        for key, value in snapshot:
            ts = self._metadata.get(key, 0)
            self._broadcast_update(key, value, ts)
            time.sleep(0.001) # Bandwidth throttle

    def _notify_observers(self, key, value):
        for q, loop in list(self._observers):
            if not loop.is_closed():
                loop.call_soon_threadsafe(q.put_nowait, (key, value))

    async def watch(self):
        loop = asyncio.get_running_loop()
        q = asyncio.Queue()
        self._observers.add((q, loop))
        try:
            while True:
                yield await q.get()
        finally:
            self._observers.discard((q, loop))

    def close(self):
        self._running = False
        self._sock.close()