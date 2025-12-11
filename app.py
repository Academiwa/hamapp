import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 設定: パスワードとファイルの場所 ---
ADMIN_PASSWORD = "hamu-edit" # 👈 ここを任意の秘密のパスワードに変更してください
PHOTO_DIR = "photos"
DATA_FILE = "diary.csv"

# --- 状態管理の初期化 ---
# 認証状態、編集対象IDを保持
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# フォルダとCSVファイルの初期化
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["日付", "内容", "画像パス"])
    df.to_csv(DATA_FILE, index=False)


# --- 共通関数：データ操作 ---

# データを読み込む関数 (IDを振るために使用)
def load_data():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        df = pd.read_csv(DATA_FILE)
        # データが空でなければIDを振る
        if not df.empty:
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

# データの更新関数 (編集)
def update_data(edit_id, new_date, new_content):
    current_df = load_data()
    
    # 編集対象のIDを持つ行を特定し、内容を上書き
    idx = current_df[current_df['id'] == edit_id].index
    
    # 新しいデータで上書き
    current_df.loc[idx, '日付'] = new_date
    current_df.loc[idx, '内容'] = new_content
    
    # ID列を削除してCSVに上書き保存
    current_df.drop(columns=['id']).to_csv(DATA_FILE, index=False)


# --- 画面構成：サイドバーの認証 ---

with st.sidebar:
    st.header("管理者認証")
    
    if st.session_state.authenticated:
        st.success("編集モード：認証済み")
        if st.button("ログアウト", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.edit_id = None # 編集モードも解除
            st.rerun()
    else:
        st.info("日記の作成・編集にはパスワードが必要です。")
        password_input = st.text_input("パスワードを入力", type="password")
        
        if st.button("編集モードへ", key="login_btn"):
            if password_input == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.success("ログイン成功！")
                st.rerun()
            else:
                st.error("パスワードが違います。")


# --- 画面構成：メインパネル ---
st.title("🐹 ハムスター観察日記")


# 1. 入力フォーム (新規作成/編集)
# 編集モードの場合、既存のデータを取得
edit_record = None
if st.session_state.edit_id is not None:
    all_data = load_data()
    # データが空でないか確認してから検索
    if not all_data.empty:
        records = all_data[all_data['id'] == st.session_state.edit_id]
        if not records.empty:
            edit_record = records.iloc[0]

# --- 認証済みの場合のみ、作成・編集フォームを表示 ---
if st.session_state.authenticated:
    
    with st.container():
        # タイトルを動的に変更
        if edit_record is not None:
            st.subheader("✏️ 日記を編集する")
        else:
            st.subheader("📝 新しい日記を書く")
        
        # フォームの初期値を設定
        default_date = edit_record['日付'] if edit_record is not None else datetime.now()
        default_content = edit_record['内容'] if edit_record is not None and pd.notna(edit_record['内容']) else "今日の様子をここに書く..."

        date = st.date_input("日付", default_date)
        content = st.text_area("今日の様子", default_content, height=150)
        
        # ※編集時の画像更新は複雑なため、新規投稿時のみ有効とします
        if edit_record is None:
            photo = st.file_uploader("写真を追加 (任意)", type=['jpg', 'png', 'jpeg'])
        else:
            st.markdown(f"**💡 編集モードでは、写真の変更はできません。**")
            photo = None # 編集モードでは画像アップロードは無視する

        # 保存ボタンのテキスト
        save_button_text = "変更を保存する" if edit_record is not None else "日記を保存する"

        if st.button(save_button_text, type="primary"):
            image_path = None
            
            # 1. 新規投稿時の画像保存処理
            if edit_record is None and photo is not None:
                file_name = f"{date}_{photo.name}"
                save_path = os.path.join(PHOTO_DIR, file_name)
                with open(save_path, "wb") as f:
                    f.write(photo.getbuffer())
                image_path = save_path
            
            if edit_record is not None:
                # 2. 編集（上書き保存）処理
                update_data(st.session_state.edit_id, date, content)
                st.session_state.edit_id = None # 編集モードを解除
                st.success("変更を保存しました！✅")
            else:
                # 3. 新規保存処理
                new_data = pd.DataFrame({"日付": [date], "内容": [content], "画像パス": [image_path]})
                new_data.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.success("新規日記を保存しました！🐹")

            st.rerun() 
else:
    st.info("日記の新規作成・編集・削除を行うには、左側のサイドバーで認証してください。")


# 2. 過去の日記を表示
st.divider()
st.subheader("📖 過去の記録")

df_display = load_data()

if not df_display.empty:
    # 新しい日付が上に来るように逆順にソート
    df_display = df_display.sort_values(by="日付", ascending=False)
    
    for index, row in df_display.iterrows():
        # Expanderのタイトル設定
        expander_title = f"🗓️ {row['日付']} の日記"
        if pd.notna(row['内容']) and row['内容']:
             expander_title += f" - {row['内容'][:20]}..."

        with st.expander(expander_title):
            # 1. 日記の内容表示
            st.write(row['内容'])
            
            # 2. 画像があれば表示
            if pd.notna(row['画像パス']) and row['画像パス']:
                st.image(row['画像パス'])
            
            # 3. 認証済みの場合のみボタンを表示
            if st.session_state.authenticated:
                st.markdown("---")
                
                # 削除ボタンと編集ボタンを配置
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2]) 
                
                # 編集ボタン
                with col2:
                    if st.button("編集", key=f"edit_{row['id']}"):
                        st.session_state.edit_id = row['id']
                        st.rerun() 
                        
                # 削除ボタン
                with col3:
                    if st.button("削除", key=f"delete_{row['id']}", type="primary"):
                        delete_row(row['id'])
                        st.toast(f"{row['日付']} の日記を削除しました。")
                        st.rerun()
else:
    st.info("まだ日記がありません。")
