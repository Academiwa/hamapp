import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 設定: 画像やデータを保存する場所を作る ---
PHOTO_DIR = "photos"
DATA_FILE = "diary.csv"

# フォルダがなければ作る
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

# データファイル(CSV)がなければ作る（項目行だけ作成）
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["日付", "内容", "画像パス"])
    df.to_csv(DATA_FILE, index=False)

# データを読み込む関数 (IDを振るために使用)
def load_data():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        # ヘッダーを読み込み、データがあるか確認
        df = pd.read_csv(DATA_FILE)
        if not df.empty:
            # データのインデックスをIDとして使用
            df['id'] = df.index
            return df
    return pd.DataFrame(columns=["日付", "内容", "画像パス", "id"])

# 指定されたIDの行を削除し、CSVを上書きする関数
def delete_row(row_id):
    current_df = load_data()
    
    # 削除対象の行を特定（IDが一致しないものだけ残す）
    df_after_delete = current_df[current_df['id'] != row_id]
    
    # 元のCSVに上書き保存 (ID列は保存しない)
    df_after_delete.drop(columns=['id'], errors='ignore').to_csv(DATA_FILE, index=False)
    
    # 【写真ファイルの削除は省略しています】

# --- ここから画面を作る ---
st.title("🐹 ハムスター観察日記")

# 1. 入力フォーム
with st.container():
    st.subheader("📝 新しい日記を書く")
    
    # 日付、テキスト、画像入力
    date = st.date_input("日付", datetime.now())
    content = st.text_area("今日の様子", placeholder="例：回し車で元気に走ってた！")
    photo = st.file_uploader("写真を追加 (任意)", type=['jpg', 'png', 'jpeg'])

    if st.button("日記を保存する"):
        image_path = None
        
        # 写真がアップロードされていたら保存処理 (既存のコード)
        if photo is not None:
            # ファイル名を「日付_ファイル名」にして重複を防ぐ
            file_name = f"{date}_{photo.name}"
            save_path = os.path.join(PHOTO_DIR, file_name)
            
            # 画像を書き出す
            with open(save_path, "wb") as f:
                f.write(photo.getbuffer())
            image_path = save_path
        
        # データをCSVに追加保存 (既存のコード)
        new_data = pd.DataFrame({
            "日付": [date],
            "内容": [content],
            "画像パス": [image_path] # 画像がない場合はNoneになる
        })
        
        # 追記モードで保存
        new_data.to_csv(DATA_FILE, mode='a', header=False, index=False)
        st.success("保存しました！🐹")
        st.rerun() # 保存後に即座に表示を更新

# 2. 過去の日記を表示と削除ボタンの配置
st.divider() # 仕切り線
st.subheader("📖 過去の記録")

df_display = load_data()

# データがある場合のみ表示
if not df_display.empty:
    # 新しい日付が上に来るように逆順にソート（Streamlit表示用）
    df_display = df_display.sort_values(by="日付", ascending=False)
    
    # 日記を ID順に処理する
    for index, row in df_display.iterrows():
        # Expanderのタイトルは日記の内容で動的に設定
        expander_title = f"🗓️ {row['日付']} の日記"
        if pd.notna(row['内容']) and row['内容']:
             expander_title += f" - {row['内容'][:20]}..." # 内容の冒頭を表示

        with st.expander(expander_title):
            # 1. 日記の内容表示
            st.write(row['内容'])
            
            # 2. 画像があれば表示
            if pd.notna(row['画像パス']) and row['画像パス']:
                st.image(row['画像パス'])
            
            st.markdown("---")
            
            # 3. 削除ボタンの配置
            # ボタンのキーはユニークなIDと紐付ける
            delete_button_key = f"delete_{row['id']}"  
            
            # st.columnsを使ってボタンを右寄せっぽく配置
            col1, col2 = st.columns([0.8, 0.2])
            with col2:
                if st.button("削除", key=delete_button_key, type="primary"):
                    # 削除処理を実行
                    delete_row(row['id'])
                    
                    # 削除完了メッセージを表示し、アプリを再読み込み
                    st.toast(f"{row['日付']} の日記を削除しました。")
                    st.rerun() 
else:
    st.info("まだ日記がありません。")