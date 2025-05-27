from ortools.sat.python import cp_model

def solve_shift_scheduling():
    """
    Solves a basic shift scheduling problem using CP-SAT solver.

    This function defines a model with employees, days, and shifts,
    applies several common constraints (e.g., one shift per employee per day,
    required personnel continuité, an-off_days), and then_employee_work_days, holiday_requests,
    and attempts to find a feasible schedule.
    """
    # --- Model Definition ---
    model = cp_model.CpModel()

    # --- Model Data ---
    num_employees = 3
    num_days = 5
    # Shift IDs: 0 = Day Off, 1 = Day Shift, 2 = Night Shift
    num_shifts = 3

    all_employees = range(num_employees)
    all_days = range(num_days)
    all_shifts = range(num_shifts)
    work_shifts = [1, 2] # Shifts that count as work

    # Required personnel for each shift on each day
    # Format: (day_index, shift_id): count
    # Example: Day shift (1) on day 0 requires 1 employee.
    required_personnel = {}
    for d in all_days:
        required_personnel[(d, 1)] = 1  # Day Shift
        required_personnel[(d, 2)] = 1  # Night Shift

    # Employee holiday requests
    # Format: (employee_id, day_index): True if requested off
    holiday_requests = {
        (0, 0): True, # Employee 0 requests day 0 off
        (1, 2): True, # Employee 1 requests day 2 off
    }

    # --- Variables ---
    # shifts[(e, d, s)] is a Boolean variable:
    # 1 if employee e is assigned to shift s on day d, 0 otherwise.
    shifts = {}
    for e in all_employees:
        for d in all_days:
            for s in all_shifts:
                shifts[(e, d, s)] = model.NewBoolVar(f'shift_e{e}_d{d}_s{s}')

    # --- Constraints ---

    # 1. Each employee is assigned to exactly one shift per day.
    for e in all_employees:
        for d in all_days:
            model.AddExactlyOne(shifts[(e, d, s)] for s in all_shifts)

    # 2. Meet personnel requirements for each work shift on each day.
    for d in all_days:
        for s in work_shifts:
            if (d, s) in required_personnel:
                model.Add(sum(shifts[(e, d, s)] for e in all_employees) == required_personnel[(d, s)])

    # 3. Honor holiday requests (assign Day Off shift).
    for e in all_employees:
        for d in all_days:
            if (e, d) in holiday_requests and holiday_requests[(e, d)]:
                model.Add(shifts[(e, d, 0)] == 1) # Shift 0 is Day Off

    # 4. An employee assigned to a Night Shift (shift 2) must have the next day off (shift 0).
    for e in all_employees:
        for d in range(num_days - 1): # Iterate up to the second to last day
            # If shifts[(e, d, 2)] is true, then shifts[(e, d + 1, 0)] must also be true.
            model.AddImplication(shifts[(e, d, 2)], shifts[(e, d + 1, 0)])

    # 5. Maximum of 3 consecutive work days for any employee.
    max_consecutive_work_days = 3
    for e in all_employees:
        for d_start in range(num_days - max_consecutive_work_days):
            # Check a window of (max_consecutive_work_days + 1) days.
            # The sum of work shifts in this window must not exceed max_consecutive_work_days.
            window_work_flags = []
            for i in range(max_consecutive_work_days + 1):
                day_in_window = d_start + i
                # Create an auxiliary Boolean variable indicating if employee e is working on day_in_window.
                is_working_on_day = model.NewBoolVar(f'e{e}_d{day_in_window}_is_working')
                # Link is_working_on_day to the sum of work shifts for employee e on that day.
                model.Add(sum(shifts[(e, day_in_window, s)] for s in work_shifts) == is_working_on_day)
                window_work_flags.append(is_working_on_day)
            model.Add(sum(window_work_flags) <= max_consecutive_work_days)

    # --- Solve the Model ---
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # --- Display Results ---
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution found:")
        shift_names = {0: "Day Off", 1: "Day Shift", 2: "Night Shift"}
        for d in all_days:
            print(f"Day {d}:")
            for e in all_employees:
                for s in all_shifts:
                    if solver.Value(shifts[(e, d, s)]) == 1:
                        print(f"  Employee {e}: {shift_names[s]} (Shift ID: {s})")
            # Optional: Verify daily assignments against requirements
            for s_check in work_shifts:
                assigned_staff = [str(e_check) for e_check in all_employees if solver.Value(shifts[(e_check, d, s_check)]) == 1]
                print(f"    -> {shift_names[s_check]} assigned: {', '.join(assigned_staff)} (Required: {required_personnel.get((d,s_check), 0)})")
        print("-" * 20)

    elif status == cp_model.INFEASIBLE:
        print("No solution found. Constraints might be too tight or conflicting.")
    elif status == cp_model.MODEL_INVALID:
        print("Model is invalid. Check model construction.")
    else:
        print(f"Solver status: {status} (An unknown error or other status occurred)")

    # (Optional) Print solver statistics.
    # print("Solver statistics:")
    # print(f"  - Status          : {solver.StatusName(status)}")
    # print(f"  - Conflicts       : {solver.NumConflicts()}")
    # print(f"  - Branches        : {solver.NumBranches()}")
    # print(f"  - Wall time       : {solver.WallTime()}s")

if __name__ == '__main__':
    solve_shift_scheduling()