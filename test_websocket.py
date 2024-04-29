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
            async for message in sockClient.recv():
                print(message)
                await asyncio.sleep(0.1)  # Slow down the loop if necessary
    except Exception as e:
        print(f"Error while handling WebSocket connection: {e}")
    finally:
        await sockClient.close()
        print("Connection closed.")

if __name__ == '__main__':
    asyncio.run(main())
