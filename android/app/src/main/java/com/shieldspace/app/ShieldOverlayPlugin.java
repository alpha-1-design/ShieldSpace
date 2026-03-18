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
