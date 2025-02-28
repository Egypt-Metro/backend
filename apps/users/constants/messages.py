# apps/users/constants/messages.py

class UserMessages:
    """
    Constants for user-related messages.
    Used for consistent message handling across the application.
    """
    # Success messages
    REGISTRATION_SUCCESS = "User registered successfully"
    LOGIN_SUCCESS = "Login successful"
    PROFILE_UPDATED = "Profile updated successfully"
    PASSWORD_CHANGED = "Password changed successfully"
    LOGOUT_SUCCESS = "Logged out successfully"

    # Error messages
    INVALID_CREDENTIALS = "Invalid credentials"
    INVALID_TOKEN = "Invalid or expired token"
    USER_NOT_FOUND = "User not found"
    EMAIL_EXISTS = "A user with this email already exists"
    USERNAME_EXISTS = "A user with this username already exists"
    PASSWORDS_NOT_MATCH = "Passwords do not match"
    INVALID_PASSWORD = "Invalid password"

    # Validation messages
    INVALID_EMAIL = "Please enter a valid email address"
    INVALID_PHONE = "Please enter a valid phone number"
    INVALID_NATIONAL_ID = "Please enter a valid national ID"
    REQUIRED_FIELD = "This field is required"

    # Authorization messages
    UNAUTHORIZED = "You do not have permission to perform this action"
    TOKEN_EXPIRED = "Your session has expired. Please login again"

    # Profile messages
    PROFILE_NOT_FOUND = "Profile not found"
    PROFILE_UPDATE_FAILED = "Failed to update profile"

    # Balance messages
    INSUFFICIENT_BALANCE = "Insufficient balance"
    INVALID_AMOUNT = "Invalid amount"

    # Subscription messages
    SUBSCRIPTION_UPDATED = "Subscription updated successfully"
    SUBSCRIPTION_FAILED = "Failed to update subscription"

    # Payment messages
    PAYMENT_SUCCESS = "Payment processed successfully"
    PAYMENT_FAILED = "Payment processing failed"

    # General messages
    SOMETHING_WENT_WRONG = "Something went wrong. Please try again"
    REQUEST_FAILED = "Request failed. Please try again"
