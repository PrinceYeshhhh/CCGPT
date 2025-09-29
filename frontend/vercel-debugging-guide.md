# 🐛 Vercel Debugging Guide for CustomerCareGPT

## Overview
This guide helps you debug 500 errors and other issues when running CustomerCareGPT on Vercel.

## 🔍 How to See Errors on Vercel

### **1. Browser Developer Tools (Same as Localhost)**
- Press **F12** to open Developer Tools
- Go to **Console tab** - See JavaScript errors and console.log outputs
- Go to **Network tab** - See all API calls and their responses (including 500 errors)
- Go to **Sources tab** - Debug JavaScript code

### **2. Vercel Function Logs**
Vercel provides built-in logging for your API routes:

#### **Access Vercel Logs:**
1. Go to your Vercel dashboard
2. Select your project
3. Go to **Functions** tab
4. Click on any function to see logs
5. Check **Runtime Logs** for error details

#### **Real-time Logs:**
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# View real-time logs
vercel logs --follow
```

### **3. Backend API Logs (Google Cloud Run)**
Your backend runs on Google Cloud Run, so you can check logs there:

#### **Google Cloud Console:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **Cloud Run**
3. Select your backend service
4. Go to **Logs** tab
5. View real-time logs and errors

#### **Command Line:**
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Follow logs in real-time
gcloud logging tail "resource.type=cloud_run_revision"
```

## 🛠️ Debugging Steps

### **Step 1: Check Frontend Errors**
1. Open your Vercel deployment in browser
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Look for red error messages
5. Go to **Network** tab
6. Look for failed API calls (red status codes)

### **Step 2: Check Backend Errors**
1. Go to Google Cloud Console
2. Navigate to Cloud Run
3. Select your backend service
4. Check logs for error details

### **Step 3: Check API Connectivity**
1. Test your API directly:
```bash
curl https://customercaregpt-backend-xxxxx-uc.a.run.app/health
```

2. Check if CORS is working:
```bash
curl -H "Origin: https://customercaregpt-frontend.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/
```

## 🔧 Common 500 Error Causes

### **1. CORS Issues**
- **Symptom**: CORS errors in browser console
- **Fix**: Check CORS configuration in backend
- **Check**: `backend/app/middleware/security_headers.py`

### **2. Database Connection Issues**
- **Symptom**: Database connection errors in logs
- **Fix**: Check database URL and credentials
- **Check**: Environment variables in Cloud Run

### **3. Redis Connection Issues**
- **Symptom**: Redis connection errors in logs
- **Fix**: Check Redis URL and credentials
- **Check**: Environment variables in Cloud Run

### **4. Missing Environment Variables**
- **Symptom**: Configuration errors in logs
- **Fix**: Check all required environment variables
- **Check**: `env.example` for required variables

### **5. API Key Issues**
- **Symptom**: Authentication errors
- **Fix**: Check API keys (Gemini, Stripe, etc.)
- **Check**: Environment variables in Cloud Run

## 📊 Monitoring Setup

### **1. Frontend Error Tracking**
Add error tracking to your frontend:

```javascript
// In your frontend code
window.addEventListener('error', (event) => {
  console.error('Frontend Error:', event.error);
  // Send to error tracking service
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled Promise Rejection:', event.reason);
  // Send to error tracking service
});
```

### **2. Backend Error Tracking**
Your backend already has structured logging:

```python
# In your backend code
import structlog
logger = structlog.get_logger()

try:
    # Your code here
    pass
except Exception as e:
    logger.error("Error occurred", error=str(e), exc_info=True)
```

## 🚀 Quick Debugging Commands

### **Check Frontend Build:**
```bash
# Build frontend locally to check for errors
cd frontend
npm run build
```

### **Check Backend Health:**
```bash
# Test backend health
curl https://customercaregpt-backend-xxxxx-uc.a.run.app/health
```

### **Check API Endpoints:**
```bash
# Test API endpoints
curl https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/
```

### **Check CORS:**
```bash
# Test CORS
curl -H "Origin: https://customercaregpt-frontend.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1/
```

## 📱 Mobile Debugging

### **Chrome DevTools for Mobile:**
1. Connect your phone to computer via USB
2. Enable USB debugging on phone
3. Open Chrome DevTools
4. Go to **More tools** > **Remote devices**
5. Select your phone
6. Debug mobile version

### **Vercel Mobile Preview:**
1. Go to Vercel dashboard
2. Select your project
3. Go to **Deployments** tab
4. Click on any deployment
5. Use **Preview** button to test on mobile

## 🎯 Next Steps

1. **Deploy to Vercel** using the deployment scripts
2. **Check browser console** for errors
3. **Check Vercel logs** for function errors
4. **Check Cloud Run logs** for backend errors
5. **Fix any issues** found in logs
6. **Test all functionality** thoroughly

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Look for specific error messages
3. Check environment variables
4. Verify API connectivity
5. Test with curl commands

The debugging process on Vercel is actually better than localhost because you have more visibility into what's happening!
