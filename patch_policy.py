import sys

def main():
    file_path = "src/gateway/node-command-policy.ts"
    with open(file_path, "r") as f:
        content = f.read()

    # Replace SMS_DANGEROUS_COMMANDS
    content = content.replace(
        'const SMS_DANGEROUS_COMMANDS = ["sms.send"];',
        'const SMS_DANGEROUS_COMMANDS = ["sms.send", "sms.read"];'
    )

    # Replace android defaults
    content = content.replace(
        '    "sms.send",\n  ],\n  macos:',
        '    "sms.send",\n    "sms.read",\n  ],\n  macos:'
    )

    with open(file_path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
