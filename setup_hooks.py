import os
import sys

def install_hook():
    git_dir = ".git"
    if not os.path.exists(git_dir):
        print("Hata: .git klasörü bulunamadı. Lütfen projenin ana dizininde çalıştırın.")
        sys.exit(1)

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    
    pre_push_path = os.path.join(hooks_dir, "pre-push")

    hook_script = b"""#!/bin/bash

# Pre-push hook to check if version.json is modified.
# If version.json is missing from the commit diff, reject the push.

while read local_ref local_sha remote_ref remote_sha
do
    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # Pushing a new branch. We allow it for now.
        continue
    fi
    
    # Check if version.json is modified between remote and local
    if ! git diff --name-only $remote_sha $local_sha | grep -q "version.json"; then
        echo "=========================================================================="
        echo "ERROR: Push rejected!"
        echo "You must modify 'version.json' (bump version) before pushing."
        echo "Please update 'version.json', commit the change, and try again."
        echo "=========================================================================="
        exit 1
    fi
done

exit 0
"""

    with open(pre_push_path, "wb") as f:
        f.write(hook_script)

    print(f"Başarılı: Pre-push hook başarıyla '{pre_push_path}' konumuna yüklendi.")
    print("Artık 'version.json' dosyasını güncellemeden kod push'layamazsınız!")

if __name__ == "__main__":
    install_hook()
