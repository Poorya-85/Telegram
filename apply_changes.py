#!/usr/bin/env python3
import os
import re
import sys

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def replace_in_file(path, old, new, required=True):
    content = read_file(path)
    if old not in content:
        if required:
            print(f"❌ ERROR: Could not find pattern in {path}")
            sys.exit(1)
        else:
            print(f"⚠️  SKIP: Pattern not found in {path} (optional)")
            return
    content = content.replace(old, new, 1)
    write_file(path, content)
    print(f"✅ Modified: {path}")

def regex_replace_in_file(path, pattern, replacement, required=True):
    content = read_file(path)
    new_content, count = re.subn(pattern, replacement, content)
    if count == 0:
        if required:
            print(f"❌ ERROR: Regex not matched in {path}")
            print(f"   Pattern: {pattern[:80]}")
            sys.exit(1)
        else:
            print(f"⚠️  SKIP: Regex not matched in {path} (optional)")
            return
    write_file(path, new_content)
    print(f"✅ Modified: {path} ({count} replacements)")

BASE = os.getcwd()

print("\n" + "="*50)
print("1. Package Name")
print("="*50)

# در نسخه جدید تلگرام، APP_PACKAGE توی gradle.properties هست
gradle_props = os.path.join(BASE, "gradle.properties")
if os.path.exists(gradle_props):
    regex_replace_in_file(
        gradle_props,
        r'APP_PACKAGE\s*=\s*org\.telegram\.messenger',
        'APP_PACKAGE=org.telegram.messenger.custom'
    )
else:
    # اگه gradle.properties نبود، توی build.gradle دنبال بگرد
    build_gradle = os.path.join(BASE, "TMessagesProj/build.gradle")
    regex_replace_in_file(
        build_gradle,
        r'applicationId\s*=?\s*["\']org\.telegram\.messenger["\']',
        'applicationId = "org.telegram.messenger.custom"'
    )

print("\n" + "="*50)
print("2. arm64-v8a Only")
print("="*50)

# توی هر دو build.gradle تغییر بده
for gradle_path in [
    "TMessagesProj/build.gradle",
    "TMessagesProj_AppHockeyApp/build.gradle"
]:
    full_path = os.path.join(BASE, gradle_path)
    if os.path.exists(full_path):
        regex_replace_in_file(
            full_path,
            r'abiFilters\s+"armeabi-v7a",\s*"arm64-v8a",\s*"x86",\s*"x86_64"',
            'abiFilters "arm64-v8a"',
            required=False
        )

print("\n" + "="*50)
print("3. Persian Translation Target")
print("="*50)

translate_controller = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/messenger/TranslateController.java")
if os.path.exists(translate_controller):
    regex_replace_in_file(
        translate_controller,
        r'(String\s+\w*[Ll]ang\w*\s*=\s*)LocaleController\.getInstance\(\)\.getCurrentLocale\(\)\.getLanguage\(\)',
        r'\1"fa"',
        required=False
    )
else:
    print("⚠️  TranslateController.java not found - skipping")

print("\n" + "="*50)
print("4. Show ID in Profile")
print("="*50)

profile_activity = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/ui/ProfileActivity.java")

if os.path.exists(profile_activity):
    content = read_file(profile_activity)
    if "SHOW_ID_MENU_ITEM" not in content:
        regex_replace_in_file(
            profile_activity,
            r'(private\s+static\s+final\s+int\s+edit\s*=\s*\d+;)',
            r'\1\n    private static final int SHOW_ID_MENU_ITEM = 9999;',
            required=False
        )
        regex_replace_in_file(
            profile_activity,
            r'(otherItem\.addSubItem\(edit,)',
            r'otherItem.addSubItem(SHOW_ID_MENU_ITEM, "Show ID");\n            \1',
            required=False
        )
        show_id_handler = '''} else if (id == SHOW_ID_MENU_ITEM) {
                long uid = userId;
                String createdDate = estimateAccountCreationDate(uid);
                androidx.appcompat.app.AlertDialog.Builder builder =
                    new androidx.appcompat.app.AlertDialog.Builder(getParentActivity());
                builder.setTitle("User ID");
                builder.setMessage("ID: " + uid + "\\n\\nCreated approximately:\\n" + createdDate);
                builder.setPositiveButton("Copy ID", (dialog, which) -> {
                    android.content.ClipboardManager clipboard =
                        (android.content.ClipboardManager) getParentActivity()
                        .getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                    android.content.ClipData clip =
                        android.content.ClipData.newPlainText("Telegram ID", String.valueOf(uid));
                    clipboard.setPrimaryClip(clip);
                    android.widget.Toast.makeText(getParentActivity(),
                        "ID copied!", android.widget.Toast.LENGTH_SHORT).show();
                });
                builder.setNegativeButton("Close", null);
                showDialog(builder.create());'''
        regex_replace_in_file(
            profile_activity,
            r'(} else if \(id == edit\) \{)',
            show_id_handler + r'\n            \1',
            required=False
        )
        estimate_method = '''
    private String estimateAccountCreationDate(long userId) {
        long[][] milestones = {
            {1L, 2013, 1}, {100000L, 2013, 6}, {1000000L, 2014, 1},
            {10000000L, 2014, 9}, {100000000L, 2016, 3}, {500000000L, 2019, 1},
            {1000000000L, 2020, 6}, {1500000000L, 2021, 7}, {2000000000L, 2022, 6},
            {5000000000L, 2023, 6}, {7000000000L, 2024, 1},
        };
        int year = 2024, month = 1;
        for (int i = milestones.length - 1; i >= 0; i--) {
            if (userId >= milestones[i][0]) {
                year = (int) milestones[i][1];
                month = (int) milestones[i][2];
                break;
            }
        }
        String[] months = {"January","February","March","April","May","June",
                           "July","August","September","October","November","December"};
        return months[month - 1] + " " + year;
    }
'''
        content = read_file(profile_activity)
        last_brace = content.rfind('}')
        content = content[:last_brace] + estimate_method + content[last_brace:]
        write_file(profile_activity, content)
        print(f"✅ Added estimateAccountCreationDate")

print("\n" + "="*50)
print("5. Message Timestamps with Seconds")
print("="*50)

locale_controller = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/messenger/LocaleController.java")
if os.path.exists(locale_controller):
    regex_replace_in_file(
        locale_controller,
        r'(formatterDay\s*=\s*FastDateFormat\.getInstance\()"HH:mm"',
        r'\1"HH:mm:ss"',
        required=False
    )
    regex_replace_in_file(
        locale_controller,
        r'(formatterDay\s*=\s*FastDateFormat\.getInstance\()"h:mm a"',
        r'\1"h:mm:ss a"',
        required=False
    )

print("\n" + "="*50)
print("6. Hide All Chats Tab")
print("="*50)

dialogs_activity = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java")
if os.path.exists(dialogs_activity):
    regex_replace_in_file(
        dialogs_activity,
        r'(for \(int a = 0; a < filters\.size\(\); a\+\+\) \{)',
        r'\1\n                if (filters.get(a).id == 0) continue;',
        required=False
    )

print("\n" + "="*50)
print("7. Disable Jump to Next Channel")
print("="*50)

chat_activity = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java")
if os.path.exists(chat_activity):
    regex_replace_in_file(
        chat_activity,
        r'(private boolean canJumpToNextChannel\(\) \{[^}]*return\s+)true',
        r'\1false',
        required=False
    )

print("\n" + "="*50)
print("8. Sticker Limit 200")
print("="*50)

media_data = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/messenger/MediaDataController.java")
if os.path.exists(media_data):
    regex_replace_in_file(
        media_data,
        r'(stickers\.size\(\)\s*>=?\s*)120',
        r'\1200',
        required=False
    )

print("\n" + "="*50)
print("9. Disable Greeting Sticker")
print("="*50)

if os.path.exists(media_data):
    regex_replace_in_file(
        media_data,
        r'(public TLRPC\.Document getGreetingSticker\(\) \{\n)',
        r'\1        return null;\n',
        required=False
    )

print("\n" + "="*50)
print("✅ All patches applied!")
print("="*50 + "\n")
