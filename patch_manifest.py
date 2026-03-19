import sys

def main():
    file_path = "apps/android/app/src/main/AndroidManifest.xml"
    with open(file_path, "r") as f:
        content = f.read()

    target = '<uses-permission android:name="android.permission.SEND_SMS" />'
    replacement = '<uses-permission android:name="android.permission.SEND_SMS" />\n    <uses-permission android:name="android.permission.READ_SMS" />'
    content = content.replace(target, replacement)

    with open(file_path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
