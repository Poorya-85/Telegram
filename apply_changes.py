#!/usr/bin/env python3
import os
import re
import sys
import json
import glob

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

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

gradle_props = os.path.join(BASE, "gradle.properties")
if os.path.exists(gradle_props):
    regex_replace_in_file(
        gradle_props,
        r'APP_PACKAGE\s*=\s*org\.telegram\.messenger',
        'APP_PACKAGE=org.telegram.messenger.custom'
    )
else:
    build_gradle = os.path.join(BASE, "TMessagesProj/build.gradle")
    regex_replace_in_file(
        build_gradle,
        r'applicationId\s*=?\s*["\']org\.telegram\.messenger["\']',
        'applicationId = "org.telegram.messenger.custom"'
    )

print("\n" + "="*50)
print("2. arm64-v8a Only")
print("="*50)

for gradle_path in glob.glob(os.path.join(BASE, "*/build.gradle")):
    regex_replace_in_file(
        gradle_path,
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
    found = False
    for pattern, replacement in [
        (r'(String\s+\w*[Ll]ang\w*\s*=\s*)LocaleController\.getInstance\(\)\.getCurrentLocale\(\)\.getLanguage\(\)', r'\1"fa"'),
        (r'(toLang\s*=\s*)LocaleController\.getInstance\(\)\.getCurrentLocale\(\)\.getLanguage\(\)', r'\1"fa"'),
        (r'Locale\.getDefault\(\)\.getLanguage\(\)', '"fa"'),
    ]:
        content = read_file(translate_controller)
        if re.search(pattern, content):
            regex_replace_in_file(translate_controller, pattern, replacement, required=False)
            found = True
            break
    if not found:
        print("⚠️  Could not find translation language pattern - skipping")
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
    else:
        print("⚠️  Show ID already added - skipping")

print("\n" + "="*50)
print("5. Message Timestamps with Seconds")
print("="*50)

locale_controller = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/messenger/LocaleController.java")
if os.path.exists(locale_controller):
    found = False
    for pattern, replacement in [
        (r'(formatterDay\s*=\s*FastDateFormat\.getInstance\()"HH:mm"', r'\1"HH:mm:ss"'),
        (r'(formatterDay\s*=\s*FastDateFormat\.getInstance\()"h:mm a"', r'\1"h:mm:ss a"'),
        (r'"HH:mm"', '"HH:mm:ss"'),
    ]:
        content = read_file(locale_controller)
        if re.search(pattern, content):
            regex_replace_in_file(locale_controller, pattern, replacement, required=False)
            found = True
            break
    if not found:
        print("⚠️  Could not find time format pattern - skipping")

print("\n" + "="*50)
print("6. Hide All Chats Tab")
print("="*50)

dialogs_activity = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java")
if os.path.exists(dialogs_activity):
    found = False
    for p in [
        r'(for \(int a = 0; a < filters\.size\(\); a\+\+\) \{)',
        r'(for \(int i = 0; i < filters\.size\(\); i\+\+\) \{)',
    ]:
        content = read_file(dialogs_activity)
        if re.search(p, content):
            regex_replace_in_file(
                dialogs_activity, p,
                r'\1\n                if (filters.get(a).id == 0) continue;',
                required=False
            )
            found = True
            break
    if not found:
        print("⚠️  Could not find filters loop - skipping")

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
print("10. Fix google-services.json for custom package")
print("="*50)

gs_files = glob.glob(os.path.join(BASE, "*/google-services.json"))
if not gs_files:
    print("⚠️  No google-services.json found")
else:
    for full_gs in gs_files:
        gs_path = os.path.relpath(full_gs, BASE)
        try:
            with open(full_gs, 'r') as f:
                gs = json.load(f)
            changed = False
            for client in gs.get('client', []):
                pkg = client.get('client_info', {}).get('android_client_info', {}).get('package_name', '')
                if pkg == 'org.telegram.messenger':
                    client['client_info']['android_client_info']['package_name'] = 'org.telegram.messenger.custom'
                    changed = True
            if changed:
                with open(full_gs, 'w') as f:
                    json.dump(gs, f, indent=2)
                print(f"✅ Updated {gs_path}")
            else:
                print(f"⚠️  No matching package in {gs_path}")
        except Exception as e:
            print(f"⚠️  Could not parse {gs_path}: {e}")

print("\n" + "="*50)
print("✅ All patches applied!")
print("="*50 + "\n")
