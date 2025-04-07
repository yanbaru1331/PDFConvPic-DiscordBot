# RePDFConv

discord上でPDFを画像に変換するbot
## 環境
```
Ubuntu 20.04
python 3.11
```

## 使い方
```bash
docker build -t 任意のイメージ名 .
docker compose build --no-cache
docker compose up -d
docker container ps
docker exec -it 控えたCONTAIENR_ID bash
```

コンテナ内に入ったら`.env`ファイルを作成して
```
GUILD_ID
DISCORD_TOKEN
```
をそれぞれ記載してください

```bash
cd ./scr
python3.11 main.py
```

## Special thanks
https://github.com/cffnpwr

## 詳しい説明
https://qiita.com/yanbaru/items/fdd95f574ae4daae4136
