import asyncio
import struct
import hashlib
import base64
import re
import os
import time
import zlib
from urllib.parse import urlparse
import socket

from pyhttpx.layers.tls.pyaiossl import SSLContext,PROTOCOL_TLSv1_2
from pyhttpx.exception import (
    SwitchingProtocolError,
    SecWebSocketKeyError,
    WebSocketClosed,
    ConnectionClosed
)

DEFAULT_HEADERS = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh,zh-CN;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Upgrade': 'websocket',
        'Connection': 'Upgrade',
        'Sec-WebSocket-Version': '13',
        'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
        }

class WebSocketClient:
    def __init__(self, url=None, headers=None, loop=None, ja3=None, exts_payload=None,ping=False):
        self._urlparse = urlparse(url)
        self.headers = headers or DEFAULT_HEADERS
        self.ja3 = ja3
        self.exts_payload = exts_payload
        self.ping = ping
        if ':' in self._urlparse.netloc:
            host = self._urlparse.netloc.split(':')[0]
            port = self._urlparse.netloc.split(':')[1]
            self.addres = (host, int(port))
        else:
            self.addres = (self._urlparse.netloc, 443)

        self.headers['Host'] = self.addres[0]

        if not self._urlparse.path:
            self.path = '/'
        elif self._urlparse.query:
            self.path = f'{self._urlparse.path}?{self._urlparse.query}'
        else:
            self.path = self._urlparse.path

        self.open = None
        self.loop = loop or asyncio.get_event_loop()
        self.load = True
        self.cache_buffer = b''
        self.reader_buffer = b''

    def isConnected(self):
        return self.open

    async def close(self):
        await self.send(struct.pack('!H', 1000).decode('latin1'), binary=True, opc=0b1000)
        self.open = False

    async def connect(self):
        context = SSLContext(PROTOCOL_TLSv1_2)
        context.set_payload(browser_type='chrome', ja3=self.ja3, exts_payload=self.exts_payload)
        self.sock = context.wrap_socket()
        await self.sock.connect(self.addres)
        status_code = await self.on_open()
        if status_code == 200:
            self.open = True
            if self.ping:
                self.loop.create_task(self.loop_ping())
            return True
        else:
            self.open = False
            return False

    def check_proto(self, data):
        data = data.decode()
        proto, status_code = data.split('\r\n',1)[0].split(' ')[:2]
        head = {}

        if status_code == '101':
            for i in data.split('\r\n')[1:]:
                k, v = i.split(':', 1)
                k, v = k.strip(), v.strip()
                head[k.lower()] = v

            sec_websocket_key = self.sec_websocket_key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
            sec_websocket_accept = head['sec-websocket-accept']

            b = base64.b64encode(hashlib.sha1(sec_websocket_key.encode('latin1')).digest())
            if b != sec_websocket_accept.encode():
                raise SecWebSocketKeyError('sec_websocket_key verify failed')
        else:
            raise SwitchingProtocolError(f"connect fail!, status_code {status_code}")

    async def on_open(self):
        self.sec_websocket_key = base64.b64encode(os.urandom(16)).decode()
        self.headers['Sec-WebSocket-Key'] = self.sec_websocket_key
        self.headers['Upgrade'] = 'websocket'
        self.headers['Connection'] = 'Upgrade'
        self.headers['Sec-WebSocket-Version'] = '13'  # WebSocket version
        request_header = [f'GET {self.path} HTTP/1.1']
        for k, v in self.headers.items():
            request_header.append(f'{k}: {v}')
        request_header = '\r\n'.join(request_header) + '\r\n\r\n'
        # print(f"on_open, sending {request_header}", flush=True)
        await self.sock.sendall(request_header.encode())
        data = None
        while not data:
            data = await self.sock.recv(2**12)
        data_decoded = data.decode('utf-8', errors='ignore')
        print(f"Received data: {data_decoded}")
        match = re.search(r'HTTP\/\d\.\d (\d{3})', data_decoded)
        if match:
            status_code = int(match.group(1))
            print(f"WebSocket handshake response status code: {status_code}")
            return status_code
        else:
            print(f"Failed to find HTTP status code in response:{data}")
            return None

    async def send(self, data: str, binary: bool=True, opc: int=None):

        FIN  = 0b10000000
        RSV1 = 0b0000000
        RSV2 = 0b000000
        RSV3 = 0b00000
        opcode = 0b0010 if binary else 0b0001
        if opc:
            #
            opcode = opc
        head_frame = FIN | RSV1 | RSV2 | RSV3 | opcode

        s = struct.pack('!B', head_frame)
        if len(data) < 126:
            MASK = 0b10000000
            MASK |= len(data)
            m = struct.pack('!B', MASK)
            s += m

        elif 126 <= len(data) <= 2 ** 16 -1:
            MASK = 0b10000000
            #数据长度2字节
            MASK |= 126
            #谁否掩码
            m = struct.pack('!B', MASK)
            s += m
            s += struct.pack('!H', len(data))



        elif 2 ** 16 -1 <  len(data) <= 2**64 -1:
            MASK = 0b10000000
            #数据长度8字节
            MASK |= 127
            m = struct.pack('!B', MASK)
            s += m
            s += struct.pack('!Q', len(data))

        else:
            raise OverflowError('data length more than 64 byte')

        mask_key = os.urandom(4)
        s += mask_key
        for i in range(len(data)):
            n = ord(data[i]) ^ (mask_key[i % 4])
            s += struct.pack('!B', n)

        await self.sock.sendall(s)

    async def recv(self):
        """Receive messages as an asynchronous generator."""
        try:
            while self.open:
                if len(self.cache_buffer) < 2:
                    data = await self.sock.recv(2**14)
                    if not data:
                        break
                    self.cache_buffer += data

                if len(self.cache_buffer) >= 2:
                    frame_head = self.cache_buffer[0]
                    FIN = frame_head >> 7
                    opcode = frame_head & 0b1111
                    payload_len = self.cache_buffer[1] & 0b1111111

                    if payload_len < 126:
                        header_size = 2
                    elif payload_len == 126:
                        if len(self.cache_buffer) < 4:
                            continue
                        payload_len, = struct.unpack('!H', self.cache_buffer[2:4])
                        header_size = 4
                    else:
                        if len(self.cache_buffer) < 10:
                            continue
                        payload_len, = struct.unpack('!Q', self.cache_buffer[2:10])
                        header_size = 10

                    total_frame_size = header_size + payload_len

                    if len(self.cache_buffer) < total_frame_size:
                        continue

                    msg = self.cache_buffer[header_size:total_frame_size]
                    self.cache_buffer = self.cache_buffer[total_frame_size:]

                    if opcode == 0x1 or opcode == 0x2:  # Text or Binary Frame
                        if FIN:
                            if opcode == 0x1:  # Text frame
                                yield msg.decode('utf-8')
                            else:  # Binary frame
                                yield msg
                    elif opcode == 0x8:  # Close Frame
                        self.open = False
                        await self.close()
                        break
                    elif opcode == 0x9:  # Ping Frame
                        await self.send(msg, binary=True, opc=0xA)  # Send Pong
        except Exception as e:
            print(f"Error during WebSocket communication: {e}")
        finally:
            await self.close()
            print("WebSocket connection has been closed.")

    async def loop_ping(self):
        while self.open:
            s = os.urandom(4).decode('latin1')
            print(f"send ping: {s}", flush=True)
            await self.send(s,binary=True, opc=0x09)
            await asyncio.sleep(20)




