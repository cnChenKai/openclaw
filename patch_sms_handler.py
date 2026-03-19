import sys

def main():
    file_path = "apps/android/app/src/main/java/ai/openclaw/app/node/SmsHandler.kt"
    with open(file_path, "w") as f:
        f.write("""package ai.openclaw.app.node

import ai.openclaw.app.gateway.GatewaySession

class SmsHandler(
  private val sms: SmsManager,
) {
  suspend fun handleSmsSend(paramsJson: String?): GatewaySession.InvokeResult {
    val res = sms.send(paramsJson)
    if (res.ok) {
      return GatewaySession.InvokeResult.ok(res.payloadJson)
    } else {
      val error = res.error ?: "SMS_SEND_FAILED"
      val idx = error.indexOf(':')
      val code = if (idx > 0) error.substring(0, idx).trim() else "SMS_SEND_FAILED"
      return GatewaySession.InvokeResult.error(code = code, message = error)
    }
  }

  suspend fun handleSmsRead(paramsJson: String?): GatewaySession.InvokeResult {
    val res = sms.read(paramsJson)
    if (res.ok) {
      return GatewaySession.InvokeResult.ok(res.payloadJson)
    } else {
      val error = res.error ?: "SMS_READ_FAILED"
      val idx = error.indexOf(':')
      val code = if (idx > 0) error.substring(0, idx).trim() else "SMS_READ_FAILED"
      return GatewaySession.InvokeResult.error(code = code, message = error)
    }
  }
}
""")

if __name__ == "__main__":
    main()
