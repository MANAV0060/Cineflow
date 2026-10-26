package com.cineflow.tv.ui.main

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.leanback.app.BrowseSupportFragment
import androidx.leanback.widget.ArrayObjectAdapter
import androidx.leanback.widget.HeaderItem
import androidx.leanback.widget.ListRow
import androidx.leanback.widget.ListRowPresenter
import androidx.leanback.widget.OnItemViewClickedListener
import androidx.lifecycle.lifecycleScope
import com.cineflow.tv.BuildConfig
import com.cineflow.tv.R
import com.cineflow.tv.data.api.CineflowApi
import com.cineflow.tv.data.model.MediaItem
import com.cineflow.tv.ui.details.DetailsActivity
import com.cineflow.tv.ui.player.PlaybackActivity
import com.cineflow.tv.ui.update.UpdateActivity
import com.cineflow.tv.util.AppUpdater
import com.cineflow.tv.util.PreferencesManager
import kotlinx.coroutines.launch

class MainFragment : BrowseSupportFragment() {

    private lateinit var rowsAdapter: ArrayObjectAdapter
    private lateinit var api: CineflowApi
    private lateinit var updater: AppUpdater
    private lateinit var prefs: PreferencesManager

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        api = CineflowApi(requireContext())
        updater = AppUpdater(requireContext())
        prefs = PreferencesManager(requireContext())

        setupUIElements()
        setupEventListeners()
        loadRows()
    }

    private fun setupUIElements() {
        title = getString(R.string.browse_title)
        badgeDrawable = ContextCompat.getDrawable(requireContext(), R.drawable.ic_launcher)
        headersState = HEADERS_ENABLED
        isHeadersTransitionOnBackEnabled = true
        brandColor = ContextCompat.getColor(requireContext(), R.color.surface_dark)
        searchAffordanceColor = ContextCompat.getColor(requireContext(), R.color.brand_gold)

        setOnSearchClickedListener {
            Toast.makeText(requireContext(), "Search: Type query with remote", Toast.LENGTH_SHORT).show()
        }
    }

    private fun setupEventListeners() {
        onItemViewClickedListener = OnItemViewClickedListener { _, item, _, _ ->
            val mediaItem = item as? MediaItem ?: return@OnItemViewClickedListener

            when (mediaItem.mediaType) {
                "update" -> {
                    checkManualUpdate()
                }
                "livetv" -> {
                    // Start Live TV stream directly
                    val intent = Intent(requireContext(), PlaybackActivity::class.java).apply {
                        putExtra(PlaybackActivity.EXTRA_MEDIA, mediaItem)
                    }
                    startActivity(intent)
                }
                else -> {
                    // Open Details for Movies, Shows, & Anime
                    val intent = Intent(requireContext(), DetailsActivity::class.java).apply {
                        putExtra(DetailsActivity.EXTRA_MEDIA, mediaItem)
                    }
                    startActivity(intent)
                }
            }
        }
    }

    private fun loadRows() {
        rowsAdapter = ArrayObjectAdapter(ListRowPresenter())
        adapter = rowsAdapter

        val cardPresenter = CardPresenter()
        val liveTvCardPresenter = LiveTvCardPresenter()

        viewLifecycleOwner.lifecycleScope.launch {
            // 1. Featured Spotlight
            val featured = api.getFeaturedSpotlight()
            val featuredAdapter = ArrayObjectAdapter(cardPresenter)
            featured.forEach { featuredAdapter.add(it) }
            val headerFeatured = HeaderItem(0, getString(R.string.category_featured))
            rowsAdapter.add(ListRow(headerFeatured, featuredAdapter))

            // 2. Continue Watching (if any)
            val watchlist = prefs.getWatchlist()
            if (watchlist.isNotEmpty()) {
                val continueAdapter = ArrayObjectAdapter(cardPresenter)
                val allMovies = api.getTrendingMovies()
                allMovies.filter { watchlist.contains(it.id) }.forEach { continueAdapter.add(it) }
                if (continueAdapter.size() > 0) {
                    val headerContinue = HeaderItem(1, getString(R.string.category_continue))
                    rowsAdapter.add(ListRow(headerContinue, continueAdapter))
                }
            }

            // 3. Trending Movies
            val movies = api.getTrendingMovies()
            val moviesAdapter = ArrayObjectAdapter(cardPresenter)
            movies.forEach { moviesAdapter.add(it) }
            val headerMovies = HeaderItem(2, getString(R.string.category_movies))
            rowsAdapter.add(ListRow(headerMovies, moviesAdapter))

            // 4. Popular TV Series
            val series = api.getTvSeries()
            val seriesAdapter = ArrayObjectAdapter(cardPresenter)
            series.forEach { seriesAdapter.add(it) }
            val headerSeries = HeaderItem(3, getString(R.string.category_series))
            rowsAdapter.add(ListRow(headerSeries, seriesAdapter))

            // 5. Anime Universe
            val anime = api.getAnimeUniverse()
            val animeAdapter = ArrayObjectAdapter(cardPresenter)
            anime.forEach { animeAdapter.add(it) }
            val headerAnime = HeaderItem(4, getString(R.string.category_anime))
            rowsAdapter.add(ListRow(headerAnime, animeAdapter))

            // 6. Live TV Channels (37 channels, 16:9 cards)
            val channels = api.getLiveTvChannels()
            val channelsAdapter = ArrayObjectAdapter(liveTvCardPresenter)
            channels.forEach { channelsAdapter.add(it) }
            val headerChannels = HeaderItem(5, getString(R.string.category_livetv))
            rowsAdapter.add(ListRow(headerChannels, channelsAdapter))

            // 7. Settings & Update Card
            val settingsAdapter = ArrayObjectAdapter(cardPresenter)
            settingsAdapter.add(
                MediaItem(
                    id = "action_update",
                    title = "Check for Updates",
                    description = "Current Version: v${BuildConfig.VERSION_NAME} (Build ${BuildConfig.VERSION_CODE})",
                    posterUrl = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800",
                    mediaType = "update",
                    quality = "v${BuildConfig.VERSION_NAME}"
                )
            )
            val headerSettings = HeaderItem(6, getString(R.string.category_settings))
            rowsAdapter.add(ListRow(headerSettings, settingsAdapter))
        }
    }

    private fun checkManualUpdate() {
        Toast.makeText(requireContext(), "Checking Cineflow updates...", Toast.LENGTH_SHORT).show()
        viewLifecycleOwner.lifecycleScope.launch {
            val update = updater.checkForUpdates()
            if (update != null) {
                val intent = Intent(requireContext(), UpdateActivity::class.java).apply {
                    putExtra(UpdateActivity.EXTRA_UPDATE_INFO, update)
                }
                startActivity(intent)
            } else {
                Toast.makeText(requireContext(), getString(R.string.app_up_to_date), Toast.LENGTH_LONG).show()
            }
        }
    }
}
