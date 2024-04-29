# gpt_wss_api
A api wrapper for chatgpt wss connection. If you get 403 errors while connecting wss url of chatgpt, you are at right place.

## Example

```
import asyncio
from gpt_wss_api import WebSocketClient

class WSS:
    def __init__(self, url=None, headers=None):
        self.url = url
        self.headers = headers
        self.sockClient = WebSocketClient(url=self.url, headers=self.headers)

    async def connect(self):
        try:
            ret = await self.sockClient.connect()
            if ret:
                print('Connected successfully')
                return True
            else:
                print('Failed to connect!')
                return False
        except Exception as e:
            print(f"Error connecting to WebSocket: {e}")
            return False

    async def send(self, message):
        if await self.sockClient.isConnected():
            await self.sockClient.send(message)

    async def recv(self):
        try:
            while await self.sockClient.isConnected():
                message = await self.sockClient.recv()
                print(message)
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error receiving data: {e}")

    async def close(self):
        await self.sockClient.close()

async def main():
    url = 'wss://chatgpt-async-webps-prod-southcentralus-5.chatgpt.com/client/hubs/conversations?access_token=eyJhbGcixxxxxxxxxx'
    headers = {
        'Host': 'chatgpt-async-webps-prod-southcentralus-5.chatgpt.com',
        'Connection': 'Upgrade',
        'Upgrade': 'websocket',
        'Sec-WebSocket-Version': '13',
        'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
    }
    wss = WSS(url, headers)
    if await wss.connect():
        # asyncio.create_task(wss.send('Hello WebSocket!'))
        await wss.recv()
    await wss.close()

if __name__ == '__main__':
    asyncio.run(main())

```