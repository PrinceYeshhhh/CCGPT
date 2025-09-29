# 🚀 CustomerCareGPT Frontend - Vercel Deployment Guide

## Overview
This guide will help you deploy your React + Vite frontend to Vercel, which is the perfect platform for your CustomerCareGPT application.

## 🎯 Why Vercel is Perfect for Your Frontend

### **✅ Key Benefits:**
- **Zero Configuration** - Works out of the box with Vite + React
- **Automatic Deployments** - Deploy on every git push
- **Global CDN** - Fast loading worldwide
- **Free Tier** - Generous limits for personal projects
- **Custom Domains** - Easy domain setup
- **Environment Variables** - Secure configuration
- **Preview Deployments** - Test before going live

### **💰 Vercel Pricing:**
- **Hobby Plan**: FREE (perfect for your project)
  - 100GB bandwidth/month
  - Unlimited deployments
  - Custom domains
  - Automatic HTTPS

## 🛠️ Prerequisites

### **Required:**
1. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
2. **GitHub/GitLab/Bitbucket** - Your code repository
3. **Google Cloud Run Backend** - Already deployed

### **Optional:**
1. **Custom Domain** - If you have one
2. **Vercel CLI** - For local development

## 🚀 Deployment Methods

### **Method 1: Vercel Dashboard (Recommended)**

#### **Step 1: Prepare Your Repository**
```bash
# Make sure your frontend is in a git repository
cd frontend
git init
git add .
git commit -m "Initial commit"
git push origin main
```

#### **Step 2: Connect to Vercel**
1. Go to [vercel.com](https://vercel.com)
2. Click **"New Project"**
3. Import your repository
4. Select the `frontend` folder as root directory

#### **Step 3: Configure Build Settings**
- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

#### **Step 4: Set Environment Variables**
In Vercel dashboard, go to **Settings > Environment Variables**:

```bash
# Production Environment
VITE_API_URL=https://your-backend-url.run.app/api/v1
VITE_WS_URL=wss://your-backend-url.run.app/ws

# Preview Environment (optional)
VITE_API_URL=https://your-preview-backend-url.run.app/api/v1
VITE_WS_URL=wss://your-preview-backend-url.run.app/ws
```

#### **Step 5: Deploy**
Click **"Deploy"** and wait for the build to complete!

### **Method 2: Vercel CLI**

#### **Step 1: Install Vercel CLI**
```bash
npm i -g vercel
```

#### **Step 2: Login to Vercel**
```bash
vercel login
```

#### **Step 3: Deploy from Frontend Directory**
```bash
cd frontend
vercel
```

#### **Step 4: Set Environment Variables**
```bash
vercel env add VITE_API_URL
vercel env add VITE_WS_URL
```

#### **Step 5: Deploy to Production**
```bash
vercel --prod
```

## 🔧 Configuration Files

### **vercel.json** (Already Created)
```json
{
  "version": 2,
  "name": "customercaregpt-frontend",
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "env": {
    "VITE_API_URL": "@vite_api_url",
    "VITE_WS_URL": "@vite_ws_url"
  }
}
```

### **Environment Variables Setup**
```bash
# In Vercel Dashboard or CLI
VITE_API_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1
VITE_WS_URL=wss://customercaregpt-backend-xxxxx-uc.a.run.app/ws
```

## 🌐 Custom Domain Setup

### **Step 1: Add Domain in Vercel**
1. Go to **Settings > Domains**
2. Add your domain (e.g., `customercaregpt.com`)
3. Follow DNS configuration instructions

### **Step 2: Update Environment Variables**
```bash
# Update API URLs to use your custom domain
VITE_API_URL=https://api.customercaregpt.com/api/v1
VITE_WS_URL=wss://api.customercaregpt.com/ws
```

## 🔄 Automatic Deployments

### **GitHub Integration**
1. Connect your GitHub repository
2. Every push to `main` branch = automatic production deployment
3. Every pull request = automatic preview deployment

### **Branch Strategy**
```bash
main branch     → Production deployment
develop branch  → Preview deployment
feature/*       → Preview deployment
```

## 📊 Monitoring & Analytics

### **Vercel Analytics**
```bash
# Install Vercel Analytics
npm install @vercel/analytics

# Add to your main.tsx
import { Analytics } from '@vercel/analytics/react';

function App() {
  return (
    <>
      <YourApp />
      <Analytics />
    </>
  );
}
```

### **Performance Monitoring**
- **Core Web Vitals** - Automatic monitoring
- **Build Logs** - Detailed build information
- **Function Logs** - Serverless function logs
- **Real User Monitoring** - User experience metrics

## 🛡️ Security Features

### **Built-in Security**
- **Automatic HTTPS** - SSL certificates
- **Security Headers** - XSS protection, etc.
- **DDoS Protection** - Built-in protection
- **Environment Variables** - Secure configuration

### **Custom Security Headers**
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        }
      ]
    }
  ]
}
```

## 🚀 Performance Optimizations

### **Automatic Optimizations**
- **Image Optimization** - Automatic WebP conversion
- **Code Splitting** - Automatic bundle splitting
- **Tree Shaking** - Remove unused code
- **Minification** - Compress JavaScript/CSS

### **CDN Benefits**
- **Global Edge Network** - Fast loading worldwide
- **Automatic Caching** - Static assets cached
- **HTTP/2** - Modern protocol support
- **Brotli Compression** - Better compression

## 🔧 Development Workflow

### **Local Development**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### **Vercel CLI Commands**
```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# View deployment logs
vercel logs

# Check deployment status
vercel ls
```

## 📈 Scaling & Limits

### **Vercel Hobby Plan Limits**
- **100GB bandwidth/month**
- **Unlimited deployments**
- **Unlimited static sites**
- **Custom domains**
- **Automatic HTTPS**

### **When to Upgrade**
- **Pro Plan** ($20/month) - For commercial use
- **Team Plan** - For collaboration
- **Enterprise Plan** - For large organizations

## 🔍 Troubleshooting

### **Common Issues**

#### **Build Failures**
```bash
# Check build logs in Vercel dashboard
# Common fixes:
npm install
npm run build
```

#### **Environment Variables Not Working**
```bash
# Make sure variables start with VITE_
VITE_API_URL=https://your-backend-url.com
VITE_WS_URL=wss://your-backend-url.com
```

#### **CORS Issues**
```bash
# Update your backend CORS settings
CORS_ORIGINS=https://your-vercel-domain.vercel.app
```

### **Debug Commands**
```bash
# Check Vercel CLI version
vercel --version

# View project information
vercel inspect

# Check environment variables
vercel env ls
```

## 🎯 Next Steps After Deployment

### **1. Test Your Deployment**
- Visit your Vercel URL
- Test all functionality
- Check mobile responsiveness
- Verify API connections

### **2. Set Up Monitoring**
- Enable Vercel Analytics
- Set up error tracking (Sentry)
- Monitor Core Web Vitals

### **3. Configure Custom Domain**
- Add your domain in Vercel
- Update DNS settings
- Test HTTPS certificate

### **4. Set Up CI/CD**
- Connect GitHub repository
- Configure branch protection
- Set up preview deployments

## 🎉 Expected Results

After deployment, you'll have:

- **Production URL**: `https://customercaregpt-frontend.vercel.app`
- **Automatic Deployments**: On every git push
- **Global CDN**: Fast loading worldwide
- **HTTPS**: Automatic SSL certificate
- **Monitoring**: Built-in analytics
- **Custom Domain**: Easy to set up

## 💡 Pro Tips

1. **Use Preview Deployments** - Test before going live
2. **Monitor Performance** - Use Vercel Analytics
3. **Optimize Images** - Use Vercel's image optimization
4. **Set Up Error Tracking** - Use Sentry or similar
5. **Use Environment Variables** - Keep secrets secure

Your CustomerCareGPT frontend will be perfectly hosted on Vercel with automatic deployments, global CDN, and zero configuration! 🚀
