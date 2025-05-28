# Shift Schedule Optimizer

A FastAPI-based shift scheduling system using Google OR-Tools for optimal employee scheduling with Kubernetes deployment support.

## Features

- **Optimal Scheduling**: Uses Google OR-Tools CP-SAT solver for optimal shift assignments
- **Flexible Constraints**: Supports holiday requests, consecutive work day limits, and personnel requirements
- **REST API**: FastAPI-based web service with automatic documentation
- **Kubernetes Ready**: Includes Helm charts and Skaffold configuration for easy deployment

## Quick Start

### Prerequisites

- Docker
- Kubernetes cluster (minikube, Docker Desktop, etc.)
- Skaffold
- Helm (optional, managed by Skaffold)

### Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd shift-schedule
   ```

2. **Start development environment**
   ```bash
   skaffold dev -p dev
   ```

3. **Access the application**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### API Usage

#### Generate Schedule
```bash
curl -X POST http://localhost:8000/schedule/generate
```

#### Example Response
```json
{
  "success": true,
  "message": "Schedule generation process completed.",
  "details": {
    "status": "OPTIMAL",
    "data": [
      "Solution found:",
      "Day 0:",
      "  Employee 1: Day Shift (Shift ID: 1)",
      "  Employee 5: Night Shift (Shift ID: 2)",
      ...
    ]
  }
}
```

## Configuration

### Scheduling Parameters

Edit `src/shift_schedule.py` to customize:

- `NUM_EMPLOYEES`: Number of employees (default: 25)
- `NUM_DAYS`: Scheduling period in days (default: 30)
- `MAX_CONSECUTIVE_WORK_DAYS`: Maximum consecutive work days (default: 3)
- `HOLIDAY_REQUESTS`: Employee holiday requests
- `REQUIRED_PERSONNEL`: Personnel requirements per shift

### Example Configuration
```python
# Employee holiday requests
HOLIDAY_REQUESTS = {
    (0, 0): True,  # Employee 0 requests day 0 off
    (1, 2): True,  # Employee 1 requests day 2 off
}

# Required personnel per day/shift
def get_required_personnel(num_days):
    return {
        (d, Shift.DAY): 1 for d in range(num_days)
    } | {
        (d, Shift.NIGHT): 1 for d in range(num_days)
    }
```

## Architecture

```
shift-schedule/
├── src/
│   ├── main.py              # FastAPI application
│   ├── shift_schedule.py    # Core scheduling logic
│   └── requirements.txt     # Python dependencies
├── charts/app/              # Helm chart
│   ├── templates/
│   ├── values.yaml
│   ├── values-dev.yaml
│   └── values-prod.yaml
├── Dockerfile               # Container definition
├── skaffold.yaml           # Skaffold configuration
└── README.md
```

## Deployment

### Development
```bash
skaffold dev -p dev
```

### Production
```bash
skaffold run -p prod
```

### Manual Deployment
```bash
# Build Docker image
docker build -t python-app .

# Deploy with Helm
helm install python-app charts/app -f charts/app/values-prod.yaml
```

## Constraints & Features

The scheduling system implements the following constraints:

1. **One Shift Per Day**: Each employee is assigned exactly one shift per day
2. **Personnel Requirements**: Each shift meets minimum staffing requirements
3. **Holiday Requests**: Honors employee vacation requests
4. **Night Shift Rest**: Employees get the day off after night shifts
5. **Consecutive Work Limit**: Limits consecutive working days for employee wellbeing

## Technology Stack

- **Backend**: FastAPI (Python)
- **Optimization**: Google OR-Tools CP-SAT
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Deployment**: Helm + Skaffold
- **Development**: Hot reload with uvicorn/gunicorn

