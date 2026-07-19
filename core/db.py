import sqlite3


DB_PATH = r"D:\Nexus98\data\db\models.db"



def init():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()


    cur.execute("""
    CREATE TABLE IF NOT EXISTS models (

        id TEXT PRIMARY KEY,

        name TEXT,

        source TEXT,

        type TEXT,

        provider TEXT,

        size TEXT,

        hash TEXT,

        installed INTEGER DEFAULT 0,

        favorite INTEGER DEFAULT 0

    )
    """)


    conn.commit()
    conn.close()



def ensure_columns():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()


    existing = [
        x[1]
        for x in cur.execute(
            "PRAGMA table_info(models)"
        )
    ]


    columns = {

        "provider": "TEXT",

        "size": "TEXT",

        "hash": "TEXT"

    }


    for name, typ in columns.items():

        if name not in existing:

            cur.execute(
                f"ALTER TABLE models ADD COLUMN {name} {typ}"
            )


    conn.commit()
    conn.close()



def upsert_model(m):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()


    cur.execute("""
    INSERT INTO models
    (
        id,
        name,
        source,
        type,
        provider,
        size,
        hash,
        installed,
        favorite
    )

    VALUES (?,?,?,?,?,?,?,?,?)

    ON CONFLICT(id)
    DO UPDATE SET

        name=excluded.name,

        source=excluded.source,

        type=excluded.type,

        provider=excluded.provider,

        size=excluded.size,

        hash=excluded.hash,

        installed=excluded.installed

    """,
    (

        m.get("id"),

        m.get("name"),

        m.get("source"),

        m.get("type"),

        m.get("provider"),

        m.get("size"),

        m.get("hash"),

        int(m.get("installed",False)),

        int(m.get("favorite",False))

    ))


    conn.commit()
    conn.close()



def get_all():

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()


    cur.execute("""
    SELECT

        id,

        name,

        source,

        type,

        provider,

        size,

        hash,

        installed,

        favorite

    FROM models
    """)


    rows = cur.fetchall()


    conn.close()


    return rows



def set_favorite(model_id,value):

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()


    cur.execute(
        "UPDATE models SET favorite=? WHERE id=?",
        (
            value,
            model_id
        )
    )


    conn.commit()
    conn.close()



def set_installed(model_id,value):

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()


    cur.execute(
        "UPDATE models SET installed=? WHERE id=?",
        (
            value,
            model_id
        )
    )


    conn.commit()
    conn.close()



ensure_columns()
