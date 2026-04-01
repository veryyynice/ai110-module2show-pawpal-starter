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


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

notifications are a hour proir to due date , unchangeable - not needed for scope
owners avaliblity is a list of available hours per week , not changabloe, not needed for scope. 
---


## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
double checking some decision it made for UML and seeing that i had some redudancis like it tried to make pets have tasks
- What kinds of prompts or questions were most helpful?
why does class1 have/own class2 
how would TimeBlock be implemtend 
**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
Didn't except Pets owning Tasks. In real life, why would Pets have tasks, it's the humans job. 
- How did you evaluate or verify what the AI suggested?
checked the commit changed. 
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
efficient/safe, schedluing, like not during lunch or at earliest, latest possible times. 

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
