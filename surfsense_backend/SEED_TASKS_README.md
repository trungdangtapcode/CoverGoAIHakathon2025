# 🎯 Task Seeder - Work Mode Demo

Scripts để tạo fake tasks cho demo Work Mode.

---

## 📋 3 Options Available

### 1️⃣ Quick Demo Seed (Recommended for Demo)
**File**: `quick_seed_demo.py`

Tạo **10 tasks** được chọn sẵn với mix tốt:
- 2 URGENT (1 overdue)
- 3 HIGH
- 3 MEDIUM
- 2 LOW

**Usage:**
```bash
cd surfsense_backend
source .venv/bin/activate

python quick_seed_demo.py <search_space_id> <user_id>
```

**Example:**
```bash
python quick_seed_demo.py 1 550e8400-e29b-41d4-a716-446655440000
```

**Output:**
```
🎯 Creating 10 demo tasks for Work Mode...

   [ 1] 🔴 Fix memory leak in Celery workers                      Due: Oct 25 ⚠️ OVERDUE
   [ 2] 🔴 Fix authentication bug in production                   Due: Oct 26
   [ 3] 🟠 Database migration for Work Mode                       Due: Oct 27
   ...

✅ Demo tasks created successfully!
```

---

### 2️⃣ Interactive Selector
**File**: `seed_tasks_interactive.py`

Cho phép bạn **chọn tasks muốn tạo** từ catalog 15 tasks.

**Usage:**
```bash
python seed_tasks_interactive.py
```

**Features:**
- Xem menu với 15 task options
- Chọn theo ID: `1,3,5,7`
- Chọn theo priority: `urgent`, `high`
- Chọn theo category: `bugs`, `features`
- Chọn tất cả: `all`

**Example Session:**
```
📋 Available Tasks
ID    Priority    Category        Title                                              Due
1     🔴 URGENT   Bug Fix         Fix critical authentication bug in production      Oct 26
2     🟠 HIGH     Feature         Implement user profile settings page               Oct 28
...

📝 Selection Options:
  • Enter task IDs (comma-separated): e.g., 1,3,5,7
  • Enter 'all' to select all tasks
  • Enter 'urgent' for URGENT priority tasks only

👉 Your selection: 1,7,13

✅ Successfully created 3 tasks!
```

---

### 3️⃣ Automatic Seed
**File**: `seed_tasks.py`

Tự động tạo **N tasks đầu tiên** từ catalog.

**Usage:**
```bash
python seed_tasks.py --search_space_id 1 --user_id <uuid> --count 10
```

**Options:**
- `--search_space_id`: Required, ID của search space
- `--user_id`: Required, UUID của user
- `--count`: Optional, số lượng tasks (default: 10, max: 15)

**Example:**
```bash
python seed_tasks.py \
  --search_space_id 1 \
  --user_id 550e8400-e29b-41d4-a716-446655440000 \
  --count 12
```

---

## 🔍 How to Get Search Space ID & User ID

### Get Search Space ID:
```bash
# Option 1: From browser URL
# Navigate to: http://localhost:3000/dashboard/1/work
# The number "1" is your search_space_id

# Option 2: Query database
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
psql -U postgres -d surfsense -c "SELECT id, name FROM search_spaces;"
```

### Get User ID:
```bash
# Query database
psql -U postgres -d surfsense -c "SELECT id, email FROM \"user\";"
```

---

## 📊 Task Categories in Catalog

| Category       | Count | Description                        |
|----------------|-------|------------------------------------|
| Bug Fix        | 2     | Critical bugs needing immediate fix|
| Feature        | 5     | New features to implement          |
| Performance    | 2     | Performance optimization tasks     |
| Testing        | 1     | Unit/integration tests             |
| Documentation  | 1     | API docs and guides                |
| Database       | 1     | Schema migrations                  |
| Integration    | 1     | Third-party integrations           |
| UX             | 2     | User experience improvements       |
| Refactoring    | 1     | Code quality improvements          |

---

## 🎨 Priority Distribution

Tasks được design với realistic priority mix:

- **🔴 URGENT** (3 tasks): Critical bugs, security issues
- **🟠 HIGH** (5 tasks): Important features, breaking changes
- **🟡 MEDIUM** (5 tasks): Nice-to-have features, improvements
- **🟢 LOW** (2 tasks): Refactoring, minor improvements

---

## ⚠️ Important Notes

1. **Clear Existing Tasks**: Scripts sẽ **XÓA** tất cả tasks hiện tại trong search space trước khi tạo mới (chỉ cho `seed_tasks.py`)

2. **User Ownership**: Tasks sẽ được assign cho user_id bạn cung cấp

3. **Due Dates**: Tasks có due dates realistic:
   - Overdue: -1 day
   - Today: 0 days
   - Future: 1-21 days from now

4. **External IDs**: Tasks có fake Linear IDs (`TASK-001`, `DEMO-001`, etc.)

---

## 🚀 Quick Start (Fastest Way)

```bash
# 1. Get your user ID
psql -U postgres -d surfsense -c "SELECT id FROM \"user\" LIMIT 1;"

# 2. Run quick seed (assumes search_space_id = 1)
cd surfsense_backend
source .venv/bin/activate
python quick_seed_demo.py 1 <your_user_id_here>

# 3. Open Work Mode in browser
# http://localhost:3000/dashboard/1/work
```

Done! 🎉

---

## 🧹 Clear All Tasks

To remove all seeded tasks:

```bash
psql -U postgres -d surfsense -c "DELETE FROM tasks WHERE search_space_id = 1;"
```

---

## 💡 Tips for Demo

1. **Use Quick Seed** for fastest setup
2. **Mix of priorities** makes demo realistic
3. **Overdue task** shows urgency highlighting
4. **Clear tasks between demos** to reset state

Happy demo-ing! 🚀
