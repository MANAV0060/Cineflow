package com.cineflow.tv.util

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.util.Log
import androidx.core.content.FileProvider
import com.cineflow.tv.BuildConfig
import com.cineflow.tv.data.model.UpdateInfo
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream
import java.util.concurrent.TimeUnit

class AppUpdater(private val context: Context) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()
    private val prefs = PreferencesManager(context)

    suspend fun checkForUpdates(): UpdateInfo? = withContext(Dispatchers.IO) {
        try {
            val server = prefs.serverUrl.trimEnd('/')
            val url = "$server/api/tv/update?current_version=${BuildConfig.VERSION_CODE}"
            val request = Request.Builder().url(url).build()

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext null
                val body = response.body?.string() ?: return@withContext null
                val info = gson.fromJson(body, UpdateInfo::class.java)

                if (info.latestVersionCode > BuildConfig.VERSION_CODE) {
                    Log.i("AppUpdater", "Update found: v${info.latestVersionName} (${info.latestVersionCode})")
                    return@withContext info
                }
            }
        } catch (e: Exception) {
            Log.w("AppUpdater", "Failed to check for updates: ${e.message}")
        }
        return@withContext null
    }

    suspend fun downloadAndInstallApk(
        updateInfo: UpdateInfo,
        onProgress: (percentage: Int) -> Unit
    ): Boolean = withContext(Dispatchers.IO) {
        try {
            var downloadUrl = updateInfo.apkUrl
            if (!downloadUrl.startsWith("http")) {
                val server = prefs.serverUrl.trimEnd('/')
                downloadUrl = "$server$downloadUrl"
            }

            Log.i("AppUpdater", "Downloading APK from: $downloadUrl")
            val request = Request.Builder().url(downloadUrl).build()

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext false
                val body = response.body ?: return@withContext false
                val totalBytes = body.contentLength()

                // Save into external files or cache directory
                val updatesDir = File(context.getExternalFilesDir(null) ?: context.cacheDir, "updates")
                if (!updatesDir.exists()) updatesDir.mkdirs()

                val apkFile = File(updatesDir, "cineflow-tv-v${updateInfo.latestVersionCode}.apk")
                if (apkFile.exists()) apkFile.delete()

                val inputStream: InputStream = body.byteStream()
                val outputStream = FileOutputStream(apkFile)

                val buffer = ByteArray(8 * 1024)
                var bytesRead: Int
                var totalRead = 0L

                while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                    outputStream.write(buffer, 0, bytesRead)
                    totalRead += bytesRead
                    if (totalBytes > 0) {
                        val progress = ((totalRead * 100) / totalBytes).toInt()
                        withContext(Dispatchers.Main) {
                            onProgress(progress)
                        }
                    }
                }

                outputStream.flush()
                outputStream.close()
                inputStream.close()

                Log.i("AppUpdater", "Download complete: ${apkFile.absolutePath} (${apkFile.length()} bytes)")

                withContext(Dispatchers.Main) {
                    launchSystemInstaller(apkFile)
                }
                return@withContext true
            }
        } catch (e: Exception) {
            Log.e("AppUpdater", "Failed to download update APK", e)
            return@withContext false
        }
    }

    fun launchSystemInstaller(apkFile: File) {
        try {
            val contentUri: Uri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                apkFile
            )

            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(contentUri, "application/vnd.android.package-archive")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION
            }

            context.startActivity(intent)
            Log.i("AppUpdater", "Launched system package installer for ${apkFile.name}")
        } catch (e: Exception) {
            Log.e("AppUpdater", "Error opening system installer", e)
        }
    }
}
