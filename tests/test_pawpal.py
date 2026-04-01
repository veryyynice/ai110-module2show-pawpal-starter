from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_task(id="t1", pet_id="p1", priority=3, due_time=None,
              completed=False, frequency="daily", duration_mins=15):
    t = Task(
        id=id, pet_id=pet_id, name="Test Task", description="",
        duration_mins=duration_mins, frequency=frequency, priority=priority,
        due_time=due_time, is_completed=completed,
    )
    return t


def make_pet(id="p1", name="Buddy"):
    return Pet(id=id, name=name, species="dog", breed="Mutt", age_years=2, weight_kg=10)


def make_owner():
    return Owner(name="Sam", contact_info="sam@test.com")


def make_scheduler_with_pet(pet_name="Buddy"):
    owner = make_owner()
    pet = make_pet(name=pet_name)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    return scheduler, owner, pet


# ── Phase 2: core task tests ──────────────────────────────────────────────────

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
    t1 = make_task(id="t1", due_time=time(8, 0), duration_mins=60)
    t2 = make_task(id="t2", due_time=time(8, 30))
    scheduler.add_task(t1)
    scheduler.add_task(t2)
    assert scheduler.check_conflicts() is True


def test_check_conflicts_no_overlap():
    owner = make_owner()
    scheduler = Scheduler(owner)
    t1 = make_task(id="t1", due_time=time(8, 0), duration_mins=30)
    t2 = make_task(id="t2", due_time=time(9, 0))
    scheduler.add_task(t1)
    scheduler.add_task(t2)
    assert scheduler.check_conflicts() is False


# ── Phase 3: session-state / wiring tests ────────────────────────────────────

def test_owner_persists_pets_across_scheduler():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    assert scheduler.owner.pets[0].id == pet.id


def test_add_pet_to_owner_visible_in_scheduler():
    owner = make_owner()
    scheduler = Scheduler(owner)
    assert len(scheduler.owner.pets) == 0
    owner.add_pet(make_pet(id="p99"))
    assert len(scheduler.owner.pets) == 1


def test_remove_pet_from_owner():
    owner = make_owner()
    pet = make_pet(id="p1")
    owner.add_pet(pet)
    owner.remove_pet("p1")
    assert len(owner.pets) == 0


def test_task_linked_to_pet_via_pet_id():
    scheduler, owner, pet = make_scheduler_with_pet()
    task = make_task(id="t1", pet_id=pet.id)
    scheduler.add_task(task)
    pet_tasks = scheduler.get_tasks_for_pet(pet)
    assert len(pet_tasks) == 1
    assert pet_tasks[0].pet_id == pet.id


def test_generate_daily_plan_excludes_completed():
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", completed=False))
    scheduler.add_task(make_task(id="t2", completed=True))
    plan = scheduler.generate_daily_plan()
    assert all(not t.is_completed for t in plan)
    assert len(plan) == 1


# ── Phase 4: sorting, filtering, recurring, conflict messages ─────────────────

def test_sort_by_time_orders_ascending():
    """Tasks added out of order should come back sorted by due_time."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", due_time=time(15, 0)))
    scheduler.add_task(make_task(id="t2", due_time=time(8, 0)))
    scheduler.add_task(make_task(id="t3", due_time=time(12, 0)))
    sorted_tasks = scheduler.sort_by_time()
    times = [t.due_time for t in sorted_tasks]
    assert times == sorted(times)


def test_sort_by_time_no_due_time_goes_last():
    """Tasks with no due_time should sort after all timed tasks."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", due_time=None))
    scheduler.add_task(make_task(id="t2", due_time=time(9, 0)))
    sorted_tasks = scheduler.sort_by_time()
    assert sorted_tasks[0].id == "t2"
    assert sorted_tasks[-1].id == "t1"


def test_filter_by_pet_name():
    """filter_tasks(pet_name=...) should return only that pet's tasks."""
    scheduler, owner, pet = make_scheduler_with_pet(pet_name="Luna")
    other_pet = make_pet(id="p2", name="Milo")
    owner.add_pet(other_pet)
    scheduler.add_task(make_task(id="t1", pet_id=pet.id))
    scheduler.add_task(make_task(id="t2", pet_id=other_pet.id))
    result = scheduler.filter_tasks(pet_name="Luna")
    assert len(result) == 1
    assert result[0].pet_id == pet.id


def test_filter_by_completed_false():
    """filter_tasks(completed=False) returns only pending tasks."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", completed=False))
    scheduler.add_task(make_task(id="t2", completed=True))
    result = scheduler.filter_tasks(completed=False)
    assert len(result) == 1
    assert result[0].id == "t1"


def test_filter_by_completed_true():
    """filter_tasks(completed=True) returns only done tasks."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", completed=False))
    scheduler.add_task(make_task(id="t2", completed=True))
    result = scheduler.filter_tasks(completed=True)
    assert len(result) == 1
    assert result[0].id == "t2"


def test_complete_task_daily_creates_next_occurrence():
    """Completing a daily task should add a new pending task for the next cycle."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", frequency="daily", due_time=time(8, 0)))
    assert len(scheduler.tasks) == 1
    next_task = scheduler.complete_task("t1")
    assert len(scheduler.tasks) == 2
    assert next_task is not None
    assert next_task.is_completed is False
    assert next_task.frequency == "daily"


def test_complete_task_once_does_not_recur():
    """Completing a one-off task should NOT add a new occurrence."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", frequency="once"))
    next_task = scheduler.complete_task("t1")
    assert next_task is None
    assert len(scheduler.tasks) == 1


def test_complete_task_weekly_creates_next_occurrence():
    """Completing a weekly task should queue the next occurrence."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", frequency="weekly", due_time=time(10, 0)))
    next_task = scheduler.complete_task("t1")
    assert next_task is not None
    assert next_task.frequency == "weekly"


def test_complete_task_marks_original_done():
    """complete_task must also flip the original task's is_completed flag."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    scheduler.add_task(make_task(id="t1", frequency="daily"))
    scheduler.complete_task("t1")
    original = next(t for t in scheduler.tasks if t.id == "t1")
    assert original.is_completed is True


def test_get_conflicts_returns_warning_message():
    """get_conflicts should return a non-empty list with readable strings."""
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    t1 = make_task(id="t1", pet_id=pet.id, due_time=time(8, 0), duration_mins=60)
    t2 = make_task(id="t2", pet_id=pet.id, due_time=time(8, 30))
    scheduler.add_task(t1)
    scheduler.add_task(t2)
    warnings = scheduler.get_conflicts()
    assert len(warnings) > 0
    assert isinstance(warnings[0], str)
    assert "CONFLICT" in warnings[0]


def test_get_conflicts_empty_when_no_overlap():
    """get_conflicts returns an empty list when no tasks overlap."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    t1 = make_task(id="t1", due_time=time(8, 0), duration_mins=30)
    t2 = make_task(id="t2", due_time=time(9, 0))
    scheduler.add_task(t1)
    scheduler.add_task(t2)
    assert scheduler.get_conflicts() == []
