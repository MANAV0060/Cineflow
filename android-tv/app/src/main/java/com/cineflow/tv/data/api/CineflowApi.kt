package com.cineflow.tv.data.api

import android.content.Context
import android.util.Log
import com.cineflow.tv.data.model.EpisodeItem
import com.cineflow.tv.data.model.MediaItem
import com.cineflow.tv.util.PreferencesManager
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

class CineflowApi(context: Context) {

    private val prefs = PreferencesManager(context)
    private val client = OkHttpClient.Builder()
        .connectTimeout(12, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()
    private val gson = Gson()

    suspend fun getFeaturedSpotlight(): List<MediaItem> = withContext(Dispatchers.IO) {
        val movies = getTrendingMovies()
        if (movies.isNotEmpty()) movies.take(3) else getCuratedSpotlight()
    }

    suspend fun getTrendingMovies(): List<MediaItem> = withContext(Dispatchers.IO) {
        try {
            val server = prefs.serverUrl.trimEnd('/')
            val request = Request.Builder().url("$server/api/movies").build()
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val body = response.body?.string() ?: ""
                    val listType = object : TypeToken<List<MediaItem>>() {}.type
                    val list: List<MediaItem> = gson.fromJson(body, listType)
                    if (list.isNotEmpty()) return@withContext list
                }
            }
        } catch (e: Exception) {
            Log.w("CineflowApi", "Backend movies endpoint unreachable, using curated catalog: ${e.message}")
        }
        return@withContext getCuratedMovies()
    }

    suspend fun getTvSeries(): List<MediaItem> = withContext(Dispatchers.IO) {
        try {
            val server = prefs.serverUrl.trimEnd('/')
            val request = Request.Builder().url("$server/api/tv").build()
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val body = response.body?.string() ?: ""
                    val listType = object : TypeToken<List<MediaItem>>() {}.type
                    val list: List<MediaItem> = gson.fromJson(body, listType)
                    if (list.isNotEmpty()) return@withContext list
                }
            }
        } catch (e: Exception) {
            Log.w("CineflowApi", "Backend TV endpoint unreachable, using curated catalog: ${e.message}")
        }
        return@withContext getCuratedTvSeries()
    }

    suspend fun getAnimeUniverse(): List<MediaItem> = withContext(Dispatchers.IO) {
        try {
            val server = prefs.serverUrl.trimEnd('/')
            val request = Request.Builder().url("$server/api/anime/trending").build()
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val body = response.body?.string() ?: ""
                    val listType = object : TypeToken<List<MediaItem>>() {}.type
                    val list: List<MediaItem> = gson.fromJson(body, listType)
                    if (list.isNotEmpty()) return@withContext list
                }
            }
        } catch (e: Exception) {
            Log.w("CineflowApi", "Backend Anime endpoint unreachable, using curated catalog: ${e.message}")
        }
        return@withContext getCuratedAnime()
    }

    suspend fun getLiveTvChannels(): List<MediaItem> = withContext(Dispatchers.IO) {
        try {
            val server = prefs.serverUrl.trimEnd('/')
            val request = Request.Builder().url("$server/api/livetv/channels").build()
            client.newCall(request).execute().use { response ->
                if (response.isSuccessful) {
                    val body = response.body?.string() ?: ""
                    val listType = object : TypeToken<List<MediaItem>>() {}.type
                    val list: List<MediaItem> = gson.fromJson(body, listType)
                    if (list.isNotEmpty()) return@withContext list
                }
            }
        } catch (e: Exception) {
            Log.w("CineflowApi", "Backend LiveTV endpoint unreachable, using curated channels: ${e.message}")
        }
        return@withContext getCuratedLiveTvChannels()
    }

    // ==========================================
    // Curated 10-foot TV Datasets (Instant Loading)
    // ==========================================

    private fun getCuratedSpotlight(): List<MediaItem> {
        return listOf(
            MediaItem(
                id = "spotlight_1",
                title = "Masters of the Universe",
                description = "Prince Adam of Eternia discovers the Sword of Power, transforming into He-Man to defend Castle Grayskull from the dark forces of Skeletor.",
                posterUrl = "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1600",
                mediaType = "movie",
                year = "2024",
                rating = 8.4,
                quality = "4K UHD • Atmos",
                hasDub = true,
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            )
        )
    }

    private fun getCuratedMovies(): List<MediaItem> {
        return listOf(
            MediaItem(
                id = "m_1",
                title = "Avatar: The Way of Water",
                description = "Jake Sully lives with his newfound family formed on the extrasolar moon Pandora. Once a familiar threat returns to finish what was previously started, Jake must work with Neytiri and the army of the Na'vi race.",
                posterUrl = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1600",
                mediaType = "movie",
                year = "2022",
                rating = 7.6,
                quality = "4K UHD",
                hasDub = true,
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"
            ),
            MediaItem(
                id = "m_2",
                title = "Dune: Part Two",
                description = "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.",
                posterUrl = "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1600",
                mediaType = "movie",
                year = "2024",
                rating = 8.6,
                quality = "4K UHD • HDR",
                hasDub = true,
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
            ),
            MediaItem(
                id = "m_3",
                title = "Oppenheimer",
                description = "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
                posterUrl = "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=1600",
                mediaType = "movie",
                year = "2023",
                rating = 8.9,
                quality = "4K UHD",
                hasDub = false,
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
            ),
            MediaItem(
                id = "m_4",
                title = "Interstellar",
                description = "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft along with a team of researchers.",
                posterUrl = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1600",
                mediaType = "movie",
                year = "2014",
                rating = 8.7,
                quality = "4K UHD",
                hasDub = true,
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4"
            )
        )
    }

    private fun getCuratedTvSeries(): List<MediaItem> {
        val breakingBadEpisodes = (1..7).map { ep ->
            EpisodeItem(
                id = "bb_ep$ep",
                episodeNumber = ep,
                title = "Episode $ep: ${if (ep == 1) "Pilot" else "Chapter $ep"}",
                thumbnailUrl = "https://images.unsplash.com/photo-1522869635100-9f4c5e86aa37?w=600",
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                durationMs = 45 * 60 * 1000L
            )
        }

        return listOf(
            MediaItem(
                id = "tv_1",
                title = "Breaking Bad",
                description = "A chemistry teacher diagnosed with inoperable lung cancer turns to manufacturing and selling methamphetamine with a former student.",
                posterUrl = "https://images.unsplash.com/photo-1522869635100-9f4c5e86aa37?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1522869635100-9f4c5e86aa37?w=1600",
                mediaType = "tv",
                year = "2008–2013",
                rating = 9.5,
                quality = "1080p FHD",
                hasDub = true,
                episodes = breakingBadEpisodes
            ),
            MediaItem(
                id = "tv_2",
                title = "Stranger Things",
                description = "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.",
                posterUrl = "https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?w=1600",
                mediaType = "tv",
                year = "2016–Present",
                rating = 8.7,
                quality = "4K UHD • Atmos",
                hasDub = true,
                episodes = breakingBadEpisodes
            )
        )
    }

    private fun getCuratedAnime(): List<MediaItem> {
        val animeEpisodes = (1..12).map { ep ->
            EpisodeItem(
                id = "anime_ep$ep",
                episodeNumber = ep,
                title = "Episode $ep",
                thumbnailUrl = "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600",
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
                durationMs = 24 * 60 * 1000L
            )
        }

        return listOf(
            MediaItem(
                id = "anime_1",
                title = "Demon Slayer: Kimetsu no Yaiba",
                description = "A family is attacked by demons and only two members survive - Tanjiro and his sister Nezuko, who is turning into a demon herself.",
                posterUrl = "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1600",
                mediaType = "anime",
                year = "2019–Present",
                rating = 8.6,
                quality = "1080p FHD",
                hasDub = true,
                episodes = animeEpisodes
            ),
            MediaItem(
                id = "anime_2",
                title = "Jujutsu Kaisen",
                description = "A boy swallows a cursed talisman - the finger of a demon - and becomes cursed himself. He enters a shaman's school to find the other body parts.",
                posterUrl = "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=1600",
                mediaType = "anime",
                year = "2020–Present",
                rating = 8.5,
                quality = "1080p FHD",
                hasDub = true,
                episodes = animeEpisodes
            )
        )
    }

    private fun getCuratedLiveTvChannels(): List<MediaItem> {
        return listOf(
            MediaItem(
                id = "live_1",
                title = "Cineflow Cinema 24/7",
                description = "Non-stop blockbuster releases and Hollywood classics in 1080p with auto-failover stream routing.",
                posterUrl = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1600",
                mediaType = "livetv",
                quality = "1080p Live",
                category = "Movies & Cinema",
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            ),
            MediaItem(
                id = "live_2",
                title = "Sports Live 1",
                description = "High-definition 60fps live sports broadcasting with auto-failover stream protection.",
                posterUrl = "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1600",
                mediaType = "livetv",
                quality = "1080p 60fps",
                category = "Live Sports",
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"
            ),
            MediaItem(
                id = "live_3",
                title = "Anime Live Network",
                description = "24/7 simulcast episodes, classic anime movies, and original Japanese animation.",
                posterUrl = "https://images.unsplash.com/photo-1563089145-599997674d42?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1563089145-599997674d42?w=1600",
                mediaType = "livetv",
                quality = "1080p Live",
                category = "Anime 24/7",
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4"
            ),
            MediaItem(
                id = "live_4",
                title = "World News HD",
                description = "Breaking international news and live reports 24 hours a day.",
                posterUrl = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800",
                backdropUrl = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1600",
                mediaType = "livetv",
                quality = "1080p Live",
                category = "News",
                streamUrl = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
            )
        )
    }
}
