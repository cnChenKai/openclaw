import sys

def main():
    file_path = "apps/android/app/src/main/java/ai/openclaw/app/node/SmsManager.kt"
    with open(file_path, "r") as f:
        content = f.read()

    # Imports
    content = content.replace(
        "import kotlinx.serialization.encodeToString\nimport ai.openclaw.app.PermissionRequester",
        "import kotlinx.serialization.encodeToString\nimport kotlinx.serialization.json.JsonArray\nimport android.provider.Telephony\nimport ai.openclaw.app.PermissionRequester"
    )

    # ReadResult struct
    target_result = "    data class SendResult("
    read_result = """    data class ReadResult(
        val ok: Boolean,
        val error: String? = null,
        val payloadJson: String,
    )

"""
    content = content.replace(target_result, read_result + target_result)

    # Permission check for READ_SMS
    has_send = "    fun hasSmsPermission(): Boolean {"
    has_read = """    fun hasReadSmsPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_SMS
        ) == PackageManager.PERMISSION_GRANTED
    }

"""
    content = content.replace(has_send, has_read + has_send)

    ensure_send = "    private suspend fun ensureSmsPermission(): Boolean {"
    ensure_read = """    private suspend fun ensureReadSmsPermission(): Boolean {
        if (hasReadSmsPermission()) return true
        val requester = permissionRequester ?: return false
        val results = requester.requestIfMissing(listOf(Manifest.permission.READ_SMS))
        return results[Manifest.permission.READ_SMS] == true
    }

"""
    content = content.replace(ensure_send, ensure_read + ensure_send)

    # Read logic
    ok_result = "    private fun okResult("
    read_logic = """    /**
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

"""
    content = content.replace(ok_result, read_logic + ok_result)

    with open(file_path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
