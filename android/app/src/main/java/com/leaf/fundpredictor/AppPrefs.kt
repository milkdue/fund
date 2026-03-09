package com.leaf.fundpredictor

import android.content.Context

private const val PREFS = "fund_predictor_prefs"
private const val KEY_RISK_ACK = "risk_ack"

class AppPrefs(context: Context) {
    private val sp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun isRiskAcknowledged(): Boolean = sp.getBoolean(KEY_RISK_ACK, false)

    fun setRiskAcknowledged(value: Boolean) {
        sp.edit().putBoolean(KEY_RISK_ACK, value).apply()
    }
}
