# WorkSphere AI

WorkSphere AI is a premium AI-powered employee management SaaS concept built with Next.js on the frontend and Django on the backend.

## Product vision
- Dark futuristic glassmorphism UI
- Black, deep navy, and electric blue theme
- Animated particle-inspired background and floating gradients
- Premium SaaS design language inspired by modern startup products

## Architecture
### Frontend
- Next.js
- React
- TypeScript
- TailwindCSS
- Framer Motion

### Backend
- Django
- Django REST Framework

### Database
- PostgreSQL

### AI services
- Claude API
- OpenCV
- Face Recognition

## Core modules
- Employee management
- Attendance tracking
- Payroll automation
- Leave management
- Notifications
- AI assistant
- Analytics dashboard

## Database structure
- Employee
- Attendance
- Payroll
- Leave
- Department
- Notifications
- Face Encodings

## Attendance logic
- Male employees: 4-punch system (IN / OUT / IN / OUT)
- Female employees: Login / Logout
- Salary rules: full day, half day, approved leave without deduction, unapproved absence with deduction

## API surface
- /api/employees/
- /api/attendance/
- /api/payroll/
- /api/leaves/
- /api/departments/
- /api/notifications/
- /api/assistant/
- /api/dashboard-stats/

## UI experience
- Landing page with hero, feature grid, and architecture section
- Owner dashboard with live operational intelligence
- Employee-facing dashboard experience
- Secure login experience
- Attendance entry module
