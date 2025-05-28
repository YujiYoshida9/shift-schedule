import json # Added for main function output
from ortools.sat.python import cp_model
from enum import IntEnum

# --- Global Constants ---
NUM_EMPLOYEES = 25
NUM_DAYS = 30

class Shift(IntEnum):
    DAY_OFF = 0
    DAY = 1
    NIGHT = 2

def get_required_personnel(num_days):
    return {
        (d, Shift.DAY): 1 for d in range(num_days)
    } | {
        (d, Shift.NIGHT): 1 for d in range(num_days)
    }

# Required personnel for each shift on each day.
# Format: (day_index, shift_id): count of required employees.
# Example: On day 0, DAY_SHIFT requires 1 employee.
REQUIRED_PERSONNEL = get_required_personnel(NUM_DAYS)

# Employee holiday requests.
# Format: (employee_id, day_index): True if the employee requests this day off.
HOLIDAY_REQUESTS = {
    (0, 0): True,  # Employee 0 requests day 0 off.
    (1, 2): True,  # Employee 1 requests day 2 off.
}

MAX_CONSECUTIVE_WORK_DAYS = 3

# --- Model Data Structure ---
# This dictionary consolidates all model parameters for easy access.
MODEL_DATA = {
    "num_employees": NUM_EMPLOYEES,
    "num_days": NUM_DAYS,
    "num_shifts": len(Shift),
    "all_employees": range(NUM_EMPLOYEES),
    "all_days": range(NUM_DAYS),
    "all_shifts": list(Shift),
    "work_shifts": [Shift.DAY, Shift.NIGHT],
    "required_personnel": REQUIRED_PERSONNEL,
    "holiday_requests": HOLIDAY_REQUESTS,
    "max_consecutive_work_days": MAX_CONSECUTIVE_WORK_DAYS,
}


def create_model_and_data():
    """
    Initializes the CP-SAT model and retrieves the model data.

    Returns:
        tuple: A tuple containing:
            - model (cp_model.CpModel): The CP-SAT model instance.
            - model_data (dict): The dictionary containing all model parameters.
    """
    model = cp_model.CpModel()
    return model, MODEL_DATA


def define_variables(model, model_data):
    """
    Defines the shift assignment variables for the model.

    The core variables `shifts[(e, d, s)]` are Boolean, indicating whether
    employee `e` is assigned to shift `s` on day `d`.

    Args:
        model (cp_model.CpModel): The CP-SAT model instance.
        model_data (dict): A dictionary containing model parameters like
                           number of employees, days, and shifts.

    Returns:
        dict: A dictionary where keys are (employee, day, shift) tuples and
              values are the corresponding Boolean decision variables.
    """
    shifts = {}
    for e in model_data["all_employees"]:
        for d in model_data["all_days"]:
            for s in model_data["all_shifts"]:
                shifts[(e, d, s)] = model.NewBoolVar(f'shift_e{e}_d{d}_s{s}')
    return shifts


def add_constraints(model, model_data, shifts):
    """
    Adds all operational and fairness constraints to the CP-SAT model.

    Args:
        model (cp_model.CpModel): The CP-SAT model instance.
        model_data (dict): A dictionary containing model parameters used
                           to define constraints (e.g., required personnel,
                           holiday requests, consecutive work day limits).
        shifts (dict): A dictionary of shift assignment variables.
    """
    # Constraint 1: Each employee is assigned to exactly one shift per day.
    # This ensures that every employee has a defined status (working or off) for each day.
    for e in model_data["all_employees"]:
        for d in model_data["all_days"]:
            model.AddExactlyOne(shifts[(e, d, s)] for s in model_data["all_shifts"])

    # Constraint 2: Meet personnel requirements for each work shift on each day.
    # Ensures that each designated work shift has the specified number of employees.
    for d in model_data["all_days"]:
        for s in model_data["work_shifts"]:
            if (d, s) in model_data["required_personnel"]:
                model.Add(
                    sum(shifts[(e, d, s)] for e in model_data["all_employees"]) ==
                    model_data["required_personnel"][(d, s)]
                )

    # Constraint 3: Honor holiday requests.
    # If an employee has requested a day off, they are assigned the DAY_OFF_SHIFT.
    for e in model_data["all_employees"]:
        for d in model_data["all_days"]:
            if (e, d) in model_data["holiday_requests"] and \
               model_data["holiday_requests"][(e, d)]:
                model.Add(shifts[(e, d, Shift.DAY_OFF)] == 1)

    # Constraint 4: An employee assigned to a Night Shift must have the next day off.
    # This is a common rule for safety and well-being.
    for e in model_data["all_employees"]:
        # Iterate up to the second to last day because the constraint looks ahead one day.
        for d in range(model_data["num_days"] - 1):
            model.AddImplication(shifts[(e, d, Shift.NIGHT)],
                                 shifts[(e, d + 1, Shift.DAY_OFF)])

    # Constraint 5: Maximum consecutive work days.
    # Limits the number of consecutive days an employee can work without a day off.
    max_consecutive = model_data["max_consecutive_work_days"]
    for e in model_data["all_employees"]:
        # Iterate through all possible start days for a sequence of work days.
        # The window size is max_consecutive + 1 to check if it *exceeds* max_consecutive.
        for d_start in range(model_data["num_days"] - max_consecutive):
            window_work_flags = []
            # Create a flag for each day in the window indicating if the employee is working.
            for i in range(max_consecutive + 1):
                day_in_window = d_start + i
                is_working_on_day = model.NewBoolVar(
                    f'e{e}_d{day_in_window}_is_working'
                )
                # An employee is working if they are assigned to any of the WORK_SHIFTS.
                model.Add(
                    sum(shifts[(e, day_in_window, s)]
                        for s in model_data["work_shifts"]) == is_working_on_day
                )
                window_work_flags.append(is_working_on_day)
            # The sum of work flags in the window must not exceed max_consecutive.
            model.Add(sum(window_work_flags) <= max_consecutive)


def solve_and_display(model, model_data, shifts):
    """
    Solves the shift scheduling model and returns the schedule or error details.

    Args:
        model (cp_model.CpModel): The CP-SAT model instance, with variables
                                   and constraints already added.
        model_data (dict): A dictionary containing model parameters.
        shifts (dict): A dictionary of the shift assignment variables.

    Returns:
        dict: A dictionary containing the solution status and data.
              Example:
              {
                  "status": "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "MODEL_INVALID" | "SOLVER_STATUS_X",
                  "data": list_of_strings_for_schedule | error_message_string
              }
    """
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    result = {"status": "", "data": None}

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        result["status"] = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        schedule_output = []
        shift_names = {
            Shift.DAY_OFF: "Day Off",
            Shift.DAY: "Day Shift",
            Shift.NIGHT: "Night Shift"
        }
        schedule_output.append("Solution found:")
        for d in model_data["all_days"]:
            schedule_output.append(f"Day {d}:")
            for e in model_data["all_employees"]:
                for s in model_data["all_shifts"]:
                    if solver.Value(shifts[(e, d, s)]) == 1:
                        schedule_output.append(
                            f"  Employee {e}: {shift_names[s]} (Shift ID: {s})"
                        )
            # Optional: Verify daily assignments against requirements.
            for s_check in model_data["work_shifts"]:
                assigned_staff = [
                    str(e_check) for e_check in model_data["all_employees"]
                    if solver.Value(shifts[(e_check, d, s_check)]) == 1
                ]
                required_count = model_data['required_personnel'].get((d, s_check), 0)
                schedule_output.append(
                    f"    -> {shift_names[s_check]} assigned: {', '.join(assigned_staff)} "
                    f"(Required: {required_count})"
                )
        schedule_output.append("-" * 20)
        result["data"] = schedule_output
    elif status == cp_model.INFEASIBLE:
        result["status"] = "INFEASIBLE"
        result["data"] = "No solution found. Constraints might be too tight or conflicting."
    elif status == cp_model.MODEL_INVALID:
        result["status"] = "MODEL_INVALID"
        result["data"] = "Model is invalid. Check model construction."
    else:
        result["status"] = f"SOLVER_STATUS_{status}"
        result["data"] = f"Solver status: {status} (An unknown error or other status occurred)"

    # Optional: Print solver statistics for debugging or performance analysis.
    # Can be added to result dict if needed:
    # result["statistics"] = {
    #     "status_name": solver.StatusName(status),
    #     "conflicts": solver.NumConflicts(),
    #     "branches": solver.NumBranches(),
    #     "wall_time_seconds": solver.WallTime()
    # }
    # print("\nSolver statistics:")
    # print(f"  - Status          : {solver.StatusName(status)}")
    # print(f"  - Conflicts       : {solver.NumConflicts()}")
    # print(f"  - Branches        : {solver.NumBranches()}")
    # print(f"  - Wall time       : {solver.WallTime():.2f}s")
    return result


def main():
    """
    Main function to orchestrate the shift scheduling process.

    It creates the model and data, defines variables, adds constraints,
    solves the model, and prints the resulting solution details as a JSON object.
    """
    model, model_data = create_model_and_data()
    shifts_variables = define_variables(model, model_data)
    add_constraints(model, model_data, shifts_variables)
    solution_details = solve_and_display(model, model_data, shifts_variables)
    print(json.dumps(solution_details, indent=2))


if __name__ == '__main__':
    main()