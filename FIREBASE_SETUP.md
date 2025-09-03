# Firebase Google Authentication Setup

## 🔥 Firebase Project Configuration

Your Firebase project is already configured with the following details:
- **Project ID**: `taskademic1`
- **Auth Domain**: `taskademic1.firebaseapp.com`
- **API Key**: `AIzaSyDCvnJdpNOeR3WI3p3tZue-duWCh9iRdjw`

## 📋 Required Setup Steps

### 1. Download Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **taskademic1**
3. Click on ⚙️ **Settings** → **Project settings**
4. Go to **Service accounts** tab
5. Click **Generate new private key**
6. Download the JSON file
7. **Rename it to**: `firebase-service-account.json`
8. **Place it in your project root**: `E:\Taskademic\firebase-service-account.json`

### 2. Enable Google Authentication

1. In Firebase Console, go to "Authentication" > "Sign-in method"
2. Click on "Google" provider
3. Toggle "Enable"
4. Set project support email
5. Click "Save"

## Step 3: Get Web App Configuration

1. Go to Project Settings (gear icon) > "General" tab
2. Scroll down to "Your apps" section
3. Click "Add app" > Web app (</>) icon
4. Enter app nickname: "Taskademic Web"
5. Check "Also set up Firebase Hosting" (optional)
6. Click "Register app"
7. Copy the firebaseConfig object values

## Step 4: Get Service Account Key

1. Go to Project Settings > "Service accounts" tab
2. Click "Generate new private key"
3. Download the JSON file
4. Rename it to `firebase-service-account.json`
5. Place it in your Django project root directory

## Step 5: Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Copy from .env.example and update values
cp .env.example .env
```

Update the `.env` file with your Firebase configuration:

```bash
# Path to your service account file
GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json

# Firebase web app config (public values)
FIREBASE_API_KEY=your_api_key_here
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
```

## Step 6: Update Firebase Config in JavaScript

Update the `firebaseConfig` object in `static/auth/firebase-auth.js` with your project's values:

```javascript
const firebaseConfig = {
  apiKey: "your_api_key_here",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.firebasestorage.app",
  messagingSenderId: "your_messaging_sender_id",
  appId: "your_app_id",
  measurementId: "your_measurement_id"
};
```

## Step 7: Test the Integration

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to `http://127.0.0.1:8000/accounts/login/`

3. Click "Sign in with Google"

4. Complete the Google authentication flow

5. You should be redirected to the dashboard upon successful authentication

## Troubleshooting

### Common Issues:

1. **"Firebase not properly configured"**
   - Check that your service account JSON file path is correct
   - Verify the JSON file is valid
   - Check Django logs for detailed error messages

2. **"Invalid token" error**
   - Ensure your Firebase project has Google authentication enabled
   - Verify the API key and project ID are correct

3. **CSRF token errors**
   - Make sure CSRF middleware is properly configured
   - Check that the frontend is sending CSRF tokens correctly

4. **User not created in database**
   - Check Django logs for any database errors
   - Verify migrations have been applied: `python manage.py migrate`

### Debug Mode:

Enable debug logging by checking Django console output when starting the server. Look for messages from:
- `taskademic.firebase_init`
- `accounts.firebase_views`

## Security Notes

- Never commit your `firebase-service-account.json` file to version control
- Add it to your `.gitignore` file
- Use environment variables for production deployments
- Keep your Firebase API keys secure (though web API keys are public by design)

## Production Deployment

For production, instead of using a file path, set the service account JSON as an environment variable:

```bash
FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"..."}' 
```

This is more secure for cloud deployments where file storage might not be persistent.
