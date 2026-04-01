import uuid
from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A smart pet care planner — schedule, sort, and never miss a task.")

# ── Session state bootstrap ───────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ── Owner setup ───────────────────────────────────────────────────────────────
st.subheader("Owner")

if st.session_state.owner is None:
    with st.form("owner_form"):
        owner_name = st.text_input("Your name", value="Jordan")
        contact = st.text_input("Contact (email or phone)", value="jordan@email.com")
        notif = st.selectbox("Notification preference", ["app", "email", "sms"])
        if st.form_submit_button("Save owner"):
            st.session_state.owner = Owner(
                name=owner_name,
                contact_info=contact,
                notification_preference=notif,
            )
            st.session_state.scheduler = Scheduler(st.session_state.owner)
            st.rerun()
else:
    owner: Owner = st.session_state.owner
    st.success(f"**{owner.name}** — notifications via *{owner.notification_preference}*")
    if st.button("Reset owner"):
        st.session_state.owner = None
        st.session_state.scheduler = None
        st.rerun()

# ── Pet management ────────────────────────────────────────────────────────────
if st.session_state.owner:
    owner: Owner = st.session_state.owner
    st.divider()
    st.subheader("Pets")

    with st.form("add_pet_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_name = st.text_input("Pet name", value="Mochi")
        with col2:
            species = st.selectbox("Species", ["dog", "cat", "other"])
        with col3:
            breed = st.text_input("Breed", value="Mixed")
        col4, col5 = st.columns(2)
        with col4:
            age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        with col5:
            weight = st.number_input("Weight (kg)", min_value=0.1, max_value=100.0, value=5.0)
        if st.form_submit_button("Add pet"):
            owner.add_pet(Pet(
                id=str(uuid.uuid4())[:8],
                name=pet_name, species=species, breed=breed,
                age_years=int(age), weight_kg=float(weight),
            ))
            st.rerun()

    if owner.pets:
        for pet in owner.pets:
            st.markdown(f"- **{pet.name}** — {pet.breed} {pet.species}, {pet.age_years}yr, {pet.weight_kg}kg")
    else:
        st.info("No pets yet. Add one above.")

# ── Task management ───────────────────────────────────────────────────────────
if st.session_state.owner and st.session_state.owner.pets:
    owner: Owner = st.session_state.owner
    scheduler: Scheduler = st.session_state.scheduler
    st.divider()
    st.subheader("Tasks")

    with st.form("add_task_form"):
        pet_options = {p.name: p for p in owner.pets}
        col1, col2 = st.columns(2)
        with col1:
            selected_pet_name = st.selectbox("Pet", list(pet_options.keys()))
            task_name = st.text_input("Task name", value="Morning walk")
            desc = st.text_input("Description (optional)", value="")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", [5, 4, 3, 2, 1],
                                    format_func=lambda x: f"{'★'*x}{'☆'*(5-x)}  ({x})")
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        due_col1, due_col2 = st.columns(2)
        with due_col1:
            due_hour = st.slider("Due hour", 0, 23, 8)
        with due_col2:
            due_min = st.selectbox("Due minute", [0, 15, 30, 45])
        if st.form_submit_button("Add task"):
            scheduler.add_task(Task(
                id=str(uuid.uuid4())[:8],
                pet_id=pet_options[selected_pet_name].id,
                name=task_name, description=desc,
                duration_mins=int(duration), frequency=frequency,
                priority=int(priority),
                due_time=time(due_hour, due_min),
            ))
            st.rerun()

# ── Schedule view ─────────────────────────────────────────────────────────────
if st.session_state.scheduler and st.session_state.scheduler.tasks:
    owner: Owner = st.session_state.owner
    scheduler: Scheduler = st.session_state.scheduler
    st.divider()
    st.subheader("Schedule")

    # Filter controls
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox(
            "Filter by pet", ["All pets"] + [p.name for p in owner.pets]
        )
    with col2:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Done"])
    with col3:
        sort_mode = st.selectbox("Sort by", ["Priority", "Time"])

    # Apply filters
    pet_name_arg = None if pet_filter == "All pets" else pet_filter
    completed_arg = None
    if status_filter == "Pending":
        completed_arg = False
    elif status_filter == "Done":
        completed_arg = True

    filtered = scheduler.filter_tasks(pet_name=pet_name_arg, completed=completed_arg)

    if sort_mode == "Time":
        display_tasks = scheduler.sort_by_time(filtered)
    else:
        display_tasks = sorted(filtered, key=lambda t: (-t.priority, t.due_time or time(23, 59)))

    # Conflict warnings
    conflicts = scheduler.get_conflicts()
    if conflicts:
        for w in conflicts:
            st.warning(f"⚠️ {w}")

    # Task table
    if display_tasks:
        rows = []
        for t in display_tasks:
            pet = next((p for p in owner.pets if p.id == t.pet_id), None)
            rows.append({
                "Pet": pet.name if pet else "?",
                "Task": t.name,
                "Due": t.due_time.strftime("%I:%M %p") if t.due_time else "—",
                "Duration": f"{t.duration_mins} min",
                "Priority": "★" * t.priority,
                "Freq": t.frequency,
                "Status": "✓ Done" if t.is_completed else "○ Pending",
            })
        st.table(rows)
    else:
        st.info("No tasks match the current filters.")

    # Complete a task
    st.divider()
    st.subheader("Complete a Task")
    pending_tasks = scheduler.filter_tasks(completed=False)
    if pending_tasks:
        task_options = {f"{t.name} (id: {t.id})": t.id for t in pending_tasks}
        chosen = st.selectbox("Select task to complete", list(task_options.keys()))
        if st.button("Mark complete"):
            next_task = scheduler.complete_task(task_options[chosen])
            if next_task:
                st.success(f"Done! Next '{next_task.name}' scheduled (id: {next_task.id})")
            else:
                st.success("Task marked complete.")
            st.rerun()
    else:
        st.success("All tasks are complete!")

    # Generate plan
    st.divider()
    if st.button("Generate priority plan"):
        plan = scheduler.generate_daily_plan()
        st.markdown("### Today's Plan (priority order)")
        for i, task in enumerate(plan, 1):
            pet = next((p for p in owner.pets if p.id == task.pet_id), None)
            due = task.due_time.strftime("%I:%M %p") if task.due_time else "Anytime"
            st.markdown(
                f"**{i}.** {task.name} for _{pet.name if pet else '?'}_  \n"
                f"Due: {due} · {task.duration_mins} min · {'★' * task.priority} · {task.frequency}"
            )
