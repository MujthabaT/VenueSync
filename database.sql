CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(100) UNIQUE NOT NULL,
    password   VARCHAR(255) NOT NULL,
    role       VARCHAR(20) DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS venues (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(200) NOT NULL,
    capacity INT,
    location VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS bookings (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    venue_id       INT NOT NULL,
    event_name     VARCHAR(200) NOT NULL,
    purpose        TEXT,
    event_id       VARCHAR(100),
    special_guests TEXT,
    date           DATE NOT NULL,
    time           TIME NOT NULL,
    status         VARCHAR(20) DEFAULT 'pending',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)  REFERENCES users(id),
    FOREIGN KEY (venue_id) REFERENCES venues(id)
);

INSERT IGNORE INTO venues (name, capacity, location) VALUES
    ('Main Auditorium',  500,  'Block A'),
    ('Conference Hall',  100,  'Block B'),
    ('Seminar Room 1',   50,   'Block C'),
    ('Seminar Room 2',   50,   'Block C'),
    ('Open Air Theatre', 1000, 'Campus Ground');
