package com.cineflow.tv.ui.details

import androidx.leanback.widget.AbstractDetailsDescriptionPresenter
import com.cineflow.tv.data.model.MediaItem

class DetailsDescriptionPresenter : AbstractDetailsDescriptionPresenter() {
    override fun onBindDescription(viewHolder: ViewHolder, item: Any?) {
        val media = item as? MediaItem ?: return
        viewHolder.title.text = media.title
        viewHolder.subtitle.text = buildString {
            if (media.year.isNotEmpty()) append("${media.year}  •  ")
            if (media.rating > 0.0) append("★ ${media.rating}  •  ")
            append(media.quality)
            if (media.hasDub) append("  •  Multi-Audio Dubbed")
        }
        viewHolder.body.text = media.description
    }
}
