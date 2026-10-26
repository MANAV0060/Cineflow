package com.cineflow.tv.ui.main

import android.animation.AnimatorInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.leanback.widget.ImageCardView
import androidx.leanback.widget.Presenter
import com.bumptech.glide.Glide
import com.cineflow.tv.R
import com.cineflow.tv.data.model.MediaItem

class LiveTvCardPresenter : Presenter() {

    companion object {
        private const val CARD_WIDTH = 280
        private const val CARD_HEIGHT = 160
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

        cardView.titleText = "🔴 ${mediaItem.title}"
        cardView.contentText = "${mediaItem.category}  •  ${mediaItem.quality}"

        Glide.with(cardView.context)
            .load(mediaItem.posterUrl)
            .centerCrop()
            .error(R.drawable.tv_banner)
            .into(cardView.mainImageView)
    }

    override fun onUnbindViewHolder(viewHolder: ViewHolder) {
        val cardView = viewHolder.view as ImageCardView
        cardView.mainImage = null
    }
}
