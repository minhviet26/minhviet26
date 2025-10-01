"""Simple appointment reminder manager with desktop notifications.

Usage::
    python reminder_app.py

The program stores reminders in an SQLite database and periodically checks
for appointments that are due. When a reminder is due it tries to display a
desktop notification (requires :mod:`plyer`).
"""

from __future__ import annotations

import sqlite3
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


try:
    from plyer import notification

    def send_notification(title: str, message: str) -> None:
        """Send a desktop notification using :mod:`plyer`."""

        notification.notify(title=title, message=message, timeout=10)


except Exception:  # pragma: no cover - fallback when plyer not available

    def send_notification(title: str, message: str) -> None:
        """Fallback when :mod:`plyer` isn't available: print to stderr."""

        print(f"[NOTIFICATION] {title}: {message}", file=sys.stderr)


DATABASE_FILE = Path("reminders.db")


@dataclass
class Reminder:
    id: int
    customer_name: str
    phone_number: str
    car_model: str
    car_year: str
    reminder_time: datetime
    notified: bool


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                car_model TEXT NOT NULL,
                car_year TEXT NOT NULL,
                reminder_time TEXT NOT NULL,
                notified INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError as exc:  # pragma: no cover - interactive validation
        raise ValueError(
            "Ngày nhắc hẹn không hợp lệ. Định dạng đúng: YYYY-MM-DD HH:MM"
        ) from exc


def add_reminder(
    customer_name: str,
    phone_number: str,
    car_model: str,
    car_year: str,
    reminder_time: datetime,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO reminders (
                customer_name, phone_number, car_model, car_year, reminder_time
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                customer_name,
                phone_number,
                car_model,
                car_year,
                reminder_time.isoformat(timespec="minutes"),
            ),
        )
        conn.commit()


def iter_pending_reminders(conn: sqlite3.Connection) -> Iterable[Reminder]:
    now_iso = datetime.now().isoformat(timespec="minutes")
    cursor = conn.execute(
        """
        SELECT * FROM reminders
        WHERE notified = 0 AND reminder_time <= ?
        ORDER BY reminder_time ASC
        """,
        (now_iso,),
    )
    for row in cursor:
        yield Reminder(
            id=row["id"],
            customer_name=row["customer_name"],
            phone_number=row["phone_number"],
            car_model=row["car_model"],
            car_year=row["car_year"],
            reminder_time=datetime.fromisoformat(row["reminder_time"]),
            notified=bool(row["notified"]),
        )


def mark_notified(conn: sqlite3.Connection, reminder_id: int) -> None:
    conn.execute(
        "UPDATE reminders SET notified = 1 WHERE id = ?",
        (reminder_id,),
    )
    conn.commit()


def format_reminder(reminder: Reminder) -> str:
    return (
        f"[{reminder.id}] {reminder.customer_name} | {reminder.phone_number} | "
        f"{reminder.car_model} - {reminder.car_year} | "
        f"Nhắc: {reminder.reminder_time:%Y-%m-%d %H:%M}"
    )


def list_reminders() -> list[Reminder]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM reminders ORDER BY reminder_time ASC"
        )
        reminders = [
            Reminder(
                id=row["id"],
                customer_name=row["customer_name"],
                phone_number=row["phone_number"],
                car_model=row["car_model"],
                car_year=row["car_year"],
                reminder_time=datetime.fromisoformat(row["reminder_time"]),
                notified=bool(row["notified"]),
            )
            for row in cursor
        ]
    return reminders


def reminder_loop(stop_event: threading.Event, interval_seconds: int = 60) -> None:
    while not stop_event.is_set():
        with get_connection() as conn:
            for reminder in iter_pending_reminders(conn):
                message = (
                    f"{reminder.customer_name} | {reminder.phone_number}\n"
                    f"Xe: {reminder.car_model} - {reminder.car_year}"
                )
                send_notification("Nhắc lịch hẹn", message)
                mark_notified(conn, reminder.id)
        stop_event.wait(interval_seconds)


def prompt_input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:  # pragma: no cover - interactive exit
        print()
        sys.exit(0)


def handle_add_reminder() -> None:
    print("\nNhập thông tin lịch hẹn")
    name = prompt_input("Họ và tên: ")
    phone = prompt_input("Số điện thoại: ")
    car_model = prompt_input("Tên xe: ")
    car_year = prompt_input("Đời xe: ")
    reminder_str = prompt_input("Ngày nhắc hẹn (YYYY-MM-DD HH:MM): ")
    reminder_time = parse_datetime(reminder_str)
    add_reminder(name, phone, car_model, car_year, reminder_time)
    print("Đã lưu lịch hẹn thành công!\n")


def handle_list_reminders() -> None:
    reminders = list_reminders()
    if not reminders:
        print("Chưa có lịch hẹn nào.")
        return
    print("\nDanh sách lịch hẹn:")
    for reminder in reminders:
        status = "Đã nhắc" if reminder.notified else "Chưa nhắc"
        print(f"- {format_reminder(reminder)} | {status}")
    print()


def main() -> None:
    initialize_database()

    print("Chương trình quản lý nhắc lịch hẹn với khách hàng")
    print("Dữ liệu được lưu tại:", DATABASE_FILE.resolve())

    stop_event = threading.Event()
    watcher = threading.Thread(target=reminder_loop, args=(stop_event,), daemon=True)
    watcher.start()

    menu = (
        "\nChọn chức năng:\n"
        "1. Thêm lịch hẹn mới\n"
        "2. Xem tất cả lịch hẹn\n"
        "3. Thoát\n"
        "Lựa chọn: "
    )

    try:
        while True:
            choice = prompt_input(menu)
            if choice == "1":
                try:
                    handle_add_reminder()
                except ValueError as exc:
                    print(exc)
            elif choice == "2":
                handle_list_reminders()
            elif choice == "3":
                print("Tạm biệt!")
                break
            else:
                print("Lựa chọn không hợp lệ, vui lòng thử lại.")
    finally:
        stop_event.set()
        watcher.join(timeout=1)


if __name__ == "__main__":
    main()

