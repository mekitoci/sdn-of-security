#!/bin/bash

# 檢查 mininet-vm 是否已經掛載了資料夾
MOUNT_STATUS=$(multipass info mininet-vm | grep /Users/yang/code/sdn-of-security)

# 如果尚未掛載，則進行掛載
if [ -z "$MOUNT_STATUS" ]; then
    echo "正在掛載資料夾到 mininet-vm..."
    multipass mount /Users/yang/code/sdn-of-security mininet-vm:/home/ubuntu/sdn-of-security
    echo "掛載完成！資料夾已共享到 /home/ubuntu/sdn-of-security"
else
    echo "資料夾已經掛載到 mininet-vm"
fi

# 進入 mininet-vm 的 shell
echo "正在連接到 mininet-vm..."
multipass shell mininet-vm