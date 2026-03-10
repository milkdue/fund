package com.leaf.fundpredictor

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject

private const val PREFS = "fund_predictor_prefs"
private const val KEY_RISK_ACK = "risk_ack"
private const val KEY_LAST_ALERT_EVENT_ID = "last_alert_event_id"

class AppPrefs @Inject constructor(
    @ApplicationContext context: Context,
) {
    private val sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun isRiskAcknowledged(): Boolean = sp.getBoolean(KEY_RISK_ACK, false)

    fun setRiskAcknowledged(value: Boolean) {
        sp.edit().putBoolean(KEY_RISK_ACK, value).apply()
    }

    fun getLastAlertEventId(): Long = sp.getLong(KEY_LAST_ALERT_EVENT_ID, 0L)

    fun setLastAlertEventId(value: Long) {
        sp.edit().putLong(KEY_LAST_ALERT_EVENT_ID, value).apply()
    }
}
