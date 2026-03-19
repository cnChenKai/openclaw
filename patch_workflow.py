import sys

def main():
    file_path = ".github/workflows/android-debug.yml"
    with open(file_path, "r") as f:
        content = f.read()

    target = """      - name: Make gradlew executable
        run: chmod +x ./gradlew"""

    replacement = """      - name: Ensure consistent debug signing
        env:
          DEBUG_KEYSTORE_BASE64: ${{ secrets.DEBUG_KEYSTORE_BASE64 }}
        run: |
          mkdir -p ~/.android
          if [ -n "$DEBUG_KEYSTORE_BASE64" ]; then
            echo "Using consistent debug keystore from secrets."
            echo "$DEBUG_KEYSTORE_BASE64" | base64 --decode > ~/.android/debug.keystore
          else
            echo "::warning::DEBUG_KEYSTORE_BASE64 secret is not set! Using ephemeral debug keystore."
            echo "::warning::This means direct overwrite installs will fail due to signature mismatch."
            echo "::warning::To fix this, create a debug keystore, base64 encode it, and save it as DEBUG_KEYSTORE_BASE64 in GitHub Secrets."
          fi

      - name: Make gradlew executable
        run: chmod +x ./gradlew"""

    content = content.replace(target, replacement)

    with open(file_path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
