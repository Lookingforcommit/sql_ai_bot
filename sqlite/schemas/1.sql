CREATE TABLE IF NOT EXISTS users (
    name TEXT,
    surname TEXT,
    patronymic TEXT,
    telegram_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
    timestamp DATETIME,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
);
