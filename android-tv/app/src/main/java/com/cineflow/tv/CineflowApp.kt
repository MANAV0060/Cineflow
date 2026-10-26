package com.cineflow.tv

import android.app.Application
import android.util.Log

class CineflowApp : Application() {
    override fun onCreate() {
        super.onCreate()
        Log.d("CineflowTV", "Cineflow TV Native Application Initialized.")
    }
}
