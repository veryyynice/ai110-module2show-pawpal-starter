import uuid
from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state bootstrap ──────────────────────────────────────────────────
# Streamlit reruns the whole script on every interaction.
# We store the Owner and Scheduler in st.session_state so they survive reruns.
if "owner" not in st.session_state:
    st.session_state.owner = None       # created when the owner form is submitted
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ── Owner setup ──────────────────────────────────────────────────────────────
st.subheader("Owner")

if st.session_state.owner is None:
    with st.form("owner_form"):
        owner_name = st.text_input("Your name", value="Jordan")
        contact = st.text_input("Contact (email or phone)", value="jordan@email.com")
        notif = st.selectbox("Notification preference", ["app", "email", "sms"])
        submitted = st.form_submit_button("Save owner")
    if submitted:
        st.session_state.owner = Owner(
            name=owner_name,
            contact_info=contact,
            notification_preference=notif,
        )
        st.session_state.scheduler = Scheduler(st.session_state.owner)
        st.rerun()
else:
    owner: Owner = st.session_state.owner
    st.success(f"Owner: **{owner.name}** — notifications via *{owner.notification_preference}*")
    if st.button("Reset owner"):
        st.session_state.owner = None
        st.session_state.scheduler = None
        st.rerun()

# ── Pet management ───────────────────────────────────────────────────────────
if st.session_state.owner is not None:
    st.divider()
    st.subheader("Pets")

    owner: Owner = st.session_state.owner

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
        add_pet = st.form_submit_button("Add pet")

    if add_pet:
        new_pet = Pet(
            id=str(uuid.uuid4())[:8],
            name=pet_name,
            species=species,
            breed=breed,
            age_years=int(age),
            weight_kg=float(weight),
        )
        owner.add_pet(new_pet)
        st.rerun()

    if owner.pets:
        for pet in owner.pets:
            st.markdown(f"- **{pet.name}** — {pet.breed} {pet.species}, {pet.age_years}yr, {pet.weight_kg}kg")
    else:
        st.info("No pets yet. Add one above.")

# ── Task management ──────────────────────────────────────────────────────────
if st.session_state.owner and st.session_state.owner.pets:
    st.divider()
    st.subheader("Tasks")

    owner: Owner = st.session_state.owner
    scheduler: Scheduler = st.session_state.scheduler

    with st.form("add_task_form"):
        pet_options = {p.name: p for p in owner.pets}
        selected_pet_name = st.selectbox("Pet", list(pet_options.keys()))
        col1, col2, col3 = st.columns(3)
        with col1:
            task_name = st.text_input("Task", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", [1, 2, 3, 4, 5], index=2,
                                    format_func=lambda x: f"{x} — {'★'*x}")
        desc = st.text_input("Description (optional)", value="")
        due_hour = st.slider("Due hour", 0, 23, 8)
        due_min = st.selectbox("Due minute", [0, 15, 30, 45], index=0)
        add_task = st.form_submit_button("Add task")

    if add_task:
        selected_pet = pet_options[selected_pet_name]
        new_task = Task(
            id=str(uuid.uuid4())[:8],
            pet_id=selected_pet.id,
            name=task_name,
            description=desc,
            duration_mins=int(duration),
            frequency="daily",
            priority=int(priority),
            due_time=time(due_hour, due_min),
        )
        scheduler.add_task(new_task)
        st.rerun()

    if scheduler.tasks:
        rows = []
        for t in scheduler.tasks:
            pet = next((p for p in owner.pets if p.id == t.pet_id), None)
            rows.append({
                "Pet": pet.name if pet else "?",
                "Task": t.name,
                "Due": t.due_time.strftime("%I:%M %p") if t.due_time else "—",
                "Duration": f"{t.duration_mins} min",
                "Priority": t.priority,
                "Done": "✓" if t.is_completed else "○",
            })
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")

# ── Schedule generation ───────────────────────────────────────────────────────
if st.session_state.scheduler and st.session_state.scheduler.tasks:
    st.divider()
    st.subheader("Generate Schedule")

    scheduler: Scheduler = st.session_state.scheduler
    owner: Owner = st.session_state.owner

    if st.button("Generate schedule"):
        plan = scheduler.generate_daily_plan()
        conflicts = scheduler.check_conflicts()

        if conflicts:
            st.warning("⚠️ Scheduling conflict detected — two tasks overlap in time.")

        st.markdown("### Today's Plan")
        for i, task in enumerate(plan, 1):
            pet = next((p for p in owner.pets if p.id == task.pet_id), None)
            due = task.due_time.strftime("%I:%M %p") if task.due_time else "Anytime"
            st.markdown(
                f"**{i}. {task.name}** for _{pet.name if pet else '?'}_  \n"
                f"Due: {due} · {task.duration_mins} min · Priority {task.priority}"
            )
