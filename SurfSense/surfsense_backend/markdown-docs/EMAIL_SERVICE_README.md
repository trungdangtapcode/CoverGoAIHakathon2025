# Email Service Documentation

## Overview

The SurfSense backend now includes a complete email service that allows authenticated users to send emails through SMTP. The service supports both plain text and HTML emails, with options for single recipient, bulk sending, and sending to specific users by ID.

## Setup

### 1. Configure Environment Variables

Add the following to your `.env` file (see `.env.example` for reference):

```bash
# SMTP Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_SENDER_EMAIL=your_email@gmail.com
SMTP_SENDER_PASSWORD=your_app_password_here
SMTP_SENDER_NAME=SurfSense
SMTP_USE_TLS=true
```

### 2. Gmail Setup (Recommended)

If using Gmail:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the generated 16-character password
   - Use this as `SMTP_SENDER_PASSWORD` (not your regular Gmail password)

### 3. Other Email Providers

#### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

#### Yahoo
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

#### Office 365
```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

## API Endpoints

All endpoints require authentication (JWT token).

### 1. Send Email to Any Address

**POST** `/api/v1/email/send`

Send an email to any email address.

**Request Body:**
```json
{
  "to_email": "recipient@example.com",
  "subject": "Welcome to SurfSense!",
  "content": "Hello! Welcome to our platform.",
  "is_html": false,
  "reply_to": "support@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email sent successfully"
}
```

### 2. Send Email to Specific User

**POST** `/api/v1/email/send-to-user/{user_id}`

Send an email to a registered user by their UUID.

**Path Parameter:**
- `user_id`: UUID of the target user

**Request Body:**
```json
{
  "subject": "Important Update",
  "content": "Hello! Here's an important update for you.",
  "is_html": false,
  "reply_to": "noreply@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email sent successfully"
}
```

### 3. Send Bulk Emails

**POST** `/api/v1/email/send-bulk`

Send the same email to multiple recipients.

**Request Body:**
```json
{
  "to_emails": [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
  ],
  "subject": "Newsletter",
  "content": "Check out our latest updates!",
  "is_html": false
}
```

**Response:**
```json
{
  "success_count": 3,
  "failure_count": 0,
  "failed_emails": [],
  "message": "Successfully sent 3 emails"
}
```

### 4. Send Email to All Users

**POST** `/api/v1/email/send-to-all-users`

Send an email to all registered users in the system.

**Request Body:**
```json
{
  "subject": "System Announcement",
  "content": "Important system update for all users.",
  "is_html": false
}
```

**Response:**
```json
{
  "success_count": 150,
  "failure_count": 2,
  "failed_emails": ["bounced@example.com", "invalid@test.com"],
  "message": "Sent to 150 users, 2 failed"
}
```

## HTML Email Example

You can send HTML emails by setting `is_html: true`:

```json
{
  "to_email": "user@example.com",
  "subject": "Welcome!",
  "content": "<html><body><h1>Welcome to SurfSense!</h1><p>We're excited to have you.</p></body></html>",
  "is_html": true
}
```

## Using the API

### cURL Example

```bash
# Get your JWT token first by logging in
TOKEN="your_jwt_token_here"

# Send a simple email
curl -X POST "http://localhost:8002/api/v1/email/send" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "recipient@example.com",
    "subject": "Test Email",
    "content": "This is a test email from SurfSense",
    "is_html": false
  }'
```

### Python Example

```python
import requests

# Login first to get token
login_response = requests.post(
    "http://localhost:8002/auth/jwt/login",
    data={
        "username": "your_email@example.com",
        "password": "your_password"
    }
)
token = login_response.json()["access_token"]

# Send email
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

email_data = {
    "to_email": "recipient@example.com",
    "subject": "Test from Python",
    "content": "Hello from SurfSense API!",
    "is_html": False
}

response = requests.post(
    "http://localhost:8002/api/v1/email/send",
    headers=headers,
    json=email_data
)

print(response.json())
```

### JavaScript/TypeScript Example

```javascript
// Login first to get token
const loginResponse = await fetch('http://localhost:8002/auth/jwt/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    username: 'your_email@example.com',
    password: 'your_password'
  })
});
const { access_token } = await loginResponse.json();

// Send email
const response = await fetch('http://localhost:8002/api/v1/email/send', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    to_email: 'recipient@example.com',
    subject: 'Test from JavaScript',
    content: 'Hello from SurfSense API!',
    is_html: false
  })
});

const result = await response.json();
console.log(result);
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Email sent successfully
- `400 Bad Request`: Invalid request data or user has no email
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: User not found (for user-specific endpoints)
- `500 Internal Server Error`: SMTP error or email sending failed

## Testing

### Local Testing with Debug Server

For development/testing without sending real emails, you can use Python's debug SMTP server:

```bash
# Start debug server
python -m smtpd -c DebuggingServer -n localhost:1025
```

Then update your `.env`:
```bash
SMTP_SERVER=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
```

Emails will be printed to the console instead of being sent.

## Security Best Practices

1. **Never commit credentials**: Keep `.env` file out of version control
2. **Use App Passwords**: Don't use your main email password
3. **Limit access**: Only authenticated users can send emails
4. **Rate limiting**: Consider implementing rate limits for production
5. **Validate recipients**: The API validates email formats using Pydantic

## Architecture

### Components

1. **EmailService** (`app/services/email_service.py`)
   - Handles SMTP connection and email sending
   - Supports text, HTML, and bulk emails
   - Includes comprehensive error handling

2. **Email Schemas** (`app/schemas/email.py`)
   - Pydantic models for request/response validation
   - Email format validation with `EmailStr`

3. **Email Routes** (`app/routes/email_routes.py`)
   - RESTful API endpoints
   - Authentication required for all endpoints
   - Database integration for user lookups

4. **Configuration** (`app/config/__init__.py`)
   - Environment-based SMTP configuration
   - Secure credential management

## Troubleshooting

### "Authentication failed" Error
- Check that you're using an App Password (for Gmail)
- Verify `SMTP_SENDER_EMAIL` and `SMTP_SENDER_PASSWORD` are correct

### "Connection timeout" Error
- Check firewall settings
- Verify `SMTP_SERVER` and `SMTP_PORT` are correct
- Ensure network allows SMTP connections

### Emails Going to Spam
- Set up SPF, DKIM, and DMARC records for your domain
- Use a verified domain email address
- Avoid spam trigger words in subject/content

### "User does not have an email address"
- Ensure users have email addresses in the database
- Check the User model has the `email` field populated

## Future Enhancements

Possible improvements:
- Email templates system
- Attachment support
- Scheduling emails for later
- Email queue with Celery for async sending
- Delivery status tracking
- Unsubscribe link management
- Email analytics and open tracking

## Support

For issues or questions about the email service:
1. Check the logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test with the debug SMTP server first
4. Review the API documentation at `/docs` endpoint
