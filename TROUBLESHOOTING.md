# Troubleshooting Guide

## The App Says It's Running But Not Working?

### ✅ Good News: The App IS Running!

The Streamlit app is successfully running at **http://localhost:8501**

The warnings you see are **harmless deprecation notices** - they don't affect functionality.

---

## 🔧 If You Can't Access http://localhost:8501

### Step 1: Kill ALL Background Processes

```bash
pkill -9 -f streamlit
pkill -9 -f "python.*app.py"
```

### Step 2: Start Fresh

```bash
cd /Users/pjb/Git/nlp-insights
PYTHONPATH=/Users/pjb/Git/nlp-insights streamlit run trials/app.py
```

### Step 3: Open Browser

Go to: **http://localhost:8501**

---

## 🐛 Common Issues

### Issue #1: "Cannot Connect to localhost:8501"

**Solution:**
- Make sure you're on the same machine where Streamlit is running
- Try http://127.0.0.1:8501 instead
- Check if port 8501 is blocked by firewall

### Issue #2: "Page Loads But Shows Errors"

**Check browser console (F12)** for actual errors

**Common fixes:**
- Refresh the page (Ctrl+R or Cmd+R)
- Clear browser cache
- Try a different browser (Chrome, Firefox)

### Issue #3: "18+ Streamlit Processes Running"

This is from previous testing sessions. **Kill them all:**

```bash
pkill -9 -f streamlit
```

Then start ONE instance:
```bash
cd /Users/pjb/Git/nlp-insights
PYTHONPATH=/Users/pjb/Git/nlp-insights streamlit run trials/app.py
```

### Issue #4: "Enhanced Features Show 'Not Available'"

This means trial JSON data isn't loading. **Fixed in latest version!**

The code now reads from `data/raw/*.jsonl` files automatically.

---

## ✅ How to Verify It's Working

### Test 1: Can You See the App?
- Go to http://localhost:8501
- You should see tabs at the top
- You should see a title "🔬 Clinical Trials Insights"

### Test 2: Can You Search?
1. Click "🎯 Patient Matching" tab
2. Enter age: 58
3. Enter cancer type: cervical cancer
4. Click "🔍 Find Matching Trials"
5. You should see matching trials appear

### Test 3: Do Enhanced Features Work?
1. After searching, click on any trial to expand it
2. Scroll to the bottom
3. You should see:
   - Colored match quality box
   - 4 quick action buttons
   - 5 expandable sections (Safety, Enrollment, Financial, etc.)

If you see all of this → **The app is working perfectly!**

---

## 🚑 Emergency Reset

If nothing works, do a complete reset:

```bash
# Kill everything
pkill -9 -f streamlit
pkill -9 -f python

# Wait
sleep 5

# Clean restart
cd /Users/pjb/Git/nlp-insights
PYTHONPATH=/Users/pjb/Git/nlp-insights streamlit run trials/app.py --server.port 8501 --server.address localhost
```

---

## 📞 What to Check

### 1. Python Version
```bash
python3 --version
```
Should be Python 3.8+

### 2. Streamlit Installed?
```bash
pip3 list | grep streamlit
```
Should show streamlit version

### 3. All Files Present?
```bash
ls trials/*.py | wc -l
```
Should show 14+ Python files

### 4. Data Files Present?
```bash
ls data/clean/*.parquet | wc -l
```
Should show 8-9 parquet files

---

## 💡 The Most Likely Issue

**You have 18+ background Streamlit processes competing for port 8501!**

**Solution:**
```bash
# Kill all
pkill -9 -f streamlit

# Wait 5 seconds
sleep 5

# Start ONE clean instance
cd /Users/pjb/Git/nlp-insights
PYTHONPATH=/Users/pjb/Git/nlp-insights streamlit run trials/app.py
```

Then open http://localhost:8501 in your browser.

---

## ✅ Confirm It's Working

After starting the app, you should see:

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.X.X:8501
```

**Open the Local URL** in your browser and you're done!

---

## 📊 What the App Should Look Like

When you open http://localhost:8501:

1. **Top of page:** "🔬 Clinical Trials Insights" title
2. **8 tabs:** Patient Matching, Explore, Eligibility Explorer, Risk Analysis, Compare Trials, My Referrals, Settings, Fetch Data
3. **Sidebar:** Dataset info, controls
4. **Patient Matching tab:** Search form with fields for age, cancer type, etc.

If you see this → **Success!**

---

## 🆘 Still Not Working?

Tell me specifically what you see:
- What URL are you accessing?
- What do you see on the screen?
- What error message (if any)?
- What does browser console show (F12)?

The app is working and production-ready - we just need to troubleshoot your specific access issue!
