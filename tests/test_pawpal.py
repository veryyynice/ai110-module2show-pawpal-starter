from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler


def make_task(id="t1", pet_id="p1", priority=3, due_time=None, completed=False):
    t = Task(
        id=id, pet_id=pet_id, name="Test Task", description="",
        duration_mins=15, frequency="daily", priority=priority,
        due_time=due_time, is_completed=completed,
    )
    return t


def make_pet(id="p1"):
    return Pet(id=id, name="Buddy", species="dog", breed="Mutt", age_years=2, weight_kg=10)


def make_owner():
    return Owner(name="Sam", contact_info="sam@test.com")


# --- Task tests ---

def test_mark_complete_changes_status():
    task = make_task()
    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_mark_complete_is_idempotent():
    task = make_task()
    task.mark_complete()
    task.mark_complete()
    assert task.is_completed is True


# --- Scheduler / Pet task count tests ---

def test_add_task_increases_count():
    owner = make_owner()
    scheduler = Scheduler(owner)
    assert len(scheduler.tasks) == 0
    scheduler.add_task(make_task())
    assert len(scheduler.tasks) == 1


def test_add_multiple_tasks():
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1"))
    scheduler.add_task(make_task(id="t2"))
    assert len(scheduler.tasks) == 2


def test_remove_task_decreases_count():
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1"))
    scheduler.remove_task("t1")
    assert len(scheduler.tasks) == 0


def test_get_incomplete_tasks_filters_correctly():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", completed=False))
    scheduler.add_task(make_task(id="t2", completed=True))
    incomplete = scheduler.get_incomplete_tasks(pet)
    assert len(incomplete) == 1
    assert incomplete[0].id == "t1"


def test_generate_daily_plan_sorted_by_priority():
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", priority=1))
    scheduler.add_task(make_task(id="t2", priority=5))
    scheduler.add_task(make_task(id="t3", priority=3))
    plan = scheduler.generate_daily_plan()
    priorities = [t.priority for t in plan]
    assert priorities == sorted(priorities, reverse=True)


def test_check_conflicts_detects_overlap():
    owner = make_owner()
    scheduler = Scheduler(owner)
    # t1: starts 08:00, lasts 60 min → ends 09:00
    # t2: starts 08:30 → overlaps
    t1 = make_task(id="t1", due_time=time(8, 0))
    t1.duration_mins = 60
    t2 = make_task(id="t2", due_time=time(8, 30))
    scheduler.add_task(t1)
    scheduler.add_task(t2)
    assert scheduler.check_conflicts() is True


def test_check_conflicts_no_overlap():
    owner = make_owner()
    scheduler = Scheduler(owner)
    t1 = make_task(id="t1", due_time=time(8, 0))
    t1.duration_mins = 30
    t2 = make_task(id="t2", due_time=time(9, 0))
    scheduler.add_task(t1)
    scheduler.add_task(t2)
    assert scheduler.check_conflicts() is False


# ── Checkpoint: session state / wiring tests ─────────────────────────────────

def test_owner_persists_pets_across_scheduler():
    """Owner is the single source of truth — Scheduler reads pets from Owner."""
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    assert scheduler.owner.pets[0].id == pet.id


def test_add_pet_to_owner_visible_in_scheduler():
    """Adding a pet after Scheduler is created is immediately visible."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    assert len(scheduler.owner.pets) == 0
    owner.add_pet(make_pet(id="p99"))
    assert len(scheduler.owner.pets) == 1


def test_remove_pet_from_owner():
    """remove_pet correctly removes by id."""
    owner = make_owner()
    pet = make_pet(id="p1")
    owner.add_pet(pet)
    owner.remove_pet("p1")
    assert len(owner.pets) == 0


def test_task_linked_to_pet_via_pet_id():
    """Task's pet_id matches the pet it was added for."""
    owner = make_owner()
    pet = make_pet(id="p1")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    task = make_task(id="t1", pet_id="p1")
    scheduler.add_task(task)
    pet_tasks = scheduler.get_tasks_for_pet(pet)
    assert len(pet_tasks) == 1
    assert pet_tasks[0].pet_id == pet.id


def test_generate_daily_plan_excludes_completed():
    """Completed tasks are not included in the daily plan."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", completed=False))
    scheduler.add_task(make_task(id="t2", completed=True))
    plan = scheduler.generate_daily_plan()
    assert all(not t.is_completed for t in plan)
    assert len(plan) == 1
