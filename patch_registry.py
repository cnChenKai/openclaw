import sys

def main():
    file_path = "apps/android/app/src/main/java/ai/openclaw/app/node/InvokeCommandRegistry.kt"
    with open(file_path, "r") as f:
        content = f.read()

    target = '      InvokeCommandSpec(\n        name = OpenClawSmsCommand.Send.rawValue,\n        availability = InvokeCommandAvailability.SmsAvailable,\n      ),'
    replacement = '      InvokeCommandSpec(\n        name = OpenClawSmsCommand.Send.rawValue,\n        availability = InvokeCommandAvailability.SmsAvailable,\n      ),\n      InvokeCommandSpec(\n        name = OpenClawSmsCommand.Read.rawValue,\n        availability = InvokeCommandAvailability.SmsAvailable,\n      ),'
    content = content.replace(target, replacement)

    with open(file_path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
