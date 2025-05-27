from fastapi import FastAPI, HTTPException
# Import the scheduling functions from src.shift_schedule
from src.shift_schedule import (
    create_model_and_data,
    define_variables,
    add_constraints,
    solve_and_display
)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World from FastAPI"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/schedule/generate")
async def generate_schedule():
    try:
        # 1. Create model and data
        model, model_data = create_model_and_data()

        # 2. Define variables
        shifts_variables = define_variables(model, model_data)

        # 3. Add constraints
        add_constraints(model, model_data, shifts_variables)

        # 4. Solve and get results
        # This function now returns a dictionary
        solution_details = solve_and_display(model, model_data, shifts_variables)

        # Return the details from the solver
        # The solution_details already has a 'status' and 'data' field.
        if solution_details["status"] == "OPTIMAL" or solution_details["status"] == "FEASIBLE":
            return {
                "success": True,
                "message": "Schedule generation process completed.",
                "details": solution_details
            }
        else:
            return {
                "success": False,
                "message": "Schedule generation process resulted in issues.",
                "details": solution_details
            }

    except Exception as e:
        # Catch any unexpected errors during the process
        # Log the error server-side (not implemented here, but good practice)
        # print(f"Error during schedule generation: {e}") # For server logs
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

# If you were to run this file directly using uvicorn for local testing (optional):
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
