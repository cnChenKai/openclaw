import sys

def main():
    file_path = "apps/android/app/src/main/java/ai/openclaw/app/node/InvokeDispatcher.kt"
    with open(file_path, "r") as f:
        content = f.read()

    target = "OpenClawSmsCommand.Send.rawValue -> smsHandler.handleSmsSend(paramsJson)"
    replacement = "OpenClawSmsCommand.Send.rawValue -> smsHandler.handleSmsSend(paramsJson)\n      OpenClawSmsCommand.Read.rawValue -> smsHandler.handleSmsRead(paramsJson)"
    content = content.replace(target, replacement)

    with open(file_path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
