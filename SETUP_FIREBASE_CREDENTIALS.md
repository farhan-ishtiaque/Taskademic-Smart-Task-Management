# Firebase Service Account Setup

⚠️ **IMPORTANT**: You need to download your Firebase service account key to enable Google authentication.

## Steps to get your Firebase service account key:

1. **Go to Firebase Console**: https://console.firebase.google.com/
2. **Select your project**: taskademic1
3. **Go to Settings** → **Project settings**
4. **Click on Service accounts tab**
5. **Click "Generate new private key"**
6. **Download the JSON file**
7. **Rename it to**: `firebase-service-account.json`
8. **Place it in this directory**: `E:\Taskademic\firebase-service-account.json`

## Enable Google Sign-In:

1. **In Firebase Console**, go to **Authentication** → **Sign-in method**
2. **Click on Google** provider
3. **Toggle Enable**
4. **Add authorized domains**:
   - `localhost`
   - `127.0.0.1`
5. **Save**

## Test the authentication:

1. **Refresh the login page**: http://127.0.0.1:8000/accounts/login/
2. **Click "Sign in with Google"**
3. **Complete Google sign-in**
4. **Should redirect to dashboard**

Without the service account file, the backend authentication will fail, but the frontend should work.
