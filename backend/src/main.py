from autogen.agentchat import initiate_group_chat
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketState
from agents import pattern

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()

            chat_result, context, last_agent = initiate_group_chat(
                pattern=pattern,
                messages=data,
                max_rounds=10,
            )

            await websocket.send_text(chat_result.summary)

        except Exception:
            if websocket.application_state != WebSocketState.DISCONNECTED:
                await websocket.close()
