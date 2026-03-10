package com.leaf.fundpredictor.alerts

import android.content.Context
import android.util.Log
import androidx.hilt.work.HiltWorker
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.leaf.fundpredictor.AppPrefs
import com.leaf.fundpredictor.domain.repository.FundRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import java.util.concurrent.TimeUnit

private const val TAG = "AlertPollWorker"
private const val DEFAULT_FETCH_LIMIT = 50
private const val DEFAULT_INTERVAL_MINUTES = 15L

@HiltWorker
class AlertPollWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val repository: FundRepository,
    private val prefs: AppPrefs,
    private val notificationHelper: AlertNotificationHelper,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        return runCatching {
            val events = repository.getAlertEvents(limit = DEFAULT_FETCH_LIMIT)
                .sortedBy { it.id }
            if (events.isEmpty()) return Result.success()

            val lastId = prefs.getLastAlertEventId()
            val latestId = events.maxOf { it.id }

            if (lastId <= 0L) {
                prefs.setLastAlertEventId(latestId)
                Log.i(TAG, "initialized last alert id: $latestId")
                return Result.success()
            }

            val newEvents = events.filter { it.id > lastId }
            if (newEvents.isNotEmpty()) {
                if (notificationHelper.canNotify()) {
                    notificationHelper.ensureChannel()
                    newEvents.takeLast(5).forEach { notificationHelper.notify(it) }
                    Log.i(TAG, "sent ${newEvents.size} alert notifications")
                } else {
                    Log.w(TAG, "notification permission not granted; skip system notify")
                }
            }

            if (latestId > lastId) {
                prefs.setLastAlertEventId(latestId)
            }
            Result.success()
        }.getOrElse { ex ->
            Log.e(TAG, "poll alerts failed: ${ex.message}", ex)
            if (runAttemptCount >= 3) Result.failure() else Result.retry()
        }
    }

    companion object {
        const val UNIQUE_WORK_NAME = "fund_alert_poll_work"
        const val UNIQUE_BOOTSTRAP_WORK_NAME = "fund_alert_poll_once"

        fun enqueue(context: Context, intervalMinutes: Long = DEFAULT_INTERVAL_MINUTES) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = PeriodicWorkRequestBuilder<AlertPollWorker>(
                repeatInterval = intervalMinutes,
                repeatIntervalTimeUnit = TimeUnit.MINUTES,
            )
                .setConstraints(constraints)
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                UNIQUE_WORK_NAME,
                ExistingPeriodicWorkPolicy.UPDATE,
                request,
            )

            val bootstrapRequest = OneTimeWorkRequestBuilder<AlertPollWorker>()
                .setConstraints(constraints)
                .build()
            WorkManager.getInstance(context).enqueueUniqueWork(
                UNIQUE_BOOTSTRAP_WORK_NAME,
                ExistingWorkPolicy.KEEP,
                bootstrapRequest,
            )
        }
    }
}
