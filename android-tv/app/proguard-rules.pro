# Cineflow TV Proguard Rules
-keep class com.cineflow.tv.data.model.** { *; }
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
