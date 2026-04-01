from dataclasses import dataclass, field
from datetime import time
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care activity."""

    id: str
    pet_id: str
    name: str
    description: str
    duration_mins: int
    frequency: str        # "once", "daily", "weekly"
    priority: int         # 1 (low) to 5 (high)
    due_time: Optional[time] = None
    is_completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def __str__(self) -> str:
        due = self.due_time.strftime("%I:%M %p") if self.due_time else "No time set"
        status = "Done" if self.is_completed else "Pending"
        return (
            f"[{status}] {self.name} @ {due} "
            f"({self.duration_mins} min) — Priority {self.priority}"
        )


@dataclass
class Pet:
    """Stores pet profile details."""

    id: str
    name: str
    species: str
    breed: str
    age_years: int
    weight_kg: float
    allergies: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    days_since_groomed: int = 0

    def __str__(self) -> str:
        return f"{self.name} ({self.breed}, {self.age_years}yr)"


@dataclass
class Owner:
    """Manages a collection of pets."""

    name: str
    contact_info: str
    available_hours: list[tuple[time, time]] = field(default_factory=list)
    notification_preference: str = "app"  # "app", "email", "sms"
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's roster."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet by ID from this owner's roster."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def get_all_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets


class Scheduler:
    """Retrieves, organizes, and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        """Initialize with an owner; pets are sourced from owner only."""
        self.owner = owner
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the scheduler."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by ID."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_tasks_for_pet(self, pet: Pet) -> list[Task]:
        """Return all tasks belonging to a specific pet."""
        return [t for t in self.tasks if t.pet_id == pet.id]

    def get_incomplete_tasks(self, pet: Pet) -> list[Task]:
        """Return tasks for a pet that are not yet completed."""
        return [t for t in self.get_tasks_for_pet(pet) if not t.is_completed]

    def check_conflicts(self) -> bool:
        """Return True if any two tasks have overlapping time windows."""
        timed = [t for t in self.tasks if t.due_time and not t.is_completed]
        timed.sort(key=lambda t: t.due_time)
        for i in range(len(timed) - 1):
            a, b = timed[i], timed[i + 1]
            a_end_h = a.due_time.hour + a.duration_mins // 60
            a_end_m = a.due_time.minute + a.duration_mins % 60
            a_end = time(a_end_h % 24, a_end_m % 60)
            if a_end > b.due_time:
                return True
        return False

    def generate_daily_plan(self) -> list[Task]:
        """Return today's pending tasks sorted by priority (high first), then due time."""
        pending = [t for t in self.tasks if not t.is_completed]
        return sorted(
            pending,
            key=lambda t: (
                -t.priority,
                t.due_time or time(23, 59),
            ),
        )

    def send_reminder(self, task: Task) -> None:
        """Print a reminder for a task (placeholder for real notification logic)."""
        pet_name = next(
            (p.name for p in self.owner.pets if p.id == task.pet_id), "Unknown pet"
        )
        due = task.due_time.strftime("%I:%M %p") if task.due_time else "soon"
        print(f"REMINDER [{self.owner.notification_preference.upper()}]: "
              f"'{task.name}' for {pet_name} is due at {due}.")
