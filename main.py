from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    # --- Setup ---
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

    # --- Tasks ---
    scheduler.add_task(Task(
        id="t1", pet_id="p1", name="Morning Walk", description="30-min neighborhood walk",
        duration_mins=30, frequency="daily", priority=5, due_time=time(7, 30),
    ))
    scheduler.add_task(Task(
        id="t2", pet_id="p1", name="Evening Walk", description="15-min backyard walk",
        duration_mins=15, frequency="daily", priority=4, due_time=time(18, 0),
    ))
    scheduler.add_task(Task(
        id="t3", pet_id="p1", name="Grooming", description="Brush and bath — overdue!",
        duration_mins=45, frequency="weekly", priority=3, due_time=time(11, 0),
    ))
    scheduler.add_task(Task(
        id="t4", pet_id="p2", name="Inhaler", description="Administer asthma inhaler",
        duration_mins=5, frequency="daily", priority=5, due_time=time(8, 0),
    ))
    scheduler.add_task(Task(
        id="t5", pet_id="p2", name="Feeding", description="Wet food — half can",
        duration_mins=5, frequency="daily", priority=4, due_time=time(17, 30),
    ))

    # --- Print schedule ---
    plan = scheduler.generate_daily_plan()
    conflicts = scheduler.check_conflicts()

    print("=" * 45)
    print("       PAWPAL+ — TODAY'S SCHEDULE")
    print("=" * 45)

    for task in plan:
        pet = next(p for p in owner.pets if p.id == task.pet_id)
        due = task.due_time.strftime("%I:%M %p") if task.due_time else "Anytime"
        status = "✓" if task.is_completed else "○"
        print(f"  {status} [{due}] {pet.name}: {task.name} ({task.duration_mins} min) P{task.priority}")

    print("-" * 45)
    print(f"  Total tasks: {len(plan)}")
    print(f"  Conflicts detected: {'YES — review schedule!' if conflicts else 'None'}")
    print("=" * 45)

    # --- Demo: complete a task and send a reminder ---
    print()
    plan[0].mark_complete()
    print(f"Completed: '{plan[0].name}'")
    scheduler.send_reminder(plan[1])


if __name__ == "__main__":
    main()
