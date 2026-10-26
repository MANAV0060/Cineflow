package com.cineflow.tv.ui.update

import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.lifecycleScope
import com.cineflow.tv.R
import com.cineflow.tv.data.model.UpdateInfo
import com.cineflow.tv.util.AppUpdater
import kotlinx.coroutines.launch

class UpdateActivity : FragmentActivity() {

    companion object {
        const val EXTRA_UPDATE_INFO = "extra_update_info"
    }

    private lateinit var updater: AppUpdater
    private var updateInfo: UpdateInfo? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_update)

        updater = AppUpdater(this)
        updateInfo = intent.getSerializableExtra(EXTRA_UPDATE_INFO) as? UpdateInfo

        if (updateInfo == null) {
            finish()
            return
        }

        val versionText = findViewById<TextView>(R.id.update_version)
        val changelogText = findViewById<TextView>(R.id.update_changelog)
        val progressLayout = findViewById<LinearLayout>(R.id.update_progress_layout)
        val progressBar = findViewById<ProgressBar>(R.id.update_progress_bar)
        val progressText = findViewById<TextView>(R.id.update_progress_text)
        val buttonsLayout = findViewById<LinearLayout>(R.id.update_buttons_layout)
        val btnLater = findViewById<Button>(R.id.btn_update_later)
        val btnNow = findViewById<Button>(R.id.btn_update_now)

        versionText.text = "Version ${updateInfo?.latestVersionName} (Build ${updateInfo?.latestVersionCode})"

        if (!updateInfo?.changelog.isNullOrEmpty()) {
            changelogText.text = updateInfo?.changelog?.joinToString("\n") { "• $it" }
        }

        // Set focus to the "Update Now" button by default for TV remote
        btnNow.requestFocus()

        btnLater.setOnClickListener {
            finish()
        }

        btnNow.setOnClickListener {
            // Hide buttons and show progress bar
            buttonsLayout.visibility = View.GONE
            progressLayout.visibility = View.VISIBLE

            lifecycleScope.launch {
                val success = updater.downloadAndInstallApk(updateInfo!!) { percent ->
                    progressBar.progress = percent
                    progressText.text = "Downloading Cineflow TV Update… $percent%"
                }

                if (!success) {
                    Toast.makeText(this@UpdateActivity, "Download failed. Please check network connection.", Toast.LENGTH_LONG).show()
                    buttonsLayout.visibility = View.VISIBLE
                    progressLayout.visibility = View.GONE
                } else {
                    finish()
                }
            }
        }
    }
}
