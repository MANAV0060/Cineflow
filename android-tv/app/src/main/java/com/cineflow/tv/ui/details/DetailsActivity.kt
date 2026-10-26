package com.cineflow.tv.ui.details

import android.os.Bundle
import androidx.fragment.app.FragmentActivity
import com.cineflow.tv.R
import com.cineflow.tv.data.model.MediaItem

class DetailsActivity : FragmentActivity() {

    companion object {
        const val EXTRA_MEDIA = "extra_media"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_details)

        if (savedInstanceState == null) {
            val media = intent.getSerializableExtra(EXTRA_MEDIA) as? MediaItem
            val fragment = DetailsFragment().apply {
                arguments = Bundle().apply {
                    putSerializable(EXTRA_MEDIA, media)
                }
            }
            supportFragmentManager.beginTransaction()
                .replace(R.id.details_fragment_container, fragment)
                .commit()
        }
    }
}
