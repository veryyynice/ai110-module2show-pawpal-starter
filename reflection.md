# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
- Make sure everything is at least 3NF
Owner, Pet, Task, Manager (Task manager/driver/reminder)
Owners have a lot of requirements surrounding their availibility. I opted not to make a schedule or avaibility class to stick with 4 classes. 
Manager is kind of the driver that sends reminders, 
Owner owns pets and tasks
Manager completes tasks, updates info on owner, tasks, pets. 
Manager checks somehow if task is completed or not, maybe like completion bool or a end time timestampl. If the tasks is not yet comelted it sends a reminder before it needs to be completed. It also suggests certain things the pet needs. 
It also makaes daily schedule/plan depending on the things that are needed today/that day.
Manager visualizes that plan with reasoning. 
Have to have tests , thats seperate mostly for scheduling conflict fixing and keeping pet in top shape. 

 attributes and methods:
Pet:
days since last wash
days since trim of claws
allergy
disease, 
weight
age
pet_name
pet_id
race


Manager
pet_satisfaction
pet_generate daily report/plan
send condolensces
 archive pet()
 add/remove/edit pet()
 add/remove/edit task()


Owner
weekly schedule
work schedule
owner contact info
notification info like phone #
pet priorities 


Task
defaulty notification time 1 hour before its due 
task name
task descritpion
task duration


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

had to put days since groomed/trimmed uder pet class, 
it should belong to the pet. It's more clean and makes more sense. 

AI review caught two more issues:

1. **Removed `Scheduler.pets`** — `Owner` and `Scheduler` both stored a pets list, creating two sources of truth. If you added a pet to the owner, the scheduler wouldn't see it. Fixed by giving `Scheduler` a reference to the `Owner` instead, so pets always come from one place.

2. **Renamed `check_task_completion` → `get_incomplete_tasks`** — the original name was misleading; it sounded like it was checking *if* tasks were done, but it was supposed to return *which* tasks aren't done yet. Clearer name prevents confusion when implementing.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?


**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers task priority (1–5), due time, and completion status. Priority was weighted first because a missed high-priority task (like medication) is worse than a scheduling gap. Due time is the secondary sort key — if two tasks share the same priority, the earlier one comes first. Owner availability is stored but not enforced in scheduling; it was deprioritized as out of scope for this version.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

notifications are a hour proir to due date, unchangeable - not needed for scope
owners avaliblity is a list of available hours per week, not changable, not needed for scope.

`get_conflicts()` checks whether task A's *end time* (due_time + duration_mins) overlaps task B's *start time*, comparing only consecutive timed tasks after sorting. This misses non-adjacent conflicts (e.g., task A and task C overlap but task B sits between them in the list). A full O(n²) pairwise check would be more accurate, but for a personal pet care app with a small number of daily tasks, the sorted consecutive check is fast

**Recurring task tradeoff:** When a recurring task is completed, `complete_task()` immediately adds the next occurrence with the *same due_time*. This means the new task is effectively "tomorrow's"The tradeoff avoids adding a full date system to the data model, keeping the scope small while still demonstrating recurrence logic.
---


## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
UML brainstorming, generating class skeletons, reviewing the skeleton for bottlenecks (caught the duplicate pets list between Owner and Scheduler), fleshing out implementations, generating test cases, and writing docstrings

- What kinds of prompts or questions were most helpful?

"Why does this class own that class?" — exposes redundant relationships
"What edge cases should I test for X?" — surfaces things I hadn't thought of
"What's the tradeoff between approach A and B?" — useful for deciding between O(n²) conflict check vs. sorted consecutive check

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

Didn't accept Pets owning Tasks. In real life, why would Pets have tasks? It's the human's job to manage tasks for a pet. Keeping tasks in Scheduler also means one place to add, remove, filter, and sort — instead of scattering task management across every Pet object.

- How did you evaluate or verify what the AI suggested?

Ran the test suite after each change. If tests still pass, the refactor is safe. If a test breaks, the suggestion introduced a regression and I investigate before accepting it.
---

## 4. Testing and Verification

**a. What you tested**

The test suite (25 tests) covers:
- Task completion: `mark_complete()` flips status correctly and is idempotent
- Task CRUD: add/remove changes count correctly
- Filtering: by pet name, by completion status, combined
- Sorting: `sort_by_time()` returns chronological order; tasks with no time go last
- Recurring tasks: daily/weekly tasks spawn a new pending occurrence on completion; one-off tasks do not
- Conflict detection: `get_conflicts()` returns readable warning strings for overlapping tasks; empty list when no overlap
- Daily plan: excludes completed tasks, sorts by priority then time

**b. Confidence**

(4/5) — The core happy paths and the main edge cases are covered. Edge cases to test next if given more time:
- Tasks that span midnight (e.g., due 11:45 PM with 30-min duration)
- Owner with zero pets / scheduler with zero tasks (empty state)
- Completing a task that doesn't exist (invalid ID passed to `complete_task`)

---

## 5. Reflection

**a. What went well**

The test-driven approach worked really well. Writing tests for each checkpoint meant I could refactor confidently — every time AI suggested a change (like renaming `check_task_completion` to `get_incomplete_tasks`), the test suite immediately told me whether the change broke anything

**b. What you would improve**

If given another iteration, I'd promote `due_time` from `time` to `datetime` so recurring tasks could properly schedule for tomorrow instead of just carrying the same `time` value. 

**c. Key takeaway**

AI is best used as a reviewer, not as a code generator you accept blindly. The most valuable moments were when AI spotted the duplicate `pets` list across `Owner` and `Scheduler`
