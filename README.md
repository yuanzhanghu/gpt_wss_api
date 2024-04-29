# gpt_wss_api
A api wrapper for chatgpt wss connection. If you get 403 errors while connecting wss url of chatgpt, you are at right place.

## Example

```
import asyncio
from gpt_wss_api import WebSocketClient

async def main():
    url = 'wss://chatgpt-async-webps-prod-southcentralus-5.chatgpt.com/client/hubs/conversations?access_token=eyJhbGcixxxxxxxxxx'
    headers = {
        'Host': 'chatgpt-async-webps-prod-southcentralus-5.chatgpt.com',
        'Connection': 'Upgrade',
        'Upgrade': 'websocket',
        'Sec-WebSocket-Version': '13',
        'Sec-WebSocket-Extensions': 'permessage-deflate',
    }
    sockClient = WebSocketClient(url=url, headers=headers)
    
    try:
        if await sockClient.connect():
            print('Connected successfully')
            try:
                while await sockClient.isConnected():
                    message = await sockClient.recv()
                    print(message)
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error receiving data: {e}")
        else:
            print('Failed to connect!')
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")
    finally:
        await sockClient.close()
        print("Connection closed.")

if __name__ == '__main__':
    asyncio.run(main())
```