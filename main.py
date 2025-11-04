"""Main application for Raspberry Pi face recognition attendance management."""

from __future__ import annotations

import json
import pickle
import queue
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import face_recognition
import numpy as np
from picamera2 import Picamera2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk


CV_SCALER = 4
WORK_START = datetime.strptime("08:30", "%H:%M").time()
WORK_END = datetime.strptime("18:00", "%H:%M").time()
EMPLOYEES = [
    "HARIS",
    "NGHIEM",
    "ANH",
    "HIEP",
    "FAISAL",
    "TIEM",
    "ADEEL",
    "AMIRUDIN",
    "RIN",
]
MONTHLY_DATA_FILE = Path("monthly_attendance_data.json")
ENCODINGS_FILE = Path("encodings.pickle")
DESKTOP_DIR = Path.home() / "Desktop"


def load_face_encodings(path: Path) -> Tuple[List[np.ndarray], List[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Encoding file not found: {path}")

    with path.open("rb") as enc_file:
        enc_data = pickle.loads(enc_file.read())
    return enc_data["encodings"], enc_data["names"]


def round_hours(delta: timedelta) -> float:
    return round(delta.total_seconds() / 3600, 2)


def is_working_day(target_date: date) -> bool:
    if target_date.weekday() < 5:  # Monday-Friday
        return True

    if target_date.weekday() != 5:  # Not Saturday
        return False

    # Determine if 1st or 3rd Saturday of the month
    first_day = target_date.replace(day=1)
    saturdays = []
    current = first_day
    while current.month == target_date.month:
        if current.weekday() == 5:
            saturdays.append(current)
        current += timedelta(days=1)
    if not saturdays:
        return False
    eligible = set()
    if len(saturdays) >= 1:
        eligible.add(saturdays[0])
    if len(saturdays) >= 3:
        eligible.add(saturdays[2])
    return target_date in eligible


def determine_period_boundaries(reference: date) -> Tuple[date, date]:
    if reference.day >= 21:
        period_start = reference.replace(day=21)
        # period end is 20th of next month
        next_month = (period_start.replace(day=1) + timedelta(days=32)).replace(day=1)
        period_end = next_month.replace(day=20)
    else:
        # period start is 21st of previous month
        prev_month = (reference.replace(day=1) - timedelta(days=1)).replace(day=1)
        period_start = prev_month.replace(day=21)
        period_end = reference.replace(day=20)
    return period_start, period_end


def daterange(start: date, end: date) -> List[date]:
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


@dataclass
class DailyRecord:
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    late: bool = False
    early_leave: bool = False

    @property
    def total_hours(self) -> Optional[float]:
        if self.clock_in and self.clock_out:
            return round_hours(self.clock_out - self.clock_in)
        return None

    @property
    def incomplete(self) -> bool:
        return self.clock_in is not None and self.clock_out is None


class AttendanceManager:
    def __init__(self, employees: List[str]):
        self.employees = employees
        self.daily_records: Dict[str, DailyRecord] = {
            name: DailyRecord() for name in employees
        }
        self.period_start, self.period_end = determine_period_boundaries(date.today())
        self.monthly_data = self._load_monthly_data()
        self.last_daily_export: Optional[date] = None
        self.last_monthly_export_period_end: Optional[date] = None

    def _load_monthly_data(self) -> Dict:
        if MONTHLY_DATA_FILE.exists():
            with MONTHLY_DATA_FILE.open("r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            saved_start = date.fromisoformat(data["period_start"])
            saved_end = date.fromisoformat(data["period_end"])
            if (saved_start, saved_end) != (self.period_start, self.period_end):
                # Period changed; start fresh
                return self._new_monthly_data()
            return data
        return self._new_monthly_data()

    def _new_monthly_data(self) -> Dict:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "records": {},
        }

    def _save_monthly_data(self) -> None:
        with MONTHLY_DATA_FILE.open("w", encoding="utf-8") as json_file:
            json.dump(self.monthly_data, json_file, indent=2)

    def _get_day_entry(self, entry_date: date) -> Dict:
        records = self.monthly_data.setdefault("records", {})
        return records.setdefault(entry_date.isoformat(), {})

    def _record_monthly(self, name: str, record: DailyRecord, record_date: date) -> None:
        day_entry = self._get_day_entry(record_date)
        info = day_entry.setdefault(name, {})
        info["clock_in"] = record.clock_in.isoformat() if record.clock_in else None
        info["clock_out"] = record.clock_out.isoformat() if record.clock_out else None
        info["late"] = record.late
        info["early_leave"] = record.early_leave
        info["incomplete"] = record.incomplete
        info["total_hours"] = record.total_hours
        self._save_monthly_data()

    def clock_in(self, name: str, timestamp: datetime) -> Tuple[bool, str]:
        record = self.daily_records[name]
        if record.clock_in is not None:
            return False, f"{name} has already clocked in."

        record.clock_in = timestamp
        record.late = timestamp.time() > WORK_START
        self._record_monthly(name, record, timestamp.date())
        return True, "Clock-in recorded successfully."

    def clock_out(self, name: str, timestamp: datetime) -> Tuple[bool, str]:
        record = self.daily_records[name]
        if record.clock_in is None:
            return False, f"{name} has not clocked in yet."
        if record.clock_out is not None:
            return False, f"{name} has already clocked out."

        record.clock_out = timestamp
        record.early_leave = timestamp.time() < WORK_END
        self._record_monthly(name, record, timestamp.date())
        return True, "Clock-out recorded successfully."

    def get_status(self, name: str) -> str:
        record = self.daily_records[name]
        if record.clock_out is not None:
            return "Clocked Out"
        if record.clock_in is not None:
            return "Clocked In"
        return "Not Yet"

    def get_display_rows(self) -> List[Tuple[str, str, str, str, Optional[bool]]]:
        rows = []
        for name in self.employees:
            record = self.daily_records[name]
            clock_in_text = ""
            if record.clock_in:
                clock_in_text = record.clock_in.strftime("%H:%M:%S")
            clock_out_text = record.clock_out.strftime("%H:%M:%S") if record.clock_out else ""
            rows.append(
                (
                    name,
                    clock_in_text,
                    clock_out_text,
                    self.get_status(name),
                    record.late if record.clock_in else None,
                )
            )
        return rows

    def reset_daily(self) -> None:
        self.daily_records = {name: DailyRecord() for name in self.employees}

    def export_daily_csv(self, export_date: date) -> Path:
        DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
        filename = DESKTOP_DIR / f"daily_attendance_{export_date.isoformat()}.csv"
        headers = [
            "Name",
            "Date",
            "Clock-in Time",
            "Clock-out Time",
            "Total Hours",
            "Late (Yes/No)",
            "Early Leave (Yes/No)",
        ]
        lines = [",".join(headers)]
        for name in self.employees:
            record = self.daily_records[name]
            clock_in_str = record.clock_in.strftime("%H:%M:%S") if record.clock_in else ""
            clock_out_str = record.clock_out.strftime("%H:%M:%S") if record.clock_out else ""
            total_hours = "" if record.total_hours is None else f"{record.total_hours:.2f}"
            late_str = "N/A"
            early_str = "N/A"
            if record.clock_in:
                late_str = "Yes" if record.late else "No"
            if record.clock_out:
                early_str = "Yes" if record.early_leave else "No"
            elif record.clock_in:
                early_str = "Incomplete"
            line = ",".join(
                [
                    name,
                    export_date.isoformat(),
                    clock_in_str,
                    clock_out_str,
                    total_hours,
                    late_str,
                    early_str,
                ]
            )
            lines.append(line)
        filename.write_text("\n".join(lines), encoding="utf-8")
        self.last_daily_export = export_date
        return filename

    def _expected_working_days(self) -> List[date]:
        return [
            day
            for day in daterange(self.period_start, self.period_end)
            if is_working_day(day)
        ]

    def generate_monthly_report(self) -> Path:
        period_start = date.fromisoformat(self.monthly_data["period_start"])
        period_end = date.fromisoformat(self.monthly_data["period_end"])
        records = self.monthly_data.get("records", {})
        expected_days = [d for d in daterange(period_start, period_end) if is_working_day(d)]

        DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
        filename = (
            DESKTOP_DIR
            / f"monthly_report_{period_start.isoformat()}_to_{period_end.isoformat()}.csv"
        )

        headers = [
            "Name",
            "Period Start",
            "Period End",
            "Total Working Days",
            "Expected Working Days",
            "Attendance Rate",
            "Late Count",
            "Early Leave Count",
            "Total Hours",
            "Late Dates",
            "Early Leave Dates",
            "Absent Dates",
            "Incomplete Dates",
        ]

        lines = [",".join(headers)]
        for name in self.employees:
            total_days_worked = 0
            total_hours = 0.0
            late_dates: List[str] = []
            early_dates: List[str] = []
            incomplete_dates: List[str] = []
            for day in records:
                day_record = records[day].get(name)
                if not day_record:
                    continue
                if day_record.get("clock_in"):
                    total_days_worked += 1
                if day_record.get("total_hours"):
                    total_hours += float(day_record["total_hours"])
                if day_record.get("late"):
                    late_dates.append(day)
                if day_record.get("early_leave"):
                    early_dates.append(day)
                if day_record.get("incomplete"):
                    incomplete_dates.append(day)

            attended_dates = {
                day
                for day, day_data in records.items()
                if name in day_data and day_data[name].get("clock_in")
            }
            absent_dates = [
                d.isoformat()
                for d in expected_days
                if d.isoformat() not in attended_dates
            ]

            expected_count = len(expected_days)
            attendance_rate = (
                f"{(total_days_worked / expected_count) * 100:.0f}%"
                if expected_count
                else "0%"
            )

            line = ",".join(
                [
                    name,
                    period_start.isoformat(),
                    period_end.isoformat(),
                    str(total_days_worked),
                    str(expected_count),
                    attendance_rate,
                    str(len(late_dates)),
                    str(len(early_dates)),
                    f"{total_hours:.2f}",
                    f"\"{', '.join(late_dates)}\"" if late_dates else "",
                    f"\"{', '.join(early_dates)}\"" if early_dates else "",
                    f"\"{', '.join(absent_dates)}\"" if absent_dates else "",
                    f"\"{', '.join(incomplete_dates)}\"" if incomplete_dates else "",
                ]
            )
            lines.append(line)

        filename.write_text("\n".join(lines), encoding="utf-8")
        self.last_monthly_export_period_end = period_end

        # Reset for next period starting the next day (21st)
        next_period_start = period_end + timedelta(days=1)
        self.period_start, self.period_end = determine_period_boundaries(next_period_start)
        self.monthly_data = {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "records": {},
        }
        self._save_monthly_data()
        return filename


class FaceRecognitionThread(threading.Thread):
    def __init__(
        self,
        picam2: Picamera2,
        known_encodings: List[np.ndarray],
        known_names: List[str],
        frame_queue: queue.Queue,
        stop_event: threading.Event,
        employees: List[str],
    ) -> None:
        super().__init__(daemon=True)
        self.picam2 = picam2
        self.known_encodings = known_encodings
        self.known_names = known_names
        self.frame_queue = frame_queue
        self.stop_event = stop_event
        self.employees = set(employees)
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0.0

    def run(self) -> None:
        while not self.stop_event.is_set():
            frame = self.picam2.capture_array()
            display_frame, active_name = self._process_frame(frame)
            frame_data = {
                "frame": display_frame,
                "active_name": active_name,
                "fps": self.fps,
            }
            try:
                self.frame_queue.put(frame_data, timeout=0.01)
            except queue.Full:
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self.frame_queue.put(frame_data, timeout=0.01)
                except queue.Full:
                    pass

    def _process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[str]]:
        resized_frame = cv2.resize(
            frame, (0, 0), fx=(1 / CV_SCALER), fy=(1 / CV_SCALER)
        )
        rgb_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_resized_frame)
        face_encodings = face_recognition.face_encodings(
            rgb_resized_frame, face_locations, model="large"
        )

        face_names = []
        active_name = None
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(
                self.known_encodings, face_encoding
            )
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_names[best_match_index]

            face_names.append(name)

        for idx, (top, right, bottom, left) in enumerate(face_locations):
            name = face_names[idx] if idx < len(face_names) else "Unknown"
            top *= CV_SCALER
            right *= CV_SCALER
            bottom *= CV_SCALER
            left *= CV_SCALER

            cv2.rectangle(frame, (left, top), (right, bottom), (244, 42, 3), 2)
            cv2.rectangle(frame, (left - 3, top - 35), (right + 3, top), (244, 42, 3), -1)
            cv2.putText(
                frame,
                name,
                (left + 6, top - 10),
                cv2.FONT_HERSHEY_DUPLEX,
                1.0,
                (255, 255, 255),
                1,
            )

        known_detected = [name for name in face_names if name in self.employees]
        if known_detected:
            active_name = known_detected[0]

        self._update_fps()
        cv2.putText(
            frame,
            f"FPS: {self.fps:.1f}",
            (frame.shape[1] - 200, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        return frame, active_name

    def _update_fps(self) -> None:
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        if elapsed >= 1:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()


class SchedulerThread(threading.Thread):
    def __init__(
        self,
        attendance_manager: AttendanceManager,
        stop_event: threading.Event,
        notify_callback,
    ) -> None:
        super().__init__(daemon=True)
        self.attendance_manager = attendance_manager
        self.stop_event = stop_event
        self.notify_callback = notify_callback

    def run(self) -> None:
        while not self.stop_event.is_set():
            now = datetime.now()
            try:
                self._handle_daily_export(now)
                self._handle_monthly_report(now)
            except Exception as exc:  # noqa: BLE001
                self.notify_callback(f"Scheduler error: {exc}")
            time.sleep(30)

    def _handle_daily_export(self, now: datetime) -> None:
        if now.hour < 23:
            return
        if self.attendance_manager.last_daily_export == now.date():
            return
        export_path = self.attendance_manager.export_daily_csv(now.date())
        self.attendance_manager.reset_daily()
        self.notify_callback(f"Daily attendance saved to {export_path}")

    def _handle_monthly_report(self, now: datetime) -> None:
        period_end = date.fromisoformat(self.attendance_manager.monthly_data["period_end"])
        if now.date() != period_end or now.hour < 23:
            return
        if (
            self.attendance_manager.last_monthly_export_period_end
            and self.attendance_manager.last_monthly_export_period_end >= period_end
        ):
            return
        report_path = self.attendance_manager.generate_monthly_report()
        self.notify_callback(f"Monthly report saved to {report_path}")


class AttendanceApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Attendance Management System")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.attendance_manager = AttendanceManager(EMPLOYEES)
        self._setup_gui()

        self.frame_queue: "queue.Queue[Dict]" = queue.Queue(maxsize=2)
        self.stop_event = threading.Event()

        self.picam2 = Picamera2()
        self.picam2.configure(
            self.picam2.create_preview_configuration(
                main={"format": "XRGB8888", "size": (1920, 1080)}
            )
        )
        self.picam2.start()

        self.known_encodings, self.known_names = load_face_encodings(ENCODINGS_FILE)

        self.face_thread = FaceRecognitionThread(
            self.picam2,
            self.known_encodings,
            self.known_names,
            self.frame_queue,
            self.stop_event,
            EMPLOYEES,
        )
        self.face_thread.start()

        self.scheduler_thread = SchedulerThread(
            self.attendance_manager,
            self.stop_event,
            self._update_status_message,
        )
        self.scheduler_thread.start()

        self.current_prompt_name: Optional[str] = None
        self.last_prompt_time: Optional[float] = None
        self._update_ui()

    def _setup_gui(self) -> None:
        self.video_label = tk.Label(self.root)
        self.video_label.grid(row=0, column=0, rowspan=6, padx=10, pady=10)

        columns = ("Name", "Clock In", "Clock Out", "Status")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor=tk.CENTER)
        self.tree.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.message_label = tk.Label(
            self.root,
            text="Waiting for detection...",
            font=("Helvetica", 18),
            wraplength=400,
            justify="left",
        )
        self.message_label.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        self.action_button = tk.Button(
            self.root,
            text="",
            font=("Helvetica", 16),
            command=self._handle_action,
        )
        self.action_button.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        self.action_button.grid_remove()

        self.status_message = tk.StringVar(value="System initialized.")
        status_label = tk.Label(
            self.root,
            textvariable=self.status_message,
            font=("Helvetica", 12),
            fg="green",
            justify="left",
        )
        status_label.grid(row=3, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        self._refresh_employee_table()

    def _update_status_message(self, message: str) -> None:
        def update() -> None:
            self.status_message.set(message)
            self._refresh_employee_table()

        self.root.after(0, update)

    def _handle_action(self) -> None:
        if not self.current_prompt_name:
            return
        name = self.current_prompt_name
        now = datetime.now()
        status = self.attendance_manager.get_status(name)
        if status == "Not Yet":
            success, msg = self.attendance_manager.clock_in(name, now)
        elif status == "Clocked In":
            success, msg = self.attendance_manager.clock_out(name, now)
        else:
            success = False
            msg = f"{name} has already completed attendance for today."
        if success:
            self._update_status_message(msg)
        else:
            messagebox.showinfo("Attendance", msg)
        self._refresh_employee_table()
        self._reset_prompt()

    def _reset_prompt(self) -> None:
        self.current_prompt_name = None
        self.last_prompt_time = None
        self.message_label.config(text="Waiting for detection...")
        self.action_button.grid_remove()

    def _refresh_employee_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.attendance_manager.get_display_rows():
            name, clock_in, clock_out, status, late_flag = row
            self.tree.insert("", tk.END, values=(name, clock_in, clock_out, status))
            item = self.tree.get_children()[-1]
            if late_flag is True:
                self.tree.tag_configure("late", foreground="red")
                self.tree.item(item, tags=("late",))
            elif late_flag is False and clock_in:
                self.tree.tag_configure("ontime", foreground="green")
                self.tree.item(item, tags=("ontime",))

    def _update_ui(self) -> None:
        try:
            frame_info = self.frame_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            frame = frame_info["frame"]
            active_name = frame_info["active_name"]
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image)
            imgtk = ImageTk.PhotoImage(image=image_pil)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            self._refresh_employee_table()
            self._handle_prompt(active_name)

        self.root.after(50, self._update_ui)

    def _handle_prompt(self, detected_name: Optional[str]) -> None:
        if not detected_name:
            # Reset prompt if no one detected for a short while
            if self.last_prompt_time and time.time() - self.last_prompt_time > 5:
                self._reset_prompt()
            return

        if detected_name not in EMPLOYEES:
            return

        status = self.attendance_manager.get_status(detected_name)
        if status == "Clocked Out":
            self.message_label.config(
                text=f"Thank you, {detected_name}. Attendance already completed."
            )
            self.action_button.grid_remove()
            self.current_prompt_name = None
            return

        prompt_changed = detected_name != self.current_prompt_name
        now = time.time()
        if prompt_changed or not self.last_prompt_time or now - self.last_prompt_time > 3:
            self.current_prompt_name = detected_name
            self.last_prompt_time = now
            if status == "Not Yet":
                self.message_label.config(
                    text=f"Good morning, {detected_name}. Would you like to clock in?"
                )
                self.action_button.config(text="Clock In")
                self.action_button.grid()
            elif status == "Clocked In":
                self.message_label.config(
                    text=f"Good job, {detected_name}. Would you like to clock out?"
                )
                self.action_button.config(text="Clock Out")
                self.action_button.grid()

    def on_close(self) -> None:
        self.stop_event.set()
        self.face_thread.join(timeout=2)
        self.scheduler_thread.join(timeout=2)
        try:
            self.picam2.stop()
        except Exception:  # noqa: BLE001
            pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = AttendanceApp()
    app.run()


if __name__ == "__main__":
    main()

