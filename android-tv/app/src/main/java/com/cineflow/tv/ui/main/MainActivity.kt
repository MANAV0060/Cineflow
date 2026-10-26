package com.cineflow.tv.ui.main

import android.content.Intent
import android.os.Bundle
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.lifecycleScope
import com.cineflow.tv.R
import com.cineflow.tv.ui.update.UpdateActivity
import com.cineflow.tv.util.AppUpdater
import com.cineflow.tv.util.PreferencesManager
import kotlinx.coroutines.launch

class MainActivity : FragmentActivity() {

    private lateinit var updater: AppUpdater
    private lateinit var prefs: PreferencesManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        updater = AppUpdater(this)
        prefs = PreferencesManager(this)

        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.main_browse_fragment, MainFragment())
                .commitNow()
        }

        // Silent background check for updates on startup
        if (prefs.autoUpdateEnabled) {
            checkBackgroundUpdates()
        }
    }

    private fun checkBackgroundUpdates() {
        lifecycleScope.launch {
            val update = updater.checkForUpdates()
            if (update != null && !isFinishing) {
                val intent = Intent(this@MainActivity, UpdateActivity::class.java).apply {
                    putExtra(UpdateActivity.EXTRA_UPDATE_INFO, update)
                }
                startActivity(intent)
            }
        }
    }
}
