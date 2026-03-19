1. **Understand SMS Read Implementation Requirements**
   - Need to add `sms.read` to `OpenClawProtocolConstants.kt` -> `OpenClawSmsCommand`.
   - Need to add `sms.read` to the TypeScript whitelist in `src/gateway/node-command-policy.ts`.
   - Need to add `Read` command to `InvokeCommandRegistry.kt` and `InvokeDispatcher.kt` in Kotlin.
   - Need to add `READ_SMS` permission handling to `SmsManager.kt`.
   - Need to implement the actual `read` function in `SmsManager.kt` using `ContentResolver` to query `content://sms/inbox` or `content://sms`.
   - Need to add `handleSmsRead` to `SmsHandler.kt`.
2. **Understand CI Signing Requirements**
   - We need a fixed keystore to build and sign APKs in `.github/workflows/android-debug.yml`.
   - Modify the workflow to:
     - Generate a keystore base64 string and save it to a file.
     - Add `signRelease` or configure `buildTypes.debug` signing config in `app/build.gradle.kts`.
     - Or rather, create a fixed `debug.keystore` file, commit it to the repository OR put it into GitHub secrets and decode it in CI.
       - *Note: As requested, the user prefers storing it securely via GitHub Secrets. I will create a python script that prints instructions on how to use secrets in GitHub Actions.*
3. **Android Manifest**
   - Need to add `<uses-permission android:name="android.permission.READ_SMS" />` to `AndroidManifest.xml` (since we need to read SMS).

4. **Detailed Implementation Steps:**
   - **Step 1:** Modify `src/gateway/node-command-policy.ts` to include `"sms.read"` in `PLATFORM_DEFAULTS.android` and `DEFAULT_DANGEROUS_NODE_COMMANDS`.
   - **Step 2:** Modify `apps/android/app/src/main/AndroidManifest.xml` to include `READ_SMS` permission.
   - **Step 3:** Modify `apps/android/app/src/main/java/ai/openclaw/app/protocol/OpenClawProtocolConstants.kt` -> `OpenClawSmsCommand` to include `Read("sms.read")`.
   - **Step 4:** Modify `apps/android/app/src/main/java/ai/openclaw/app/node/InvokeCommandRegistry.kt` -> Add `InvokeCommandSpec` for `OpenClawSmsCommand.Read.rawValue`.
   - **Step 5:** Modify `apps/android/app/src/main/java/ai/openclaw/app/node/SmsManager.kt`:
     - Add `hasReadSmsPermission()`.
     - Update `ensureSmsPermission` logic to request `READ_SMS` when needed, or create `ensureReadSmsPermission()`.
     - Implement `read(paramsJson: String?): ReadResult` returning latest SMS messages. Let's make it fetch a configurable limit (e.g., last 10-20 messages).
   - **Step 6:** Modify `apps/android/app/src/main/java/ai/openclaw/app/node/SmsHandler.kt`:
     - Implement `handleSmsRead(paramsJson: String?)`.
   - **Step 7:** Modify `apps/android/app/src/main/java/ai/openclaw/app/node/InvokeDispatcher.kt`:
     - Call `smsHandler.handleSmsRead(paramsJson)` when `command == OpenClawSmsCommand.Read.rawValue`.
   - **Step 8:** CI/CD modifications:
     - The user wants to keep a stable signing identity for the GitHub actions build.
     - I will update `.github/workflows/android-debug.yml` to generate a static debug keystore securely stored in GitHub secrets or generate one and commit it.
       - Wait, the user specifically mentioned: `"ideally store the keystore securely via GitHub Secrets (or another secure CI secret mechanism), rather than committing it directly into the repository"`.
       - I will use `echo "${{ secrets.DEBUG_KEYSTORE_BASE64 }}" | base64 -d > debug.keystore`.
       - And instruct the user to set `DEBUG_KEYSTORE_BASE64` and `DEBUG_KEYSTORE_PASS` secrets in GitHub, but wait, the debug keystore has standard password (`android`, alias `androiddebugkey`). We just need to decode it.
       - Alternatively, if the secret isn't provided, it falls back to the ephemeral one? No, they want it to always be signed with the same keystore. We can create a step that checks if the secret exists. If not, it creates a new debug keystore, signs with it, and prints a warning that the user needs to save it for future builds. Or, since I'm modifying the workflow, I can make it so it downloads the keystore from the secrets, and if it's empty, fail the build so the user knows they need to set it.
       - Actually, wait, debug keystore signing config can be set directly via gradle properties or just by replacing the `~/.android/debug.keystore`. `setup-android` or Gradle defaults to `~/.android/debug.keystore`. I can overwrite it!
