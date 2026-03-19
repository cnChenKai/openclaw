import sys

def main():
    file_path = "apps/android/app/src/main/java/ai/openclaw/app/protocol/OpenClawProtocolConstants.kt"
    with open(file_path, "r") as f:
        content = f.read()

    target = 'enum class OpenClawSmsCommand(val rawValue: String) {\n  Send("sms.send"),\n  ;'
    replacement = 'enum class OpenClawSmsCommand(val rawValue: String) {\n  Send("sms.send"),\n  Read("sms.read"),\n  ;'
    content = content.replace(target, replacement)

    with open(file_path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
