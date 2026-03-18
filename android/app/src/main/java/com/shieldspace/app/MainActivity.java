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
