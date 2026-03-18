#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║  ShieldSpace — Native Overlay (v2.2)                ║
║  Run inside ~/ShieldSpace: python3 native.py        ║
╚══════════════════════════════════════════════════════╝
Creates:
  1. ShieldOverlayService.java     — draws Samsung-style dim over all apps
  2. ShieldOverlayPlugin.java      — Capacitor JS bridge
  3. ShieldOverlayTile.java        — Quick Settings tile (1-tap toggle)
  4. ShieldNotificationService.java— notification listener
  5. overlay_icon.xml              — vector drawable for QS tile
  6. strings.xml                   — app strings
  Updates:
  7. MainActivity.java             — register plugin
  8. build.gradle                  — dependencies
  9. AndroidManifest.xml           — service declarations
  10. www/overlay-manager.js        — wire JS to native bridge
"""
import os

BASE = 'android/app/src/main'
JAVA = f'{BASE}/java/com/shieldspace/app'
RES  = f'{BASE}/res'

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.lstrip('\n'))
    print(f"  \033[92m✓\033[0m  {path}")

print('\n\033[92m🛡  Building native overlay layer...\033[0m\n')

# ══════════════════════════════════════════════════════
# 1. ShieldOverlayService.java
#    Samsung Extra Dim style — full screen WindowManager overlay
#    User triggers manually via QS tile or JS bridge
# ══════════════════════════════════════════════════════
write(f'{JAVA}/ShieldOverlayService.java', r"""
package com.shieldspace.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

/**
 * ShieldOverlayService
 *
 * Draws a Samsung Extra Dim-style overlay over all apps.
 * Uses WindowManager TYPE_APPLICATION_OVERLAY — the same mechanism
 * Samsung uses for Extra Dim, Blue Light Filter, etc.
 *
 * Overlay specs (matched to Samsung Extra Dim):
 *   - Full screen ARGB black layer
 *   - Default alpha: 0x99 (~60% opacity) — same as Samsung default
 *   - Non-interactive (touches pass through)
 *   - Sits above all apps, below system UI (status bar / nav bar)
 *   - Persists until user turns it off
 */
public class ShieldOverlayService extends Service {

    public static final String ACTION_SHOW   = "com.shieldspace.app.OVERLAY_SHOW";
    public static final String ACTION_HIDE   = "com.shieldspace.app.OVERLAY_HIDE";
    public static final String ACTION_TOGGLE = "com.shieldspace.app.OVERLAY_TOGGLE";
    public static final String ACTION_ALPHA  = "com.shieldspace.app.OVERLAY_ALPHA";
    public static final String EXTRA_ALPHA   = "alpha";

    private static final String CHANNEL_ID   = "shield_overlay";
    private static final int    NOTIF_ID     = 1001;
    private static final String PREFS_NAME   = "shield_overlay_prefs";
    private static final String PREF_ACTIVE  = "overlay_active";
    private static final String PREF_ALPHA   = "overlay_alpha";

    // Samsung Extra Dim default: 0x99 = 153 = ~60%
    private static final int DEFAULT_ALPHA = 0x99;

    private WindowManager windowManager;
    private View          overlayView;
    private boolean       isShowing = false;
    private int           currentAlpha = DEFAULT_ALPHA;

    @Override
    public void onCreate() {
        super.onCreate();
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        _createNotificationChannel();
        _startForeground();
        _restoreState();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) return START_STICKY;
        String action = intent.getAction();
        if (action == null) return START_STICKY;

        switch (action) {
            case ACTION_SHOW:
                currentAlpha = intent.getIntExtra(EXTRA_ALPHA, currentAlpha);
                _showOverlay();
                break;
            case ACTION_HIDE:
                _hideOverlay();
                break;
            case ACTION_TOGGLE:
                if (isShowing) _hideOverlay(); else _showOverlay();
                break;
            case ACTION_ALPHA:
                currentAlpha = intent.getIntExtra(EXTRA_ALPHA, currentAlpha);
                _updateAlpha();
                break;
        }
        return START_STICKY;
    }

    // ── Overlay control ──────────────────────────────
    private void _showOverlay() {
        if (isShowing) { _updateAlpha(); return; }
        overlayView = new View(this);
        overlayView.setBackgroundColor(Color.argb(currentAlpha, 0, 0, 0));

        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_SYSTEM_OVERLAY,
            // Non-interactive + not focusable = touches pass through
            WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
                | WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        );
        params.gravity = Gravity.TOP | Gravity.START;
        params.x = 0;
        params.y = 0;

        try {
            windowManager.addView(overlayView, params);
            isShowing = true;
            _saveState();
            _updateNotification(true);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void _hideOverlay() {
        if (!isShowing || overlayView == null) return;
        try {
            windowManager.removeView(overlayView);
        } catch (Exception ignored) {}
        overlayView = null;
        isShowing   = false;
        _saveState();
        _updateNotification(false);
    }

    private void _updateAlpha() {
        if (!isShowing || overlayView == null) return;
        overlayView.setBackgroundColor(Color.argb(currentAlpha, 0, 0, 0));
        _saveState();
    }

    // ── State persistence ────────────────────────────
    private void _saveState() {
        getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(PREF_ACTIVE, isShowing)
            .putInt(PREF_ALPHA, currentAlpha)
            .apply();
    }

    private void _restoreState() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        currentAlpha = prefs.getInt(PREF_ALPHA, DEFAULT_ALPHA);
        if (prefs.getBoolean(PREF_ACTIVE, false)) {
            _showOverlay();
        }
    }

    // ── Foreground notification ──────────────────────
    private void _createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                CHANNEL_ID, "Privacy Overlay",
                NotificationManager.IMPORTANCE_LOW
            );
            ch.setDescription("ShieldSpace privacy overlay is active");
            ch.setShowBadge(false);
            ((NotificationManager) getSystemService(NOTIFICATION_SERVICE))
                .createNotificationChannel(ch);
        }
    }

    private void _startForeground() {
        startForeground(NOTIF_ID, _buildNotification(false));
    }

    private void _updateNotification(boolean active) {
        ((NotificationManager) getSystemService(NOTIFICATION_SERVICE))
            .notify(NOTIF_ID, _buildNotification(active));
    }

    private Notification _buildNotification(boolean active) {
        // Tap notification = open ShieldSpace
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(
            this, 0, open,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        // Quick toggle action in notification
        Intent toggle = new Intent(this, ShieldOverlayService.class);
        toggle.setAction(ACTION_TOGGLE);
        PendingIntent togglePi = PendingIntent.getService(
            this, 1, toggle,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        return new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setContentTitle(active ? "🛡 Privacy Overlay ON" : "ShieldSpace")
            .setContentText(active ? "Screen dimmed for privacy. Tap to manage." : "Overlay ready — tap to activate.")
            .setContentIntent(pi)
            .addAction(android.R.drawable.ic_lock_lock,
                active ? "Turn Off" : "Turn On", togglePi)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setSilent(true)
            .build();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        _hideOverlay();
        super.onDestroy();
    }

    // ── Static helpers ───────────────────────────────
    public static void show(Context ctx, int alpha) {
        Intent i = new Intent(ctx, ShieldOverlayService.class);
        i.setAction(ACTION_SHOW);
        i.putExtra(EXTRA_ALPHA, alpha);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            ctx.startForegroundService(i);
        else ctx.startService(i);
    }

    public static void hide(Context ctx) {
        Intent i = new Intent(ctx, ShieldOverlayService.class);
        i.setAction(ACTION_HIDE);
        ctx.startService(i);
    }

    public static void toggle(Context ctx) {
        Intent i = new Intent(ctx, ShieldOverlayService.class);
        i.setAction(ACTION_TOGGLE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            ctx.startForegroundService(i);
        else ctx.startService(i);
    }
}
""")

# ══════════════════════════════════════════════════════
# 2. ShieldOverlayPlugin.java — Capacitor JS bridge
# ══════════════════════════════════════════════════════
write(f'{JAVA}/ShieldOverlayPlugin.java', r"""
package com.shieldspace.app;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * ShieldOverlayPlugin
 * Capacitor bridge — lets JavaScript control the native overlay service.
 *
 * JS usage:
 *   const { ShieldOverlay } = Capacitor.Plugins;
 *   await ShieldOverlay.show({ alpha: 0.6 });
 *   await ShieldOverlay.hide();
 *   await ShieldOverlay.toggle();
 *   const s = await ShieldOverlay.getStatus(); // { active: bool, alpha: int }
 *   await ShieldOverlay.requestPermission();
 */
@CapacitorPlugin(name = "ShieldOverlay")
public class ShieldOverlayPlugin extends Plugin {

    private static final String PREFS   = "shield_overlay_prefs";
    private static final int    DEFAULT_ALPHA = 0x99; // ~60%

    @PluginMethod
    public void show(PluginCall call) {
        float alphaFloat = call.getFloat("alpha", 0.6f);
        int alpha = Math.round(alphaFloat * 255);
        alpha = Math.max(0, Math.min(255, alpha));
        Context ctx = getContext();
        if (_hasPermission(ctx)) {
            ShieldOverlayService.show(ctx, alpha);
            JSObject r = new JSObject();
            r.put("success", true);
            call.resolve(r);
        } else {
            call.reject("PERMISSION_DENIED", "Draw over apps permission not granted");
        }
    }

    @PluginMethod
    public void hide(PluginCall call) {
        ShieldOverlayService.hide(getContext());
        JSObject r = new JSObject();
        r.put("success", true);
        call.resolve(r);
    }

    @PluginMethod
    public void toggle(PluginCall call) {
        Context ctx = getContext();
        if (_hasPermission(ctx)) {
            ShieldOverlayService.toggle(ctx);
            JSObject r = new JSObject();
            r.put("success", true);
            call.resolve(r);
        } else {
            call.reject("PERMISSION_DENIED", "Draw over apps permission not granted");
        }
    }

    @PluginMethod
    public void getStatus(PluginCall call) {
        SharedPreferences prefs = getContext()
            .getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        boolean active = prefs.getBoolean("overlay_active", false);
        int alpha      = prefs.getInt("overlay_alpha", DEFAULT_ALPHA);
        boolean hasPerm = _hasPermission(getContext());
        JSObject r = new JSObject();
        r.put("active",      active);
        r.put("alpha",       alpha);
        r.put("hasPermission", hasPerm);
        call.resolve(r);
    }

    @PluginMethod
    public void requestPermission(PluginCall call) {
        Context ctx = getContext();
        if (_hasPermission(ctx)) {
            JSObject r = new JSObject();
            r.put("granted", true);
            call.resolve(r);
            return;
        }
        // Open Android system settings for SYSTEM_ALERT_WINDOW
        Intent intent = new Intent(
            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
            Uri.parse("package:" + ctx.getPackageName())
        );
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        ctx.startActivity(intent);
        JSObject r = new JSObject();
        r.put("granted", false);
        r.put("message", "Opened Android settings — enable 'Display over other apps' for ShieldSpace");
        call.resolve(r);
    }

    @PluginMethod
    public void configure(PluginCall call) {
        // Accept config from JS overlay manager
        String mode = call.getString("mode", "off");
        float alphaFloat = call.getFloat("dimAmount", 0.6f);
        int alpha = Math.round(alphaFloat * 255);
        Context ctx = getContext();
        if ("off".equals(mode)) {
            ShieldOverlayService.hide(ctx);
        } else if (_hasPermission(ctx)) {
            ShieldOverlayService.show(ctx, alpha);
        }
        JSObject r = new JSObject();
        r.put("success", true);
        call.resolve(r);
    }

    private boolean _hasPermission(Context ctx) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            return Settings.canDrawOverlays(ctx);
        }
        return true;
    }
}
""")

# ══════════════════════════════════════════════════════
# 3. ShieldOverlayTile.java — Quick Settings Tile
#    One-tap toggle from notification shade (Android 7+)
# ══════════════════════════════════════════════════════
write(f'{JAVA}/ShieldOverlayTile.java', r"""
package com.shieldspace.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.drawable.Icon;
import android.os.Build;
import android.service.quicksettings.Tile;
import android.service.quicksettings.TileService;
import androidx.annotation.RequiresApi;

/**
 * ShieldOverlayTile
 * Adds ShieldSpace to the Android Quick Settings panel.
 * User can pull down notification shade and tap once to
 * toggle privacy overlay — exactly like Samsung Extra Dim tile.
 */
@RequiresApi(api = Build.VERSION_CODES.N)
public class ShieldOverlayTile extends TileService {

    private static final String PREFS  = "shield_overlay_prefs";
    private static final String ACTIVE = "overlay_active";

    @Override
    public void onTileAdded() {
        super.onTileAdded();
        _syncTile();
    }

    @Override
    public void onStartListening() {
        super.onStartListening();
        _syncTile();
    }

    @Override
    public void onClick() {
        super.onClick();
        Context ctx = getApplicationContext();
        ShieldOverlayService.toggle(ctx);
        // Small delay to let service update prefs before we read them
        getQsTile().getIcon(); // keep reference
        new android.os.Handler().postDelayed(this::_syncTile, 300);
    }

    private void _syncTile() {
        Tile tile = getQsTile();
        if (tile == null) return;
        SharedPreferences prefs = getApplicationContext()
            .getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        boolean active = prefs.getBoolean(ACTIVE, false);
        tile.setState(active ? Tile.STATE_ACTIVE : Tile.STATE_INACTIVE);
        tile.setLabel("Privacy Dim");
        tile.setSubtitle(active ? "On" : "Off");
        tile.setIcon(Icon.createWithResource(this, android.R.drawable.ic_lock_lock));
        tile.updateTile();
    }
}
""")

# ══════════════════════════════════════════════════════
# 4. ShieldNotificationService.java
#    Listens for notifications — can trigger overlay
# ══════════════════════════════════════════════════════
write(f'{JAVA}/ShieldNotificationService.java', r"""
package com.shieldspace.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

/**
 * ShieldNotificationService
 * Notification listener — detects when notifications arrive.
 * If overlay mode is set to NOTIFICATIONS, triggers the dim.
 * User controls this from the overlay manager in the app.
 */
public class ShieldNotificationService extends NotificationListenerService {

    private static final String PREFS = "shield_overlay_prefs";

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        SharedPreferences prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String mode = prefs.getString("overlay_mode", "off");
        // Only auto-trigger if user chose notifications mode
        if ("notifications".equals(mode)) {
            int alpha = prefs.getInt("overlay_alpha", 0x99);
            ShieldOverlayService.show(getApplicationContext(), alpha);
            // Auto-hide after 8 seconds
            new android.os.Handler().postDelayed(
                () -> ShieldOverlayService.hide(getApplicationContext()),
                8000
            );
        }
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        // Nothing needed here
    }
}
""")

# ══════════════════════════════════════════════════════
# 5. MainActivity.java — register plugin
# ══════════════════════════════════════════════════════
write(f'{JAVA}/MainActivity.java', r"""
package com.shieldspace.app;

import android.os.Bundle;
import android.view.WindowManager;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Register native plugins BEFORE super.onCreate
        registerPlugin(ShieldOverlayPlugin.class);
        super.onCreate(savedInstanceState);

        // Block screenshots & screen recording
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_SECURE,
            WindowManager.LayoutParams.FLAG_SECURE
        );

        // Start overlay service so it's ready in background
        ShieldOverlayService.hide(this); // starts service in OFF state
    }

    @Override
    protected void onPause() {
        super.onPause();
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }
}
""")

# ══════════════════════════════════════════════════════
# 6. Drawable — overlay tile icon (shield with A)
# ══════════════════════════════════════════════════════
write(f'{RES}/drawable/ic_shield_overlay.xml', r"""
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
  <path
    android:fillColor="@android:color/white"
    android:pathData="M12,2L4,5v7c0,5.25 3.6,10.15 8,11.5C16.4,22.15 20,17.25 20,12V5L12,2z
                     M14.5,17h-1.8l-0.7-2H12h-0.7l-0.7,2H8.8L12,8L14.5,17z
                     M11.5,13.5h1l-0.5-2.5L11.5,13.5z"/>
</vector>
""")

# ══════════════════════════════════════════════════════
# 7. strings.xml
# ══════════════════════════════════════════════════════
write(f'{RES}/values/strings.xml', r"""
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">ShieldSpace</string>
    <string name="title_activity_main">ShieldSpace</string>
    <string name="overlay_tile_label">Privacy Dim</string>
    <string name="overlay_channel_name">Privacy Overlay</string>
    <string name="overlay_channel_desc">ShieldSpace privacy overlay status</string>
</resources>
""")

# ══════════════════════════════════════════════════════
# 8. build.gradle — add foreground service + tile deps
# ══════════════════════════════════════════════════════
write('android/app/build.gradle', r"""
apply plugin: 'com.android.application'

android {
    namespace "com.shieldspace.app"
    compileSdk 34

    defaultConfig {
        applicationId "com.shieldspace.app"
        minSdk 24
        targetSdk 34
        versionCode 3
        versionName "2.2.0"
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
        debug {
            applicationIdSuffix ".debug"
            debuggable true
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }

    packagingOptions {
        resources {
            excludes += ['META-INF/LICENSE', 'META-INF/LICENSE.txt']
        }
    }
}

repositories {
    google()
    mavenCentral()
}

dependencies {
    implementation fileTree(include: ['*.jar'], dir: 'libs')
    implementation "androidx.appcompat:appcompat:1.6.1"
    implementation "androidx.core:core:1.12.0"
    implementation "androidx.core:core-ktx:1.12.0"

    // Biometric
    implementation "androidx.biometric:biometric:1.2.0-alpha05"

    // Security crypto
    implementation "androidx.security:security-crypto:1.1.0-alpha06"

    // Capacitor
    implementation project(':capacitor-android')
}

apply from: 'capacitor.build.gradle'
""")

# ══════════════════════════════════════════════════════
# 9. AndroidManifest.xml — full with all services
# ══════════════════════════════════════════════════════
write('android/app/src/main/AndroidManifest.xml', r"""
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.shieldspace.app">

  <!-- Network -->
  <uses-permission android:name="android.permission.INTERNET"/>
  <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>

  <!-- Camera -->
  <uses-permission android:name="android.permission.CAMERA"/>
  <uses-feature android:name="android.hardware.camera"       android:required="false"/>
  <uses-feature android:name="android.hardware.camera.front" android:required="false"/>

  <!-- Storage -->
  <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"  android:maxSdkVersion="32"/>
  <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29"/>
  <uses-permission android:name="android.permission.READ_MEDIA_IMAGES"/>
  <uses-permission android:name="android.permission.READ_MEDIA_VIDEO"/>
  <uses-permission android:name="android.permission.READ_MEDIA_AUDIO"/>

  <!-- System overlay (draw over other apps) — THE KEY PERMISSION -->
  <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>

  <!-- Foreground service (keeps overlay alive) -->
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE"/>

  <!-- Biometric -->
  <uses-permission android:name="android.permission.USE_BIOMETRIC"/>
  <uses-permission android:name="android.permission.USE_FINGERPRINT"/>
  <uses-feature android:name="android.hardware.fingerprint" android:required="false"/>

  <!-- Notifications -->
  <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
  <uses-permission android:name="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"/>

  <!-- Motion (shake-to-lock) -->
  <uses-feature android:name="android.hardware.sensor.accelerometer" android:required="false"/>

  <!-- Vibration + wake lock -->
  <uses-permission android:name="android.permission.VIBRATE"/>
  <uses-permission android:name="android.permission.WAKE_LOCK"/>

  <application
    android:allowBackup="false"
    android:icon="@mipmap/ic_launcher"
    android:label="@string/app_name"
    android:theme="@style/AppTheme"
    android:hardwareAccelerated="true"
    android:usesCleartextTraffic="false">

    <!-- Main activity -->
    <activity
      android:name=".MainActivity"
      android:label="@string/app_name"
      android:launchMode="singleTask"
      android:configChanges="orientation|keyboardHidden|keyboard|screenSize|locale|uiMode"
      android:windowSoftInputMode="adjustResize"
      android:exported="true"
      android:screenOrientation="portrait">
      <intent-filter>
        <action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
      </intent-filter>
    </activity>

    <!-- Privacy overlay foreground service -->
    <service
      android:name=".ShieldOverlayService"
      android:foregroundServiceType="specialUse"
      android:exported="false"/>

    <!-- Quick Settings tile — appears in Android notification shade -->
    <service
      android:name=".ShieldOverlayTile"
      android:icon="@drawable/ic_shield_overlay"
      android:label="@string/overlay_tile_label"
      android:permission="android.permission.BIND_QUICK_SETTINGS_TILE"
      android:exported="true">
      <intent-filter>
        <action android:name="android.service.quicksettings.action.QS_TILE"/>
      </intent-filter>
      <meta-data
        android:name="android.service.quicksettings.TOGGLEABLE_TILE"
        android:value="true"/>
    </service>

    <!-- Notification listener service -->
    <service
      android:name=".ShieldNotificationService"
      android:label="ShieldSpace Overlay"
      android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"
      android:exported="true">
      <intent-filter>
        <action android:name="android.service.notification.NotificationListenerService"/>
      </intent-filter>
    </service>

    <!-- File provider -->
    <provider
      android:name="androidx.core.content.FileProvider"
      android:authorities="${applicationId}.fileprovider"
      android:exported="false"
      android:grantUriPermissions="true">
      <meta-data
        android:name="android.support.FILE_PROVIDER_PATHS"
        android:resource="@xml/file_paths"/>
    </provider>

  </application>
</manifest>
""")

# ══════════════════════════════════════════════════════
# 10. file_paths.xml (required by FileProvider)
# ══════════════════════════════════════════════════════
write(f'{RES}/xml/file_paths.xml', r"""
<?xml version="1.0" encoding="utf-8"?>
<paths>
    <external-path name="external_files" path="."/>
    <cache-path name="cache_files" path="."/>
</paths>
""")

# ══════════════════════════════════════════════════════
# 11. Update www/overlay-manager.js — wire to native
# ══════════════════════════════════════════════════════
patch = r"""

// ── v2.2: Wire to native ShieldOverlayPlugin ─────────
(async function _initNativeOverlay() {
  const native = window.Capacitor?.Plugins?.ShieldOverlay;
  if (!native) return; // PWA mode — JS overlay only

  // Sync status from native on load
  try {
    const status = await native.getStatus();
    if (status.active) {
      const dot = document.getElementById('overlayDot');
      const txt = document.getElementById('overlayTxt');
      if (dot) dot.className = 'status-dot on';
      if (txt) txt.textContent = 'active';
    }
  } catch(e) {}

  // Expose toggle to window so QS tile changes reflect in UI
  window.ShieldNativeOverlay = {
    async show(alpha = 0.6) {
      try {
        await native.show({ alpha });
        _updateOverlayStatus(true);
      } catch(e) {
        // Permission not granted — request it
        await native.requestPermission();
      }
    },
    async hide() {
      try {
        await native.hide();
        _updateOverlayStatus(false);
      } catch(e) {}
    },
    async toggle() {
      try {
        await native.toggle();
        const s = await native.getStatus();
        _updateOverlayStatus(s.active);
      } catch(e) {
        await native.requestPermission();
      }
    },
    async requestPermission() {
      return native.requestPermission();
    }
  };

  function _updateOverlayStatus(active) {
    const dot = document.getElementById('overlayDot');
    const txt = document.getElementById('overlayTxt');
    if (dot) dot.className = 'status-dot ' + (active ? 'on' : 'off');
    if (txt) txt.textContent = active ? 'active' : 'off';
  }
})();
"""

with open('www/overlay-manager.js', 'a', encoding='utf-8') as f:
    f.write(patch)
print("  \033[94m+\033[0m  www/overlay-manager.js (native bridge appended)")

print(f"""
\033[92m╔══════════════════════════════════════════════════════╗
║  ✅  Native overlay layer built — 11 files           ║
╚══════════════════════════════════════════════════════╝\033[0m

Now push to GitHub — Actions will build the APK:

  git add .
  git commit -m "feat: native Samsung-style overlay, QS tile, notification listener"
  git push origin main

\033[96mWhat this adds:\033[0m
  🛡  Full-screen dim over ALL apps (WindowManager)
  📲  Quick Settings tile — one tap from notification shade
  🔔  Notification listener — optional auto-dim on notifs
  🔌  Capacitor JS bridge — app controls native service
  💾  State persists — overlay survives app close/reopen

\033[93mFirst install:\033[0m
  After installing APK → ShieldSpace will prompt you to
  grant "Display over other apps" in Android Settings.
  After that — the overlay works system-wide instantly.
""")
