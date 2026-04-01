import uuid
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

    # ── Sorting ──────────────────────────────────────────────────────────────

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks sorted by due_time ascending; tasks with no time go last."""
        source = tasks if tasks is not None else self.tasks
        return sorted(source, key=lambda t: t.due_time or time(23, 59))

    # ── Filtering ────────────────────────────────────────────────────────────

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """Filter tasks by pet name and/or completion status.

        Args:
            pet_name: If given, only tasks for the pet with this name.
            completed: If True return only done tasks; False returns only pending.
                       None returns all.
        """
        pet_ids: Optional[set[str]] = None
        if pet_name is not None:
            pet_ids = {p.id for p in self.owner.pets if p.name.lower() == pet_name.lower()}

        result = []
        for t in self.tasks:
            if pet_ids is not None and t.pet_id not in pet_ids:
                continue
            if completed is not None and t.is_completed != completed:
                continue
            result.append(t)
        return result

    # ── Recurring tasks ───────────────────────────────────────────────────────

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task complete and, if recurring, queue its next occurrence.

        Returns the newly created next-occurrence Task, or None for one-off tasks.
        """
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task is None:
            return None

        task.mark_complete()

        if task.frequency in ("daily", "weekly"):
            next_task = Task(
                id=str(uuid.uuid4())[:8],
                pet_id=task.pet_id,
                name=task.name,
                description=task.description,
                duration_mins=task.duration_mins,
                frequency=task.frequency,
                priority=task.priority,
                due_time=task.due_time,   # same time, next cycle
                is_completed=False,
            )
            self.tasks.append(next_task)
            return next_task

        return None

    # ── Conflict detection ────────────────────────────────────────────────────

    def get_conflicts(self) -> list[str]:
        """Return a list of human-readable conflict warnings for overlapping tasks.

        Checks every pair of pending timed tasks. A conflict occurs when task A's
        end time (due_time + duration) overlaps task B's due_time.
        """
        timed = sorted(
            [t for t in self.tasks if t.due_time and not t.is_completed],
            key=lambda t: t.due_time,
        )

        def end_minutes(t: Task) -> int:
            return t.due_time.hour * 60 + t.due_time.minute + t.duration_mins

        def start_minutes(t: Task) -> int:
            return t.due_time.hour * 60 + t.due_time.minute

        warnings = []
        for i in range(len(timed) - 1):
            a, b = timed[i], timed[i + 1]
            if end_minutes(a) > start_minutes(b):
                pet_a = next((p.name for p in self.owner.pets if p.id == a.pet_id), "?")
                pet_b = next((p.name for p in self.owner.pets if p.id == b.pet_id), "?")
                a_end = time((end_minutes(a) // 60) % 24, end_minutes(a) % 60)
                warnings.append(
                    f"CONFLICT: '{a.name}' ({pet_a}) ends at "
                    f"{a_end.strftime('%I:%M %p')} but "
                    f"'{b.name}' ({pet_b}) starts at "
                    f"{b.due_time.strftime('%I:%M %p')}"
                )
        return warnings

    def check_conflicts(self) -> bool:
        """Return True if any pending tasks have overlapping time windows."""
        return len(self.get_conflicts()) > 0

    # ── Planning ──────────────────────────────────────────────────────────────

    def generate_daily_plan(self) -> list[Task]:
        """Return today's pending tasks sorted by priority (high first), then due time."""
        pending = [t for t in self.tasks if not t.is_completed]
        return sorted(
            pending,
            key=lambda t: (-t.priority, t.due_time or time(23, 59)),
        )

    def send_reminder(self, task: Task) -> None:
        """Print a reminder for a task (placeholder for real notification logic)."""
        pet_name = next(
            (p.name for p in self.owner.pets if p.id == task.pet_id), "Unknown pet"
        )
        due = task.due_time.strftime("%I:%M %p") if task.due_time else "soon"
        print(
            f"REMINDER [{self.owner.notification_preference.upper()}]: "
            f"'{task.name}' for {pet_name} is due at {due}."
        )
