# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets

logging.basicConfig()

THREAD = []

USERS = set()


def history_event():
    return json.dumps({"type": "history", "thread_history": THREAD if 0 < len(THREAD) else None})


def thread_event():
    return json.dumps({"type": "thread", "last_message": THREAD[-1] if 0 < len(THREAD) else None})


def users_event(new_user):
    return json.dumps({"type": "users", "count": len(USERS),
                       "count_change_message": "user joined the chat" if new_user else "user left the chat"})


async def notify_history(user):
    if USERS:
        message = history_event()
        await asyncio.create_task(user.send(message))


async def notify_thread():
    if USERS:
        message = thread_event()
        await asyncio.wait([user.send(message) for user in USERS])


async def notify_users(new_user):
    if USERS:
        message = users_event(new_user=new_user)
        await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
    # Add user to count on login
    USERS.add(websocket)
    await notify_history(websocket)
    await notify_users(new_user=True)


async def unregister(websocket):
    # Delete user from count on logout
    USERS.remove(websocket)
    await notify_users(new_user=False)


async def chat(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["message"]:
                message = data["message"]
                logging.info("message '{}' received", message)
                THREAD.append(message)
                await notify_thread()
            else:
                logging.error("unsupported event: {}", data)
    finally:
        await unregister(websocket)


start_server = websockets.serve(chat, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
