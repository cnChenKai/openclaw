package ai.openclaw.app.node

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.telephony.SmsManager as AndroidSmsManager
import androidx.core.content.ContextCompat
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.JsonArray
import android.provider.Telephony
import ai.openclaw.app.PermissionRequester

/**
 * Sends SMS messages via the Android SMS API.
 * Requires SEND_SMS permission to be granted.
 */
class SmsManager(private val context: Context) {

    private val json = JsonConfig
    @Volatile private var permissionRequester: PermissionRequester? = null

    data class ReadResult(
        val ok: Boolean,
        val error: String? = null,
        val payloadJson: String,
    )

    data class SendResult(
        val ok: Boolean,
        val to: String,
        val message: String?,
        val error: String? = null,
        val payloadJson: String,
    )

    internal data class ParsedParams(
        val to: String,
        val message: String,
    )

    internal sealed class ParseResult {
        data class Ok(val params: ParsedParams) : ParseResult()
        data class Error(
            val error: String,
            val to: String = "",
            val message: String? = null,
        ) : ParseResult()
    }

    internal data class SendPlan(
        val parts: List<String>,
        val useMultipart: Boolean,
    )

    companion object {
        internal val JsonConfig = Json { ignoreUnknownKeys = true }

        internal fun parseParams(paramsJson: String?, json: Json = JsonConfig): ParseResult {
            val params = paramsJson?.trim().orEmpty()
            if (params.isEmpty()) {
                return ParseResult.Error(error = "INVALID_REQUEST: paramsJSON required")
            }

            val obj = try {
                json.parseToJsonElement(params).jsonObject
            } catch (_: Throwable) {
                null
            }

            if (obj == null) {
                return ParseResult.Error(error = "INVALID_REQUEST: expected JSON object")
            }

            val to = (obj["to"] as? JsonPrimitive)?.content?.trim().orEmpty()
            val message = (obj["message"] as? JsonPrimitive)?.content.orEmpty()

            if (to.isEmpty()) {
                return ParseResult.Error(
                    error = "INVALID_REQUEST: 'to' phone number required",
                    message = message,
                )
            }

            if (message.isEmpty()) {
                return ParseResult.Error(
                    error = "INVALID_REQUEST: 'message' text required",
                    to = to,
                )
            }

            return ParseResult.Ok(ParsedParams(to = to, message = message))
        }

        internal fun buildSendPlan(
            message: String,
            divider: (String) -> List<String>,
        ): SendPlan {
            val parts = divider(message).ifEmpty { listOf(message) }
            return SendPlan(parts = parts, useMultipart = parts.size > 1)
        }

        internal fun buildPayloadJson(
            json: Json = JsonConfig,
            ok: Boolean,
            to: String,
            error: String?,
        ): String {
            val payload =
                mutableMapOf<String, JsonElement>(
                    "ok" to JsonPrimitive(ok),
                    "to" to JsonPrimitive(to),
                )
            if (!ok) {
                payload["error"] = JsonPrimitive(error ?: "SMS_SEND_FAILED")
            }
            return json.encodeToString(JsonObject.serializer(), JsonObject(payload))
        }
    }

    fun hasReadSmsPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_SMS
        ) == PackageManager.PERMISSION_GRANTED
    }

    fun hasSmsPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.SEND_SMS
        ) == PackageManager.PERMISSION_GRANTED
    }

    fun canSendSms(): Boolean {
        return hasTelephonyFeature()
    }

    fun hasTelephonyFeature(): Boolean {
        return context.packageManager?.hasSystemFeature(PackageManager.FEATURE_TELEPHONY) == true
    }

    fun attachPermissionRequester(requester: PermissionRequester) {
        permissionRequester = requester
    }

    /**
     * Send an SMS message.
     *
     * @param paramsJson JSON with "to" (phone number) and "message" (text) fields
     * @return SendResult indicating success or failure
     */
    suspend fun send(paramsJson: String?): SendResult {
        if (!hasTelephonyFeature()) {
            return errorResult(
                error = "SMS_UNAVAILABLE: telephony not available",
            )
        }

        if (!ensureSmsPermission()) {
            return errorResult(
                error = "SMS_PERMISSION_REQUIRED: grant SMS permission",
            )
        }

        val parseResult = parseParams(paramsJson, json)
        if (parseResult is ParseResult.Error) {
            return errorResult(
                error = parseResult.error,
                to = parseResult.to,
                message = parseResult.message,
            )
        }
        val params = (parseResult as ParseResult.Ok).params

        return try {
            val smsManager = context.getSystemService(AndroidSmsManager::class.java)
                ?: throw IllegalStateException("SMS_UNAVAILABLE: SmsManager not available")

            val plan = buildSendPlan(params.message) { smsManager.divideMessage(it) }
            if (plan.useMultipart) {
                smsManager.sendMultipartTextMessage(
                    params.to,     // destination
                    null,          // service center (null = default)
                    ArrayList(plan.parts),    // message parts
                    null,          // sent intents
                    null,          // delivery intents
                )
            } else {
                smsManager.sendTextMessage(
                    params.to,     // destination
                    null,          // service center (null = default)
                    params.message,// message
                    null,          // sent intent
                    null,          // delivery intent
                )
            }

            okResult(to = params.to, message = params.message)
        } catch (e: SecurityException) {
            errorResult(
                error = "SMS_PERMISSION_REQUIRED: ${e.message}",
                to = params.to,
                message = params.message,
            )
        } catch (e: Throwable) {
            errorResult(
                error = "SMS_SEND_FAILED: ${e.message ?: "unknown error"}",
                to = params.to,
                message = params.message,
            )
        }
    }

    private suspend fun ensureReadSmsPermission(): Boolean {
        if (hasReadSmsPermission()) return true
        val requester = permissionRequester ?: return false
        val results = requester.requestIfMissing(listOf(Manifest.permission.READ_SMS))
        return results[Manifest.permission.READ_SMS] == true
    }

    private suspend fun ensureSmsPermission(): Boolean {
        if (hasSmsPermission()) return true
        val requester = permissionRequester ?: return false
        val results = requester.requestIfMissing(listOf(Manifest.permission.SEND_SMS))
        return results[Manifest.permission.SEND_SMS] == true
    }

    /**
     * Read SMS messages.
     */
    suspend fun read(paramsJson: String?): ReadResult {
        if (!hasTelephonyFeature()) {
            return readErrorResult(error = "SMS_UNAVAILABLE: telephony not available")
        }

        if (!ensureReadSmsPermission()) {
            return readErrorResult(error = "SMS_PERMISSION_REQUIRED: grant READ_SMS permission")
        }

        var limit = 20
        if (!paramsJson.isNullOrBlank()) {
            try {
                val obj = json.parseToJsonElement(paramsJson).jsonObject
                val limitPrimitive = obj["limit"] as? JsonPrimitive
                limitPrimitive?.content?.toIntOrNull()?.let {
                    if (it > 0) limit = it
                }
            } catch (_: Throwable) {}
        }

        return try {
            val messages = mutableListOf<JsonObject>()
            val uri = Telephony.Sms.CONTENT_URI
            val projection = arrayOf(
                Telephony.Sms._ID,
                Telephony.Sms.ADDRESS,
                Telephony.Sms.BODY,
                Telephony.Sms.DATE,
                Telephony.Sms.TYPE
            )

            context.contentResolver.query(
                uri,
                projection,
                null,
                null,
                "${Telephony.Sms.DATE} DESC LIMIT $limit"
            )?.use { cursor ->
                val idIdx = cursor.getColumnIndexOrThrow(Telephony.Sms._ID)
                val addrIdx = cursor.getColumnIndexOrThrow(Telephony.Sms.ADDRESS)
                val bodyIdx = cursor.getColumnIndexOrThrow(Telephony.Sms.BODY)
                val dateIdx = cursor.getColumnIndexOrThrow(Telephony.Sms.DATE)
                val typeIdx = cursor.getColumnIndexOrThrow(Telephony.Sms.TYPE)

                while (cursor.moveToNext()) {
                    val msgObj = JsonObject(mapOf(
                        "id" to JsonPrimitive(cursor.getString(idIdx)),
                        "address" to JsonPrimitive(cursor.getString(addrIdx)),
                        "body" to JsonPrimitive(cursor.getString(bodyIdx)),
                        "date" to JsonPrimitive(cursor.getLong(dateIdx)),
                        "type" to JsonPrimitive(cursor.getInt(typeIdx))
                    ))
                    messages.add(msgObj)
                }
            }

            val payloadObj = JsonObject(mapOf(
                "ok" to JsonPrimitive(true),
                "messages" to JsonArray(messages)
            ))
            val payloadStr = json.encodeToString(JsonObject.serializer(), payloadObj)
            ReadResult(ok = true, error = null, payloadJson = payloadStr)
        } catch (e: SecurityException) {
            readErrorResult(error = "SMS_PERMISSION_REQUIRED: ${e.message}")
        } catch (e: Throwable) {
            readErrorResult(error = "SMS_READ_FAILED: ${e.message ?: "unknown error"}")
        }
    }

    private fun readErrorResult(error: String): ReadResult {
        val payloadObj = JsonObject(mapOf(
            "ok" to JsonPrimitive(false),
            "error" to JsonPrimitive(error)
        ))
        val payloadStr = json.encodeToString(JsonObject.serializer(), payloadObj)
        return ReadResult(ok = false, error = error, payloadJson = payloadStr)
    }

    private fun okResult(to: String, message: String): SendResult {
        return SendResult(
            ok = true,
            to = to,
            message = message,
            error = null,
            payloadJson = buildPayloadJson(json = json, ok = true, to = to, error = null),
        )
    }

    private fun errorResult(error: String, to: String = "", message: String? = null): SendResult {
        return SendResult(
            ok = false,
            to = to,
            message = message,
            error = error,
            payloadJson = buildPayloadJson(json = json, ok = false, to = to, error = error),
        )
    }
}
