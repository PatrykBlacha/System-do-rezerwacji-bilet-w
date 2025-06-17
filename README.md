# 🎟️ Ticket Reservation System

A web-based ticket reservation system built with Django and PostgreSQL. Users can browse upcoming events, reserve and purchase tickets, and manage their orders through a user-friendly interface.

> ⚠️ Note: The payment system is **not implemented**. Tickets can be reserved and marked as sold, but no real payment gateway is integrated.

---

## 🚀 Features

- User registration and login system (based on Django's built-in auth).
- Browse and search upcoming events.
- Reserve multiple tickets per event.
- Shopping cart view with participant data input.
- Automatic ticket reservation expiration (10 minutes).
- Order history and detailed order view.
- Order cancellation and ticket availability reset.
- Bootstrap 5-based responsive UI.

---

## 🧱 Tech Stack

- **Backend:** Django (Python)
- **Database:** PostgreSQL
- **Frontend:** HTML, Bootstrap 5
- **Auth:** Django built-in authentication
- **ORM:** Django ORM

---

## 🧪 How to Run Locally

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/ticket-reservation-system.git
   cd ticket-reservation-system/tickets_system
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**

   Make sure PostgreSQL is running and create a database, e.g. `tickets_db`.

   Update `settings.py` with your PostgreSQL credentials:

   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'tickets_db',
           'USER': 'your_user',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

5. **Apply migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Run the development server**

   ```bash
   python manage.py runserver
   ```

---

## 👥 Authors

- [Patryk Blacha](https://github.com/PatrykBlacha)
- [Maciej Trznadel](https://github.com/mtrznadel24)



