CREATE TABLE IF NOT EXISTS users (
    name TEXT,
    surname TEXT,
    patronymic TEXT,
    telegram_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS actions (
    message TEXT,
    timestamp DATETIME,
    user_id INTEGER,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
);

CREATE TABLE IF NOT EXISTS stats (
    correct_num INTEGER,
    incorrect_num INTEGER,
    user_id INTEGER PRIMARY KEY,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
);

CREATE TABLE IF NOT EXISTS scheduler (
    interval_minutes INTEGER,
    user_id INTEGER PRIMARY KEY,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
);