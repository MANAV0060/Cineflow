package com.cineflow.tv.ui.details

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.drawable.Drawable
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.leanback.app.DetailsSupportFragment
import androidx.leanback.app.DetailsSupportFragmentBackgroundController
import androidx.leanback.widget.Action
import androidx.leanback.widget.ArrayObjectAdapter
import androidx.leanback.widget.ClassPresenterSelector
import androidx.leanback.widget.DetailsOverviewRow
import androidx.leanback.widget.FullWidthDetailsOverviewRowPresenter
import androidx.leanback.widget.HeaderItem
import androidx.leanback.widget.ListRow
import androidx.leanback.widget.ListRowPresenter
import com.bumptech.glide.Glide
import com.bumptech.glide.request.target.CustomTarget
import com.bumptech.glide.request.transition.Transition
import com.cineflow.tv.R
import com.cineflow.tv.data.model.EpisodeItem
import com.cineflow.tv.data.model.MediaItem
import com.cineflow.tv.ui.main.CardPresenter
import com.cineflow.tv.ui.player.PlaybackActivity
import com.cineflow.tv.util.PreferencesManager

class DetailsFragment : DetailsSupportFragment() {

    private lateinit var mediaItem: MediaItem
    private lateinit var backgroundController: DetailsSupportFragmentBackgroundController
    private lateinit var prefs: PreferencesManager

    companion object {
        private const val ACTION_PLAY = 1L
        private const val ACTION_RESUME = 2L
        private const val ACTION_WATCHLIST = 3L
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        mediaItem = arguments?.getSerializable(DetailsActivity.EXTRA_MEDIA) as? MediaItem
            ?: return

        prefs = PreferencesManager(requireContext())
        backgroundController = DetailsSupportFragmentBackgroundController(this)
        backgroundController.enableParallax()

        setupDetailsOverview()
        loadBackdrop()
    }

    private fun setupDetailsOverview() {
        val detailsPresenter = FullWidthDetailsOverviewRowPresenter(DetailsDescriptionPresenter()).apply {
            backgroundColor = ContextCompat.getColor(requireContext(), R.color.surface_dark)
            actionsBackgroundColor = ContextCompat.getColor(requireContext(), R.color.surface_card)
        }

        val rowPresenterSelector = ClassPresenterSelector().apply {
            addClassPresenter(DetailsOverviewRow::class.java, detailsPresenter)
            addClassPresenter(ListRow::class.java, ListRowPresenter())
        }

        val rowsAdapter = ArrayObjectAdapter(rowPresenterSelector)
        val detailsOverview = DetailsOverviewRow(mediaItem)

        // Load poster bitmap
        Glide.with(requireContext())
            .asBitmap()
            .load(mediaItem.posterUrl)
            .into(object : CustomTarget<Bitmap>() {
                override fun onResourceReady(resource: Bitmap, transition: Transition<in Bitmap>?) {
                    detailsOverview.setImageBitmap(requireContext(), resource)
                }
                override fun onLoadCleared(placeholder: Drawable?) {}
            })

        // Action Buttons
        val actionsAdapter = ArrayObjectAdapter()
        val savedPosition = prefs.getPlaybackPosition(mediaItem.id)

        if (savedPosition > 30000L) {
            val minutes = (savedPosition / 1000) / 60
            actionsAdapter.add(Action(ACTION_RESUME, getString(R.string.action_resume), "From ${minutes}m"))
        }
        actionsAdapter.add(Action(ACTION_PLAY, getString(R.string.action_play)))
        
        val isInWatchlist = prefs.isInWatchlist(mediaItem.id)
        val watchlistLabel = if (isInWatchlist) "✓ In Watchlist" else "+ Add to Watchlist"
        actionsAdapter.add(Action(ACTION_WATCHLIST, watchlistLabel))

        detailsOverview.actionsAdapter = actionsAdapter
        rowsAdapter.add(detailsOverview)

        // Episode List Row for Series & Anime
        if (mediaItem.episodes.isNotEmpty()) {
            val episodesAdapter = ArrayObjectAdapter(CardPresenter())
            mediaItem.episodes.forEach { ep ->
                episodesAdapter.add(
                    MediaItem(
                        id = ep.id,
                        title = ep.title,
                        description = "Episode ${ep.episodeNumber}",
                        posterUrl = ep.thumbnailUrl.ifEmpty { mediaItem.posterUrl },
                        backdropUrl = mediaItem.backdropUrl,
                        mediaType = "episode",
                        streamUrl = ep.streamUrl.ifEmpty { mediaItem.streamUrl }
                    )
                )
            }
            rowsAdapter.add(ListRow(HeaderItem(1, "Episodes & Seasons (${mediaItem.episodes.size})"), episodesAdapter))
        }

        adapter = rowsAdapter

        detailsPresenter.onActionClickedListener = androidx.leanback.widget.OnActionClickedListener { action ->
            when (action.id) {
                ACTION_PLAY -> {
                    startPlayback(mediaItem, 0L)
                }
                ACTION_RESUME -> {
                    startPlayback(mediaItem, savedPosition)
                }
                ACTION_WATCHLIST -> {
                    if (prefs.isInWatchlist(mediaItem.id)) {
                        prefs.removeFromWatchlist(mediaItem.id)
                        action.label1 = "+ Add to Watchlist"
                    } else {
                        prefs.addToWatchlist(mediaItem.id)
                        action.label1 = "✓ In Watchlist"
                    }
                    actionsAdapter.notifyItemRangeChanged(2, 1)
                }
            }
        }

        onItemViewClickedListener = androidx.leanback.widget.OnItemViewClickedListener { _, item, _, _ ->
            val clickedMedia = item as? MediaItem ?: return@OnItemViewClickedListener
            if (clickedMedia.mediaType == "episode") {
                startPlayback(clickedMedia, 0L)
            }
        }
    }

    private fun loadBackdrop() {
        if (mediaItem.backdropUrl.isNotEmpty()) {
            Glide.with(requireContext())
                .asBitmap()
                .load(mediaItem.backdropUrl)
                .into(object : CustomTarget<Bitmap>() {
                    override fun onResourceReady(resource: Bitmap, transition: Transition<in Bitmap>?) {
                        backgroundController.coverBitmap = resource
                    }
                    override fun onLoadCleared(placeholder: Drawable?) {}
                })
        }
    }

    private fun startPlayback(item: MediaItem, startPositionMs: Long) {
        val intent = Intent(requireContext(), PlaybackActivity::class.java).apply {
            putExtra(PlaybackActivity.EXTRA_MEDIA, item)
            putExtra(PlaybackActivity.EXTRA_START_POSITION, startPositionMs)
        }
        startActivity(intent)
    }
}
