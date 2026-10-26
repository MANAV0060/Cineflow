package com.cineflow.tv.util

import android.content.Context
import android.content.SharedPreferences

class PreferencesManager(context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("cineflow_tv_prefs", Context.MODE_PRIVATE)

    companion object {
        private const val KEY_SERVER_URL = "key_server_url"
        private const val KEY_WATCH_POSITION_PREFIX = "pos_"
        private const val KEY_WATCHLIST = "key_watchlist"
        private const val KEY_AUTO_UPDATE = "key_auto_update"
        
        // Default local dev server and failover cloud URL
        const val DEFAULT_SERVER_URL = "http://10.0.2.2:5000"
    }

    var serverUrl: String
        get() = prefs.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL) ?: DEFAULT_SERVER_URL
        set(value) = prefs.edit().putString(KEY_SERVER_URL, value).apply()

    var autoUpdateEnabled: Boolean
        get() = prefs.getBoolean(KEY_AUTO_UPDATE, true)
        set(value) = prefs.edit().putBoolean(KEY_AUTO_UPDATE, value).apply()

    fun savePlaybackPosition(mediaId: String, positionMs: Long) {
        prefs.edit().putLong("$KEY_WATCH_POSITION_PREFIX$mediaId", positionMs).apply()
    }

    fun getPlaybackPosition(mediaId: String): Long {
        return prefs.getLong("$KEY_WATCH_POSITION_PREFIX$mediaId", 0L)
    }

    fun addToWatchlist(mediaId: String) {
        val set = getWatchlist().toMutableSet()
        set.add(mediaId)
        prefs.edit().putStringSet(KEY_WATCHLIST, set).apply()
    }

    fun removeFromWatchlist(mediaId: String) {
        val set = getWatchlist().toMutableSet()
        set.remove(mediaId)
        prefs.edit().putStringSet(KEY_WATCHLIST, set).apply()
    }

    fun isInWatchlist(mediaId: String): Boolean {
        return getWatchlist().contains(mediaId)
    }

    fun getWatchlist(): Set<String> {
        return prefs.getStringSet(KEY_WATCHLIST, emptySet()) ?: emptySet()
    }
}
