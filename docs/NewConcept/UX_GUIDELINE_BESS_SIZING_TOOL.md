# BESS & DG Sizing Tool — UX Guideline

**Version:** 1.0  
**Status:** DRAFT FOR REVIEW  
**Created:** 2025-12-02  
**Purpose:** Define user experience architecture before UI implementation

---

## 1. Executive Summary

### 1.1 The Core Problem

Investment analysts currently use fragmented Excel workflows to size BESS and DG systems. The experience is:

- **Disconnected:** Input in one sheet, results in another, constant navigation
- **Dead feedback:** Change a number → re-run → navigate to results → repeat
- **No comparison:** Evaluating alternatives requires manual side-by-side work
- **Invisible logic:** Dispatch rules exist in formulas, not visible to user

### 1.2 The UX Goal

Create a tight feedback loop where analysts can:

1. Describe their system in plain terms (not technical templates)
2. See sizing results immediately
3. Compare alternatives effortlessly
4. Understand dispatch logic visually

### 1.3 Design Principles

| Principle | Meaning |
|-----------|---------|
| **Constraints, not templates** | Users describe what they want. System picks the algorithm. |
| **Three numbers matter** | Delivery %, Wastage %, BESS Size — always visible, always prominent |
| **Progressive disclosure** | Simple first, advanced on demand |
| **Comparison is core** | Not a feature — a primary workflow |
| **Show the machine** | Dispatch logic should be visible, not hidden in code |

---

## 2. User Profile

### 2.1 Primary User

| Attribute | Description |
|-----------|-------------|
| **Role** | Investment analyst |
| **Frequency** | Daily use |
| **Device** | Laptop (limited screen space) |
| **Technical level** | Comfortable with Excel, understands energy concepts, not a programmer |
| **Context** | Site evaluation, cold selling offers, customer-specific proposals |

### 2.2 User Goals

| Goal | Priority |
|------|----------|
| Get sizing recommendation quickly | HIGH |
| Compare different configurations | HIGH |
| Understand why a configuration performs well/poorly | MEDIUM |
| Export results for proposals/presentations | MEDIUM |
| Explore "what if" scenarios | MEDIUM |

### 2.3 User Frustrations (Current State)

| Frustration | Impact |
|-------------|--------|
| "I wish I could change a number and see it update live" | Slows iteration |
| "I have to flip between sheets constantly" | Breaks focus |
| "I can't easily compare two setups" | Reduces confidence |
| "I don't really understand when DG kicks in" | Black box feeling |

---

## 3. Mental Model

### 3.1 The Shift

**OLD (Engineer's Model):**
```
Select Template → Configure Parameters → Run Simulation → View Results
```

**NEW (User's Model):**
```
Describe My System → Set My Rules → See What Works → Compare Options
```

### 3.2 User Language vs. System Language

| User Says | System Understands |
|-----------|-------------------|
| "I have solar, battery, and a generator" | Topology C (Solar + BESS + DG) |
| "Generator can't run at night — noise rules" | Template 5 (DG Day Charge) |
| "Generator should only start when battery is low" | SoC-triggered DG (Templates 4, 5, 6) |
| "I want the battery charged from solar only" | `dg_charges_bess = No` |
| "Generator runs continuously when on" | `dg_running_mode = Full Capacity` |

### 3.3 Template Selection Logic (Hidden from User)

The system infers the correct template from user answers:

```
Q1: Do you have a diesel/gas generator (DG)?
    └── No  → TEMPLATE 0 (Solar + BESS Only)
    └── Yes → Continue...

Q2: When is DG allowed to operate?
    └── Anytime (no restrictions)     → Continue to Q3a
    └── Day only (silent nights)      → TEMPLATE 5
    └── Night only (green days)       → Continue to Q3b
    └── Custom blackout hours         → TEMPLATE 3

Q3a: What triggers DG? (Anytime operation)
    └── When load can't be met        → TEMPLATE 1 (Green Priority)
    └── When battery gets low (SoC)   → TEMPLATE 4 (Emergency Only)

Q3b: What triggers DG? (Night only)
    └── Start of night (proactive)    → TEMPLATE 2 (Night Charge)
    └── When battery gets low (SoC)   → TEMPLATE 6 (Night SoC Trigger)
```

**UI shows:** "Dispatch Strategy: Green Priority" (informational, not editable)

---

## 4. Information Architecture

### 4.1 Screen Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BESS SIZING TOOL                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │  STEP 1  │───▶│  STEP 2  │───▶│  STEP 3  │───▶│  STEP 4  │     │
│   │  Setup   │    │  Rules   │    │  Sizing  │    │ Results  │     │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│        │                                               │            │
│        │                                               ▼            │
│        │                                        ┌──────────┐        │
│        │                                        │  Detail  │        │
│        │                                        │   View   │        │
│        │                                        └──────────┘        │
│        │                                               │            │
│        ▼                                               ▼            │
│   ┌──────────┐                                  ┌──────────┐        │
│   │  Saved   │◀────────────────────────────────▶│ Compare  │        │
│   │ Scenarios│                                  │   View   │        │
│   └──────────┘                                  └──────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Screen Definitions

| Screen | Purpose | Entry Points |
|--------|---------|--------------|
| **Step 1: Setup** | Upload/define load and solar profiles; set BESS and DG parameters | App start, "New Scenario" |
| **Step 2: Rules** | Define dispatch constraints (→ template inference) | Step 1 completion |
| **Step 3: Sizing** | Define sizing ranges (capacity, duration, DG sizes) | Step 2 completion |
| **Step 4: Results** | Comparison table of all configurations | Simulation completion |
| **Detail View** | Deep dive on single configuration | Click row in Results |
| **Compare View** | Side-by-side of 2-3 configurations | Select rows + "Compare" |
| **Saved Scenarios** | List of previously saved scenarios | Sidebar/menu |

---

## 5. Screen Specifications

### 5.1 Step 1: Setup

**Purpose:** Define the energy system being evaluated

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1 OF 4: SYSTEM SETUP                          [Next →]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LOAD PROFILE                                           │   │
│  │  ○ Upload CSV                                           │   │
│  │  ○ Use Load Builder                                     │   │
│  │     └── [Constant] [Day Only] [Night Only] [Custom]     │   │
│  │  Preview: [sparkline or summary]                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SOLAR PROFILE                                          │   │
│  │  ○ Upload CSV                                           │   │
│  │  Installed Capacity: [____] MWp                         │   │
│  │  Preview: [sparkline or summary]                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  BATTERY (BESS)                                         │   │
│  │  Round-trip Efficiency: [85] %                          │   │
│  │  Min State of Charge:   [10] %                          │   │
│  │  Max State of Charge:   [90] %                          │   │
│  │  Initial SoC:           [50] %                          │   │
│  │  ▼ Advanced (cycle limits)                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GENERATOR (DG)                                         │   │
│  │  ☑ Include generator in system                          │   │
│  │  └── (enabled only if checked)                          │   │
│  │      Min Stable Load: [30] %                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Behavior:**

| Element | Behavior |
|---------|----------|
| Load Profile toggle | Switches between CSV upload and Load Builder |
| Load Builder | Modal or inline options: Constant (MW), Day Only (hours, MW), Night Only, Custom windows |
| Solar CSV | Standard file upload; validates 8760 rows |
| BESS Advanced | Collapsed by default; reveals cycle limit, enforce toggle |
| DG checkbox | If unchecked, Step 2 simplified (no DG rules), Template 0 auto-selected |
| Next button | Validates required fields, proceeds to Step 2 |

**Validation:**
- Load profile: Required, 8760 values, non-negative
- Solar profile: Required, 8760 values, non-negative
- Solar capacity: Required, positive
- BESS efficiency: 0-100%
- BESS SoC bounds: min < max, both within 0-100%

---

### 5.2 Step 2: Dispatch Rules

**Purpose:** Define constraints that determine dispatch behavior (template inference)

**Layout (with DG):**
```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2 OF 4: DISPATCH RULES                [← Back] [Next →]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  How should your system operate?                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. WHEN CAN THE GENERATOR RUN?                         │   │
│  │                                                         │   │
│  │  ○ Anytime (no restrictions)                            │   │
│  │  ○ Day only (nights must be silent)                     │   │
│  │  ○ Night only (days must be green)                      │   │
│  │  ○ Custom blackout window                               │   │
│  │       └── Blackout from [__:__] to [__:__]              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  2. WHAT TRIGGERS THE GENERATOR?                        │   │
│  │                                                         │   │
│  │  ○ When battery + solar can't meet load (reactive)      │   │
│  │  ○ When battery charge drops below threshold (SoC)      │   │
│  │       └── Turn ON at [30] % SoC                         │   │
│  │       └── Turn OFF at [80] % SoC                        │   │
│  │  ○ At start of allowed window (proactive charging)      │   │
│  │       └── Charge until [90] % SoC                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  3. CAN THE GENERATOR CHARGE THE BATTERY?               │   │
│  │                                                         │   │
│  │  ○ No — battery charges from solar only                 │   │
│  │  ○ Yes — excess generator power can charge battery      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  DISPATCH STRATEGY SELECTED                             │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  🔋 Green Priority                              │    │   │
│  │  │  Solar → Battery → Generator → Unserved         │    │   │
│  │  │  Generator runs only when battery depleted      │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Layout (no DG — simplified):**
```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2 OF 4: DISPATCH RULES                [← Back] [Next →]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  DISPATCH STRATEGY                                      │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  ☀️ Solar + Battery Only                        │    │   │
│  │  │  Solar → Battery → Unserved                     │    │   │
│  │  │  No generator in this configuration             │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  No additional rules needed.                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Behavior:**

| Element | Behavior |
|---------|----------|
| Q1 options | Radio buttons; selecting "Custom blackout" reveals time inputs |
| Q2 options | Radio buttons; some options reveal threshold inputs |
| Q2 visibility | Options filtered based on Q1 (e.g., "proactive" only for night-only) |
| Q3 options | Radio buttons |
| Strategy card | Updates in real-time as user answers questions |
| Strategy card | Shows template name + merit order + one-line description |

**Template Inference Matrix:**

| Q1: When | Q2: Trigger | → Template |
|----------|-------------|------------|
| Anytime | Reactive | 1 (Green Priority) |
| Anytime | SoC-based | 4 (Emergency Only) |
| Day only | SoC-based | 5 (DG Day Charge) |
| Night only | Proactive | 2 (DG Night Charge) |
| Night only | SoC-based | 6 (DG Night SoC Trigger) |
| Custom blackout | Reactive | 3 (DG Blackout Window) |

**Validation:**
- If SoC-based: ON threshold < OFF threshold
- If SoC-based: ON threshold ≥ BESS min_soc
- If SoC-based: OFF threshold ≤ BESS max_soc
- If custom blackout: start ≠ end
- Warn if deadband < 20%

---

### 5.3 Step 3: Sizing Range

**Purpose:** Define what configurations to simulate

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3 OF 4: SIZING RANGE                  [← Back] [Run →]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  MODE                                                   │   │
│  │  ○ Sizing Mode — test range of configurations           │   │
│  │  ○ Fixed Mode — test single configuration               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  BATTERY CAPACITY RANGE                                 │   │
│  │  From: [50] MWh   To: [200] MWh   Step: [25] MWh        │   │
│  │                                                         │   │
│  │  DURATION CLASSES (auto-calculated power)               │   │
│  │  ☑ 1-hour  ☑ 2-hour  ☑ 4-hour  ☐ 6-hour  ☐ 8-hour      │   │
│  │                                                         │   │
│  │  Preview: 7 capacity values × 3 durations = 21 configs  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GENERATOR CAPACITY RANGE (if DG enabled)               │   │
│  │  From: [0] MW   To: [20] MW   Step: [5] MW              │   │
│  │                                                         │   │
│  │  Preview: 5 DG values                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SIMULATION SUMMARY                                     │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  Total configurations: 105                      │    │   │
│  │  │  Estimated time: ~3 seconds                     │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Behavior:**

| Element | Behavior |
|---------|----------|
| Mode toggle | Switches between Sizing Mode (ranges) and Fixed Mode (single values) |
| Capacity inputs | Three fields: min, max, step |
| Duration checkboxes | User selects which durations to test; at least one required |
| DG range | Only visible if DG enabled in Step 1 |
| Simulation summary | Updates in real-time; shows total configs and estimated time |
| Run button | Starts simulation; shows progress indicator |

**Validation:**
- Capacity: min > 0, max ≥ min, step > 0
- DG: min ≥ 0, max ≥ min, step > 0 (if DG enabled)
- At least one duration class selected
- Total simulations ≤ 50,000 (error) or ≤ 10,000 (warning)

---

### 5.4 Step 4: Results Table

**Purpose:** Primary output view — scan, sort, filter, select for comparison

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  RESULTS                                    [← Edit] [Export]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  QUICK FILTERS                                          │   │
│  │  [100% Delivery] [Zero DG] [Low Wastage] [Hide Dominated]│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ☐ │ BESS    │ Duration │ Power │ DG   │ DELIVERY │ WASTAGE │   │
│  │    │ (MWh)   │ (hrs)    │ (MW)  │ (MW) │ (%)      │ (%)     │   │
│  │ ───┼─────────┼──────────┼───────┼──────┼──────────┼─────────│   │
│  │  ☐ │ 100     │ 2        │ 50    │ 10   │ 99.8%    │ 1.9%    │   │
│  │  ☐ │ 150     │ 4        │ 37.5  │ 5    │ 99.2%    │ 2.4%    │   │
│  │  ☐ │ 100     │ 4        │ 25    │ 10   │ 98.7%    │ 3.1%    │   │
│  │  ☐ │ 200     │ 4        │ 50    │ 0    │ 98.4%    │ 1.4%    │   │
│  │  ☐ │ 100     │ 2        │ 50    │ 0    │ 96.1%    │ 2.4%    │   │
│  │  ☐ │ 100     │ 4        │ 25    │ 0    │ 93.8%  ⚠│ 6.9%    │   │
│  │  ...                                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SELECTED: 0 configurations          [Compare Selected] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Behavior:**

| Element | Behavior |
|---------|----------|
| Quick filters | Toggle buttons; multiple can be active; filters stack |
| Column headers | Clickable for sort; arrow indicates direction |
| Row checkbox | Select for comparison (max 3) |
| Row click | Opens Detail View for that configuration |
| Delivery % | **Primary metric** — bold, color-coded (green >99%, yellow 95-99%, red <95%) |
| Wastage % | **Secondary metric** — color-coded (green <2%, yellow 2-5%, red >5%) |
| BESS column | **Size metric** — always visible |
| Dominated rows | Dimmed or marked with indicator |
| Compare button | Active when 2-3 rows selected; opens Compare View |
| Export | Dropdown: CSV, Excel (full), Excel (summary only) |

**Default Sort:** Delivery % descending, then Wastage % ascending

**Additional Columns (toggleable):**
- DG Runtime (hours)
- DG Starts (count)
- BESS Cycles
- Green Hours (%)
- Unserved MWh

---

### 5.5 Detail View

**Purpose:** Deep dive on a single configuration

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  DETAIL: 100 MWh / 2-hour / 10 MW DG             [← Results]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Summary] [Day View] [Year View] [Dispatch Logic]              │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
│  (TAB: SUMMARY)                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  KEY METRICS                                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │  99.8%   │  │   1.9%   │  │  156 hrs │              │   │
│  │  │ Delivery │  │ Wastage  │  │ DG Time  │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ENERGY FLOWS (Annual)                                  │   │
│  │  Solar Generated:    450,000 MWh                        │   │
│  │  ├─ To Load:         320,000 MWh                        │   │
│  │  ├─ To Battery:       85,000 MWh                        │   │
│  │  └─ Curtailed:         8,550 MWh (1.9%)                 │   │
│  │                                                         │   │
│  │  Battery Discharged:  82,000 MWh                        │   │
│  │  DG Generated:        45,000 MWh                        │   │
│  │  Unserved:               876 MWh (0.2%)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  BATTERY METRICS                                        │   │
│  │  Equivalent Cycles:   218                               │   │
│  │  Max Daily Cycles:    1.8                               │   │
│  │  Days Over Limit:     0                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Tabs:**

| Tab | Content |
|-----|---------|
| **Summary** | Key metrics cards, energy flow breakdown, BESS/DG stats |
| **Day View** | 24-hour stacked area chart; user can pick specific day or "worst day" |
| **Year View** | Heatmap (365 × 24) showing SoC, delivery status, or DG runtime |
| **Dispatch Logic** | Flowchart of the template logic; current template highlighted |

---

### 5.6 Compare View

**Purpose:** Side-by-side evaluation of 2-3 configurations

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  COMPARE                                          [← Results]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────┬───────────────────┬───────────────────┐ │
│  │  CONFIG A         │  CONFIG B         │  CONFIG C         │ │
│  │  100 MWh / 2-hr   │  150 MWh / 4-hr   │  200 MWh / 4-hr   │ │
│  │  DG: 10 MW        │  DG: 5 MW         │  DG: 0 MW         │ │
│  ├───────────────────┼───────────────────┼───────────────────┤ │
│  │  Delivery: 99.8%  │  Delivery: 99.2%  │  Delivery: 98.4%  │ │
│  │  Wastage:  1.9%   │  Wastage:  2.4%   │  Wastage:  1.4% ✓ │ │
│  │  DG Hours: 156    │  DG Hours: 89     │  DG Hours: 0    ✓ │ │
│  │  Cycles:   218    │  Cycles:   156    │  Cycles:   121  ✓ │ │
│  ├───────────────────┼───────────────────┼───────────────────┤ │
│  │  [Day Chart]      │  [Day Chart]      │  [Day Chart]      │ │
│  │  (synchronized)   │  (synchronized)   │  (synchronized)   │ │
│  └───────────────────┴───────────────────┴───────────────────┘ │
│                                                                 │
│  ✓ = Best in category                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Behavior:**

| Element | Behavior |
|---------|----------|
| Columns | One per selected configuration (2-3 max) |
| Metrics | Same rows across all columns; best value highlighted |
| Day charts | Synchronized — hovering on one highlights same hour on others |
| Day selector | Single control affects all columns |

---

## 6. Interaction Patterns

### 6.1 Navigation

| Action | Result |
|--------|--------|
| Step indicator click | Navigate to that step (with validation warning if incomplete) |
| Back button | Return to previous step; data preserved |
| Browser back | Same as Back button (no data loss) |
| Results → Edit | Return to Step 3 (sizing) with current values |

### 6.2 Data Persistence

| Scenario | Behavior |
|----------|----------|
| Navigate between steps | Data preserved in session |
| Browser refresh | Data lost (MVP); saved scenarios persist |
| Save scenario | Stores all inputs + results with user-defined name |
| Load scenario | Restores full state; can re-run or modify |

### 6.3 Feedback

| Event | Feedback |
|-------|----------|
| Validation error | Inline message below field; field highlighted |
| Simulation running | Progress bar with config count (e.g., "Running 45 of 105...") |
| Simulation complete | Auto-navigate to Results |
| Export started | Toast notification; download auto-starts |

---

## 7. Visual Design Principles

### 7.1 Hierarchy

| Level | Usage | Treatment |
|-------|-------|-----------|
| **Primary** | Delivery %, BESS Size | Large, bold, color-coded |
| **Secondary** | Wastage %, DG metrics | Standard size, visible |
| **Tertiary** | Cycles, throughput, starts | Available on demand |

### 7.2 Color System

| Color | Meaning |
|-------|---------|
| **Green** | Good (high delivery, low wastage, zero DG) |
| **Yellow** | Warning (moderate, approaching limits) |
| **Red** | Problem (low delivery, high wastage, constraint violation) |
| **Gray** | Disabled, dominated, or secondary |
| **Blue** | Interactive element, selected state |

### 7.3 Density

- Laptop-first design (limited vertical space)
- Prefer horizontal layouts where possible
- Collapsible sections for advanced options
- Table should show 10-15 rows without scrolling

---

## 8. Future Considerations (Post-MVP)

### 8.1 Floating Config Bar

After MVP, consider a floating/auto-hiding configuration bar:

```
┌─────────────────────────────────────────────────────────────────┐
│  Results Table (full width)                                     │
│                                                                 │
│  ...                                                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [▼] BESS: 100 MWh | DG: 10 MW | Template: Green Priority  [Run]│
└─────────────────────────────────────────────────────────────────┘
```

- Expands on click to show full config
- Allows quick parameter changes without leaving results
- Run button triggers re-simulation

### 8.2 Live Update Mode

For Fixed Mode only:
- Single configuration displayed
- Changing any input triggers immediate re-simulation
- Results update in 2-3 seconds without page navigation

### 8.3 Scenario Comparison Across Templates

Allow comparing:
- Same sizing, different templates
- Different sites (load/solar profiles)
- What-if analysis (e.g., "what if DG fails for a week?")

---

## 9. Open Questions

| Question | Status | Decision |
|----------|--------|----------|
| Should dominated rows be hidden by default? | OPEN | Current: shown but marked |
| Should we show cost estimates (even rough)? | DEFERRED | V2 feature |
| Export format: single Excel or multiple sheets? | OPEN | Needs user input |
| Should scenarios auto-save? | OPEN | MVP: manual save only |

---

## 10. Acceptance Criteria (UX)

MVP is UX-complete when:

1. ☐ User can define system without knowing template names
2. ☐ System correctly infers template from dispatch rules
3. ☐ Results table shows three key metrics prominently
4. ☐ User can sort and filter results
5. ☐ User can drill down to configuration detail
6. ☐ User can compare 2-3 configurations side-by-side
7. ☐ User can export results to Excel
8. ☐ Navigation is clear and doesn't lose data
9. ☐ Validation prevents invalid simulations
10. ☐ Feedback is immediate and informative

---

*End of UX Guideline*
