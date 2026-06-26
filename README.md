# Task 2 — Event Registration System
> Django REST Framework backend | CodeAlpha Internship

## Tech Stack
- **Python 3** / **Django 4** / **Django REST Framework**
- **SQLite** (dev) — swap to PostgreSQL/MySQL in production
- Token-based authentication

## Quick Start

```bash
# 1. Install dependencies
pip install django djangorestframework django-cors-headers django-filter

# 2. Apply migrations
python manage.py migrate

# 3. Seed sample data
python seed_data.py

# 4. Run server
python manage.py runserver
```

### Admin panel
`http://127.0.0.1:8000/admin/`  — login: `admin` / `admin123`

---

## API Endpoints

### Authentication
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Get auth token |
| POST | `/api/auth/logout/` | Invalidate token |
| GET  | `/api/auth/profile/` | Current user info |

### Events (public read, auth required to create)
| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/api/events/` | List all events |
| GET  | `/api/events/?category=workshop` | Filter by category |
| GET  | `/api/events/?upcoming=true` | Upcoming events only |
| GET  | `/api/events/?search=python` | Search events |
| POST | `/api/events/create/` | Create event (auth) |
| GET  | `/api/events/<id>/` | Event detail |
| PUT/PATCH | `/api/events/<id>/edit/` | Update own event |
| DELETE | `/api/events/<id>/edit/` | Delete own event |
| GET  | `/api/events/my/` | My organized events |
| GET  | `/api/events/<id>/stats/` | Capacity stats |
| GET  | `/api/events/<id>/attendees/` | Attendee list (organizer only) |

### Registrations
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/events/<id>/register/` | Register for event |
| POST | `/api/events/<id>/cancel/` | Cancel registration |
| GET  | `/api/registrations/my/` | My registrations |
| GET  | `/api/registrations/my/?status=confirmed` | Filter by status |

---

## Example Usage

### 1. Register a user
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@mail.com","password":"pass1234","password2":"pass1234"}'
```

### 2. Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"pass1234"}'
# Returns: {"token": "abc123..."}
```

### 3. List events
```bash
curl http://127.0.0.1:8000/api/events/
```

### 4. Register for an event
```bash
curl -X POST http://127.0.0.1:8000/api/events/1/register/ \
  -H "Authorization: Token abc123..."
# Returns ticket_code
```

### 5. Cancel registration
```bash
curl -X POST http://127.0.0.1:8000/api/events/1/cancel/ \
  -H "Authorization: Token abc123..."
```

---

## Models

### Event
- `title`, `description`, `category`, `location`
- `date`, `end_date`, `capacity`, `price`
- `organizer` (FK → User), `is_active`
- Computed: `available_spots`, `is_full`, `is_upcoming`

### Registration
- `user`, `event` (FK), `status` (confirmed/cancelled/waitlisted)
- `ticket_code` (auto-generated, unique)
- `registered_at`, `notes`

### OrganizerProfile
- `user`, `organization`, `bio`, `website`, `is_verified`

---

## Test Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Organizer | `organizer1` | `password123` |
| User | `user1` | `password123` |
