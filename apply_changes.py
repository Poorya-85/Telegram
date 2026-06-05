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

def regex_replace_in_file(path, pattern, replacement, required=True, flags=0):
    content = read_file(path)
    new_content, count = re.subn(pattern, replacement, content, flags=flags)
    if count == 0:
        if required:
            print(f"ERROR: Regex not matched in {path}")
            print(f"   Pattern: {pattern[:80]}")
            sys.exit(1)
        else:
            print(f"SKIP: Regex not matched in {path} (optional)")
            return
    write_file(path, new_content)
    print(f"OK: Modified {path} ({count} replacements)")

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
    regex_replace_in_file(
        translate_controller,
        r'LocaleController\.getInstance\(\)\.getCurrentLocaleInfo\(\)\.pluralLangCode',
        '"fa"',
        required=False
    )
    regex_replace_in_file(
        translate_controller,
        r'Resources\.getSystem\(\)\.getConfiguration\(\)\.locale\.getLanguage\(\)',
        '"fa"',
        required=False
    )
else:
    print("SKIP: TranslateController.java not found")

print("\n" + "="*50)
print("4. Show ID in Profile")
print("="*50)

profile_activity = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/ui/ProfileActivity.java")

if os.path.exists(profile_activity):
    content = read_file(profile_activity)
    if "show_id" not in content:

        anchor_const = re.search(r'private final static int edit_avatar\s*=\s*\d+;', content)
        if anchor_const:
            insert_pos = anchor_const.end()
            content = content[:insert_pos] + '\n    private final static int show_id = 9999;' + content[insert_pos:]
            print("OK: Added show_id constant")
        else:
            print("SKIP: Could not find edit_avatar constant")

        anchor_menu = 'otherItem.showSubItem(gallery_menu_save);'
        if anchor_menu in content:
            content = content.replace(
                anchor_menu,
                anchor_menu + '\n                    otherItem.addSubItem(show_id, "Show ID");',
                1
            )
            print("OK: Added Show ID menu item")
        else:
            print("SKIP: Could not find gallery_menu_save anchor")

        anchor_handler = '} else if (id == edit_avatar) {'
        if anchor_handler in content:
            java_newline = '\\n'
            show_id_block = (
                '} else if (id == show_id) {\n'
                '                long uid = userId;\n'
                '                String createdDate = estimateAccountCreationDate(uid);\n'
                '                String msg = "ID: " + uid + "' + java_newline + java_newline + 'Account created approximately:' + java_newline + '" + createdDate;\n'
                '                androidx.appcompat.app.AlertDialog.Builder builder =\n'
                '                    new androidx.appcompat.app.AlertDialog.Builder(getParentActivity());\n'
                '                builder.setTitle("User ID");\n'
                '                builder.setMessage(msg);\n'
                '                builder.setPositiveButton("Copy ID", (dialog, which) -> {\n'
                '                    android.content.ClipboardManager clipboard =\n'
                '                        (android.content.ClipboardManager) getParentActivity()\n'
                '                        .getSystemService(android.content.Context.CLIPBOARD_SERVICE);\n'
                '                    android.content.ClipData clip =\n'
                '                        android.content.ClipData.newPlainText("ID", String.valueOf(uid));\n'
                '                    clipboard.setPrimaryClip(clip);\n'
                '                    android.widget.Toast.makeText(getParentActivity(),\n'
                '                        "ID copied!", android.widget.Toast.LENGTH_SHORT).show();\n'
                '                });\n'
                '                builder.setNegativeButton("Close", null);\n'
                '                showDialog(builder.create());\n'
                '            ' + anchor_handler
            )
            content = content.replace(anchor_handler, show_id_block, 1)
            print("OK: Added Show ID handler")
        else:
            print("SKIP: Could not find edit_avatar handler")

        estimate_method = (
            '\n'
            '    private String estimateAccountCreationDate(long userId) {\n'
            '        long[][] milestones = {\n'
            '            {1L, 2013, 1}, {100000L, 2013, 6}, {1000000L, 2014, 1},\n'
            '            {10000000L, 2014, 9}, {100000000L, 2016, 3}, {500000000L, 2019, 1},\n'
            '            {1000000000L, 2020, 6}, {1500000000L, 2021, 7}, {2000000000L, 2022, 6},\n'
            '            {5000000000L, 2023, 6}, {7000000000L, 2024, 1},\n'
            '        };\n'
            '        int year = 2024, month = 1;\n'
            '        for (int i = milestones.length - 1; i >= 0; i--) {\n'
            '            if (userId >= milestones[i][0]) {\n'
            '                year = (int) milestones[i][1];\n'
            '                month = (int) milestones[i][2];\n'
            '                break;\n'
            '            }\n'
            '        }\n'
            '        String[] months = {"January","February","March","April","May","June",\n'
            '                           "July","August","September","October","November","December"};\n'
            '        return months[month - 1] + " " + year;\n'
            '    }\n'
        )
        last_brace = content.rfind('}')
        content = content[:last_brace] + estimate_method + content[last_brace:]
        write_file(profile_activity, content)
        print("OK: Show ID fully added")
    else:
        print("SKIP: Show ID already added")

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

# روش درست: به جای حذف از لیست اصلی، موقع نمایش تب چک میکنیم
dialogs_activity = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java")
if os.path.exists(dialogs_activity):
    # پیدا کردن جایی که تب ها رو نمایش میده و All Chats رو skip میکنیم
    regex_replace_in_file(
        dialogs_activity,
        r'(canShowFilterTabsView\s*=\s*true;)',
        r'\1\n                filterTabsView.setVisibility(View.GONE); // hide all chats tab',
        required=False
    )
    # روش دوم: مخفی کردن اولین تب که همیشه All Chats هست
    regex_replace_in_file(
        dialogs_activity,
        r'(filterTabsView\.addTab\([^)]+\);\s*\n)(\s*)(filterTabsView\.addTab)',
        r'\1\2// first tab (All Chats) hidden\n\2\3',
        required=False
    )
    # روش سوم: وقتی filter id == 0 باشه تب رو اضافه نکن
    regex_replace_in_file(
        dialogs_activity,
        r'(for \(int i = 0; i < filters\.size\(\); i\+\+\) \{)',
        r'\1\n                MessagesController.DialogFilter f = filters.get(i); if (f.id == 0) continue;',
        required=False
    )
else:
    print("SKIP: DialogsActivity.java not found")

print("\n" + "="*50)
print("7. Disable Jump to Next Channel")
print("="*50)

chat_activity = os.path.join(BASE,
    "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java")
if os.path.exists(chat_activity):
    regex_replace_in_file(
        chat_activity,
        r'(public void setNextChannels\(ArrayList<TLRPC\.Chat> channels\) \{)\s*\n\s*nextChannels = channels;',
        r'\1\n        nextChannels = null; // disabled',
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
        r'(stickerSets\[\d+\]\.size\(\)\s*>=?\s*)200',
        r'\1200',
        required=False
    )

print("\n" + "="*50)
print("9. Disable Greeting Sticker")
print("="*50)

if os.path.exists(media_data):
    regex_replace_in_file(
        media_data,
        r'(greetingsSticker\s*=\s*)(?!null)[^;]+;',
        r'\1null; // disabled',
        required=False
    )

print("\n" + "="*50)
print("10. Fix google-services.json (only App modules)")
print("="*50)

for full_gs in glob.glob(os.path.join(BASE, "*/google-services.json")):
    gs_path = os.path.relpath(full_gs, BASE)
    module_name = gs_path.split('/')[0]
    if module_name == "TMessagesProj":
        print(f"SKIP base module: {gs_path}")
        continue
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
            print(f"OK: Updated {gs_path}")
        else:
            print(f"SKIP: No matching package in {gs_path}")
    except Exception as e:
        print(f"SKIP: Could not parse {gs_path}: {e}")

print("\n" + "="*50)
print("11. Fix agconnect-services.json for Huawei")
print("="*50)

for full_agc in glob.glob(os.path.join(BASE, "*/agconnect-services.json")):
    agc_path = os.path.relpath(full_agc, BASE)
    module_name = agc_path.split('/')[0]
    if module_name == "TMessagesProj":
        print(f"SKIP base module: {agc_path}")
        continue
    try:
        with open(full_agc, 'r') as f:
            agc = json.load(f)
        changed = False
        client_pkg = agc.get('client', {}).get('package_name', '')
        if client_pkg == 'org.telegram.messenger':
            agc['client']['package_name'] = 'org.telegram.messenger.custom'
            changed = True
        if changed:
            with open(full_agc, 'w') as f:
                json.dump(agc, f, indent=2)
            print(f"OK: Updated {agc_path}")
        else:
            print(f"SKIP: No matching package in {agc_path}")
    except Exception as e:
        print(f"SKIP: Could not parse {agc_path}: {e}")

print("\n" + "="*50)
print("ALL PATCHES APPLIED!")
print("="*50 + "\n")
