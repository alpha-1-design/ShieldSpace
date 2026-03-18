# 🛡 ShieldSpace v2.0

> AES-256 encrypted vault · private browser · shake-to-lock · intruder selfie · panic mode · self-destruct

---

## 🚀 First-time Termux Setup

```bash
# Install Node + Git (if not done)
pkg install nodejs git -y

# Go into project
cd ShieldSpace

# Install Capacitor
npm install

# Init Capacitor (first time only)
npx cap init ShieldSpace com.shieldspace.app --web-dir www

# Add Android platform
npx cap add android

# Sync web files
npx cap sync android

# Open in Android Studio (on PC)
# npx cap open android
```

---

## 📲 Push to GitHub

```bash
cd ~/ShieldSpace
git init
git add .
git commit -m "🛡 ShieldSpace v2.0 — initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ShieldSpace.git
git push -u origin main
```

---

## ⚡ Features

| Feature | How it works |
|---------|-------------|
| AES-256-GCM Vault | Web Crypto API, PBKDF2-SHA256 key from PIN |
| Intruder Selfie | 3 wrong PINs → front camera photo → encrypted |
| Shake to Lock | DeviceMotion API threshold detection |
| Self-Destruct | 5 wrong PINs → wipe all data |
| PIN Lockout | 3 wrong → 2 min cooldown |
| Privacy Blur | Vignette after 4s inactivity |
| Panic Mode | Shows fake Calculator |
| Decoy PIN | Secondary PIN opens fake vault |
| Secure Browser | Session wiped on tab switch |
| Encrypted Clipboard | Auto-clears clipboard in 30s |
| Vault Search | Full-text search (in-memory only) |
| Backup/Restore | Export .shieldspace file, import back |
| Stealth Tab | Browser tab shows "Battery ⚡ 78%" |
| Biometric | WebAuthn fingerprint unlock |
| Screenshot Block | FLAG_SECURE (Android native) |
| Offline PWA | Service worker caches all assets |

---

## 🔐 Default PIN: `1234` — Change immediately in Settings!
