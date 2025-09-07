# Secure Authentication App

A production-ready Streamlit application with MongoDB authentication, enhanced security features, and modern UI design.

## Features

### Security
- **Account Locking**: Automatic lockout after 5 failed attempts
- **Input Validation**: Comprehensive email and username validation
- **Connection Security**: Secure MongoDB connection handling

### User Management
- **User Registration**: With email verification
- **Secure Login**: With failed attempt tracking
- **Profile Management**: View and update user information
- **Password Change**: Secure password update functionality
- **Session Management**: Proper session handling and cleanup

### Modern UI
- **Responsive Design**: Clean, mobile-friendly interface
- **Status Indicators**: Connection and security status
- **Enhanced Dashboard**: Activity tracking and settings
- **Progress Animations**: Visual feedback for user actions

## Quick Start

### Prerequisites
- Python 3.8+
- MongoDB Atlas account or local MongoDB instance

### Installation

1. **Clone or download the files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your MongoDB connection string:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
   ```

4. **Run the application**:
   ```bash
   streamlit run main.py
   ```

## Project Structure

```
├── main.py           # Application entry point and routing
├── login.py          # Authentication logic and user management
├── database.py       # MongoDB connection and configuration
├── ui.py             # User interface components
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variables template
└── README.md         # This file
```

## Configuration

### MongoDB Setup

1. **Create MongoDB Atlas Account**: [MongoDB Atlas](https://cloud.mongodb.com)
2. **Create Cluster**: Follow the setup wizard
3. **Get Connection String**: From the "Connect" button in your cluster
4. **Whitelist IP**: Add your IP address to the network access list
5. **Create Database User**: With read/write permissions

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB connection string | ✅ |
| `SECRET_KEY` | Application secret key | No |
| `DEBUG` | Enable debug mode | No |

## Security Features

### Account Protection
- Account lockout after 5 failed login attempts
- 15-minute lockout period
- Automatic unlock after timeout

### Data Protection
- Email addresses stored in lowercase
- No sensitive data in logs
- Secure database connections

## Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "username": String (unique),
  "email": String (unique, lowercase),
  "password": String (hashed),
  "salt": String,
  "role": String,
  "created_at": DateTime,
  "last_login": DateTime,
  "is_active": Boolean,
  "failed_login_attempts": Number,
  "account_locked_until": DateTime
}
```

### Dashboard Collection
```javascript
{
  "_id": ObjectId,
  "user_id": String,
  "data": Object,
  "created_at": DateTime
}
```

## API Functions

### Authentication
- `verify_user(username, password)` - Verify login credentials
- `register_user(username, password, email)` - Register new user
- `user_exists(username)` - Check if username exists
- `change_password(username, old_password, new_password)` - Change password

### Security
- `is_account_locked(username)` - Check account lock status
- `handle_failed_login(username)` - Handle failed login attempts

### User Management
- `get_user_info(username)` - Get user profile information
- `update_last_login(username)` - Update last login timestamp

## Deployment

### Streamlit Cloud
1. Push code to GitHub repository
2. Connect Streamlit Cloud to your repository
3. Add environment variables in Streamlit Cloud settings
4. Deploy

### Docker (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "main.py"]
```

## Future Enhancements

- [ ] Two-factor authentication (2FA)
- [ ] Email verification for registration
- [ ] Password reset via email
- [ ] OAuth integration (Google, GitHub)
- [ ] User roles and permissions
- [ ] Activity logging and audit trails
- [ ] Rate limiting for API endpoints
- [ ] Session timeout management
- [ ] CAPTCHA for registration
- [ ] Email notifications for security events

## Troubleshooting

### Common Issues

**Connection Error**: 
- Check MongoDB URI in `.env` file
- Verify network access whitelist in MongoDB Atlas
- Ensure database user has proper permissions

**Authentication Error**:
- Verify username and password
- Check if account is locked due to failed attempts
- Ensure database connection is active

**Import Errors**:
- Install all requirements: `pip install -r requirements.txt`
- Check Python version compatibility

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For support and questions, please create an issue in the repository or contact the development team.