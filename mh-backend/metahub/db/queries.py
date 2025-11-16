from asyncpg.connection import Connection

async def get_clients(conn: Connection):
    conn.execute("SELECT id, name FROM clients")

async def add_client(conn: Connection, name: str, host: str):
    pass

async def get_client_categories(conn: Connection, client_id: int):
    pass

async def add_category(conn: Connection, client_id: int, name: str):
    pass

async def get_category_tags(conn: Connection, category_id: int):
    pass

async def add_tag(conn: Connection, category_id: int, name: str):
    pass

async def get_registered_nodes_of(conn: Connection, tag_id: int):
    pass