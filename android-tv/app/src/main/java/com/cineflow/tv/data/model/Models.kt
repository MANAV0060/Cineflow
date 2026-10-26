package com.cineflow.tv.data.model

import com.google.gson.annotations.SerializedName
import java.io.Serializable

data class MediaItem(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String,
    @SerializedName("description") val description: String = "",
    @SerializedName("poster_url") val posterUrl: String = "",
    @SerializedName("backdrop_url") val backdropUrl: String = "",
    @SerializedName("media_type") val mediaType: String = "movie", // movie, tv, anime, livetv
    @SerializedName("year") val year: String = "",
    @SerializedName("rating") val rating: Double = 0.0,
    @SerializedName("quality") val quality: String = "4K UHD",
    @SerializedName("has_dub") val hasDub: Boolean = false,
    @SerializedName("stream_url") val streamUrl: String = "",
    @SerializedName("category") val category: String = "",
    @SerializedName("episodes") val episodes: List<EpisodeItem> = emptyList()
) : Serializable

data class EpisodeItem(
    @SerializedName("id") val id: String,
    @SerializedName("episode_number") val episodeNumber: Int,
    @SerializedName("title") val title: String,
    @SerializedName("thumbnail_url") val thumbnailUrl: String = "",
    @SerializedName("stream_url") val streamUrl: String = "",
    @SerializedName("duration_ms") val durationMs: Long = 0L
) : Serializable

data class UpdateInfo(
    @SerializedName("latest_version_code") val latestVersionCode: Int,
    @SerializedName("latest_version_name") val latestVersionName: String,
    @SerializedName("release_date") val releaseDate: String = "",
    @SerializedName("apk_url") val apkUrl: String,
    @SerializedName("changelog") val changelog: List<String> = emptyList(),
    @SerializedName("mandatory") val mandatory: Boolean = false,
    @SerializedName("min_supported_version") val minSupportedVersion: Int = 1000
) : Serializable

data class StreamSource(
    val quality: String,
    val url: String,
    val isHls: Boolean = false,
    val isDash: Boolean = false
) : Serializable
