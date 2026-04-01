from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler


def print_schedule(plan: list[Task], owner: Owner, title: str = "TODAY'S SCHEDULE") -> None:
    """Print a formatted schedule to the terminal."""
    width = 50
    print("=" * width)
    print(f"  PAWPAL+ — {title}".center(width))
    print("=" * width)
    for task in plan:
        pet = next((p for p in owner.pets if p.id == task.pet_id), None)
        due = task.due_time.strftime("%I:%M %p") if task.due_time else "Anytime"
        status = "✓" if task.is_completed else "○"
        print(f"  {status} [{due}] {pet.name if pet else '?'}: {task.name} "
              f"({task.duration_mins} min) P{task.priority}")
    print("-" * width)
    print(f"  Total: {len(plan)} tasks")
    print("=" * width)


def main():
    # ── Setup ─────────────────────────────────────────────────────────────────
    owner = Owner(
        name="Alex",
        contact_info="alex@email.com",
        available_hours=[(time(7, 0), time(20, 0))],
        notification_preference="app",
    )

    luna = Pet(id="p1", name="Luna", species="dog", breed="Golden Retriever",
               age_years=3, weight_kg=28.5, days_since_groomed=12)
    milo = Pet(id="p2", name="Milo", species="cat", breed="Tabby",
               age_years=5, weight_kg=4.2, conditions=["asthma"])

    owner.add_pet(luna)
    owner.add_pet(milo)

    scheduler = Scheduler(owner)

    # Tasks added intentionally out of time order to demo sort_by_time
    scheduler.add_task(Task(
        id="t1", pet_id="p1", name="Evening Walk", description="15-min backyard walk",
        duration_mins=15, frequency="daily", priority=4, due_time=time(18, 0),
    ))
    scheduler.add_task(Task(
        id="t2", pet_id="p2", name="Feeding", description="Wet food — half can",
        duration_mins=5, frequency="daily", priority=4, due_time=time(17, 30),
    ))
    scheduler.add_task(Task(
        id="t3", pet_id="p1", name="Grooming", description="Brush and bath",
        duration_mins=45, frequency="weekly", priority=3, due_time=time(11, 0),
    ))
    scheduler.add_task(Task(
        id="t4", pet_id="p2", name="Inhaler", description="Asthma inhaler",
        duration_mins=5, frequency="daily", priority=5, due_time=time(8, 0),
    ))
    scheduler.add_task(Task(
        id="t5", pet_id="p1", name="Morning Walk", description="30-min neighborhood walk",
        duration_mins=30, frequency="daily", priority=5, due_time=time(7, 30),
    ))

    # ── 1. Sorted by time ─────────────────────────────────────────────────────
    print("\n── Sorted by time (not priority) ──")
    by_time = scheduler.sort_by_time()
    for t in by_time:
        pet = next(p for p in owner.pets if p.id == t.pet_id)
        due = t.due_time.strftime("%I:%M %p") if t.due_time else "Anytime"
        print(f"  [{due}] {pet.name}: {t.name}")

    # ── 2. Filter by pet ──────────────────────────────────────────────────────
    print("\n── Luna's tasks only ──")
    luna_tasks = scheduler.filter_tasks(pet_name="Luna")
    for t in luna_tasks:
        print(f"  {t.name} (P{t.priority})")

    # ── 3. Full priority plan ─────────────────────────────────────────────────
    print()
    plan = scheduler.generate_daily_plan()
    print_schedule(plan, owner)

    # ── 4. Conflict detection ─────────────────────────────────────────────────
    print("\n── Conflict check ──")
    conflicts = scheduler.get_conflicts()
    if conflicts:
        for w in conflicts:
            print(f"  ⚠️  {w}")
    else:
        print("  No conflicts detected.")

    # ── 5. Introduce a conflict and re-check ──────────────────────────────────
    scheduler.add_task(Task(
        id="t6", pet_id="p1", name="Vet Call", description="Phone consult",
        duration_mins=20, frequency="once", priority=5, due_time=time(7, 40),
    ))
    print("\n── After adding overlapping task (Vet Call @ 07:40) ──")
    for w in scheduler.get_conflicts():
        print(f"  ⚠️  {w}")

    # ── 6. Complete a recurring task → next occurrence auto-added ─────────────
    print("\n── Recurring task demo ──")
    print(f"  Tasks before completing Morning Walk: {len(scheduler.tasks)}")
    next_task = scheduler.complete_task("t5")
    print(f"  Tasks after: {len(scheduler.tasks)}")
    if next_task:
        due = next_task.due_time.strftime("%I:%M %p") if next_task.due_time else "?"
        print(f"  Next occurrence queued: '{next_task.name}' @ {due} (id={next_task.id})")

    # ── 7. Filter pending only ────────────────────────────────────────────────
    print("\n── Pending tasks only ──")
    pending = scheduler.filter_tasks(completed=False)
    for t in pending:
        pet = next(p for p in owner.pets if p.id == t.pet_id)
        print(f"  {pet.name}: {t.name}")


if __name__ == "__main__":
    main()
