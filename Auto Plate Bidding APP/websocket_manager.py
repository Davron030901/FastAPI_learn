class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def broadcast(self, message: str, plate_id: int):
        if plate_id in self.active_connections:
            for connection in self.active_connections[plate_id]:
                await connection.send_text(message)