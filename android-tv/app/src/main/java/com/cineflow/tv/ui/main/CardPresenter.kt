package com.cineflow.tv.ui.main

import android.animation.AnimatorInflater
import android.graphics.Color
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.leanback.widget.ImageCardView
import androidx.leanback.widget.Presenter
import com.bumptech.glide.Glide
import com.cineflow.tv.R
import com.cineflow.tv.data.model.MediaItem

class CardPresenter : Presenter() {

    companion object {
        private const val CARD_WIDTH = 190
        private const val CARD_HEIGHT = 280
    }

    override fun onCreateViewHolder(parent: ViewGroup): ViewHolder {
        val cardView = ImageCardView(parent.context).apply {
            isFocusable = true
            isFocusableInTouchMode = true
            setMainImageDimensions(
                (CARD_WIDTH * resources.displayMetrics.density).toInt(),
                (CARD_HEIGHT * resources.displayMetrics.density).toInt()
            )
            setBackgroundColor(ContextCompat.getColor(context, R.color.surface_card))
            stateListAnimator = AnimatorInflater.loadStateListAnimator(context, R.animator.card_focus_animator)
        }
        return ViewHolder(cardView)
    }

    override fun onBindViewHolder(viewHolder: ViewHolder, item: Any?) {
        val mediaItem = item as? MediaItem ?: return
        val cardView = viewHolder.view as ImageCardView

        cardView.titleText = mediaItem.title
        cardView.contentText = when {
            mediaItem.rating > 0.0 -> "★ ${mediaItem.rating}  •  ${mediaItem.quality}"
            mediaItem.year.isNotEmpty() -> "${mediaItem.year}  •  ${mediaItem.quality}"
            else -> mediaItem.quality
        }

        Glide.with(cardView.context)
            .load(mediaItem.posterUrl)
            .centerCrop()
            .error(R.drawable.ic_launcher)
            .into(cardView.mainImageView)
    }

    override fun onUnbindViewHolder(viewHolder: ViewHolder) {
        val cardView = viewHolder.view as ImageCardView
        cardView.badgeImage = null
        cardView.mainImage = null
    }
}
