package com.cineflow.tv.ui.player

import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.KeyEvent
import android.view.View
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.annotation.OptIn
import androidx.fragment.app.FragmentActivity
import androidx.media3.common.MediaItem as ExoMediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.cineflow.tv.R
import com.cineflow.tv.data.model.MediaItem
import com.cineflow.tv.util.PreferencesManager
import java.util.Locale

class PlaybackActivity : FragmentActivity() {

    companion object {
        const val EXTRA_MEDIA = "extra_media"
        const val EXTRA_START_POSITION = "extra_start_position"
        private const val SEEK_STEP_MS = 10000L // 10s step
    }

    private lateinit var playerView: PlayerView
    private lateinit var topHud: LinearLayout
    private lateinit var bottomHud: LinearLayout
    private lateinit var seekFeedbackLayout: LinearLayout
    private lateinit var seekFeedbackText: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var timeCurrentText: TextView
    private lateinit var timeTotalText: TextView
    private lateinit var titleText: TextView
    private lateinit var subtitleText: TextView

    private var player: ExoPlayer? = null
    private var mediaItem: MediaItem? = null
    private var startPositionMs: Long = 0L

    private val handler = Handler(Looper.getMainLooper())
    private lateinit var prefs: PreferencesManager

    // Cumulative seeking state
    private var accumulatedSeekSeconds = 0
    private var seekCommitRunnable = Runnable { commitSeek() }
    private var hideHudRunnable = Runnable { hideHud() }
    private var progressUpdateRunnable: Runnable? = null

    @OptIn(UnstableApi::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_playback)

        mediaItem = intent.getSerializableExtra(EXTRA_MEDIA) as? MediaItem
        startPositionMs = intent.getLongExtra(EXTRA_START_POSITION, 0L)
        prefs = PreferencesManager(this)

        initViews()
        initPlayer()
    }

    private fun initViews() {
        playerView = findViewById(R.id.player_view)
        topHud = findViewById(R.id.top_hud_layout)
        bottomHud = findViewById(R.id.bottom_hud_layout)
        seekFeedbackLayout = findViewById(R.id.seek_feedback_layout)
        seekFeedbackText = findViewById(R.id.seek_feedback_text)
        progressBar = findViewById(R.id.player_progress_bar)
        timeCurrentText = findViewById(R.id.player_time_current)
        timeTotalText = findViewById(R.id.player_time_total)
        titleText = findViewById(R.id.player_media_title)
        subtitleText = findViewById(R.id.player_media_subtitle)

        playerView.useController = false // Custom Cineflow TV remote HUD
        titleText.text = mediaItem?.title ?: "Cineflow"
        subtitleText.text = when (mediaItem?.mediaType) {
            "livetv" -> "🔴 LIVE BROADCAST  •  Auto-Failover Protected"
            else -> "${mediaItem?.quality ?: "4K UHD"}  •  ExoPlayer Hardware Decoded"
        }

        showHud()
    }

    @OptIn(UnstableApi::class)
    private fun initPlayer() {
        val streamUrl = mediaItem?.streamUrl?.ifEmpty {
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        } ?: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

        player = ExoPlayer.Builder(this).build().apply {
            setMediaItem(ExoMediaItem.fromUri(Uri.parse(streamUrl)))
            prepare()
            if (startPositionMs > 0L) {
                seekTo(startPositionMs)
            }
            playWhenReady = true

            addListener(object : Player.Listener {
                override fun onPlaybackStateChanged(state: Int) {
                    if (state == Player.STATE_READY) {
                        updateProgress()
                    }
                }
            })
        }
        playerView.player = player
        startProgressUpdater()
    }

    private fun updateProgress() {
        val p = player ?: return
        if (p.duration > 0) {
            val progress = ((p.currentPosition * 1000) / p.duration).toInt()
            progressBar.progress = progress
            timeCurrentText.text = formatTime(p.currentPosition)
            timeTotalText.text = formatTime(p.duration)
        }
    }

    private fun startProgressUpdater() {
        progressUpdateRunnable = object : Runnable {
            override fun run() {
                updateProgress()
                handler.postDelayed(this, 500)
            }
        }
        handler.post(progressUpdateRunnable!!)
    }

    private fun formatTime(ms: Long): String {
        val totalSeconds = ms / 1000
        val seconds = totalSeconds % 60
        val minutes = (totalSeconds / 60) % 60
        val hours = totalSeconds / 3600
        return if (hours > 0) {
            String.format(Locale.US, "%02d:%02d:%02d", hours, minutes, seconds)
        } else {
            String.format(Locale.US, "%02d:%02d", minutes, seconds)
        }
    }

    // ==========================================
    // Remote Control D-pad Event Dispatcher
    // ==========================================

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        if (event.action == KeyEvent.ACTION_DOWN) {
            when (event.keyCode) {
                KeyEvent.KEYCODE_DPAD_CENTER,
                KeyEvent.KEYCODE_ENTER,
                KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE -> {
                    togglePlayPause()
                    return true
                }
                KeyEvent.KEYCODE_DPAD_RIGHT,
                KeyEvent.KEYCODE_MEDIA_FAST_FORWARD -> {
                    handleCumulativeSeek(10)
                    return true
                }
                KeyEvent.KEYCODE_DPAD_LEFT,
                KeyEvent.KEYCODE_MEDIA_REWIND -> {
                    handleCumulativeSeek(-10)
                    return true
                }
                KeyEvent.KEYCODE_DPAD_UP,
                KeyEvent.KEYCODE_DPAD_DOWN -> {
                    showHud()
                    return true
                }
                KeyEvent.KEYCODE_BACK -> {
                    saveAndExit()
                    return true
                }
            }
        }
        return super.dispatchKeyEvent(event)
    }

    private fun togglePlayPause() {
        val p = player ?: return
        if (p.isPlaying) {
            p.pause()
            showHud(persistent = true)
        } else {
            p.play()
            showHud()
        }
    }

    private fun handleCumulativeSeek(deltaSeconds: Int) {
        val p = player ?: return
        if (mediaItem?.mediaType == "livetv") return // Live streams cannot seek

        handler.removeCallbacks(seekCommitRunnable)
        accumulatedSeekSeconds += deltaSeconds

        seekFeedbackText.text = if (accumulatedSeekSeconds > 0) "+${accumulatedSeekSeconds}s" else "${accumulatedSeekSeconds}s"
        seekFeedbackLayout.visibility = View.VISIBLE
        showHud()

        // Debounce commit by 600ms to allow continuous remote clicks
        handler.postDelayed(seekCommitRunnable, 600)
    }

    private fun commitSeek() {
        val p = player ?: return
        val targetMs = (p.currentPosition + (accumulatedSeekSeconds * 1000L)).coerceIn(0L, p.duration)
        p.seekTo(targetMs)
        accumulatedSeekSeconds = 0

        handler.postDelayed({
            seekFeedbackLayout.visibility = View.GONE
        }, 800)
    }

    private fun showHud(persistent: Boolean = false) {
        topHud.visibility = View.VISIBLE
        bottomHud.visibility = View.VISIBLE
        handler.removeCallbacks(hideHudRunnable)
        if (!persistent && (player?.isPlaying == true)) {
            handler.postDelayed(hideHudRunnable, 4000)
        }
    }

    private fun hideHud() {
        topHud.visibility = View.GONE
        bottomHud.visibility = View.GONE
    }

    private fun saveAndExit() {
        player?.let { p ->
            mediaItem?.id?.let { id ->
                if (mediaItem?.mediaType != "livetv") {
                    prefs.savePlaybackPosition(id, p.currentPosition)
                }
            }
        }
        finish()
    }

    override fun onPause() {
        super.onPause()
        player?.pause()
        saveAndExit()
    }

    override fun onDestroy() {
        super.onDestroy()
        progressUpdateRunnable?.let { handler.removeCallbacks(it) }
        handler.removeCallbacksAndMessages(null)
        player?.release()
        player = null
    }
}
