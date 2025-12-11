import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# --- 設定: パスワードとファイルの場所 ---
ADMIN_PASSWORD = "gamu" # ※公開後、誰も知らないパスワードに変更してください。
PHOTO_DIR = "photos"
DATA_FILE = "diary.csv"
NOTICE_FILE = "notices.csv" # 👈 お知らせ用の新しいファイル

# --- 状態管理の初期化 ---
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

if not os.path.exists(NOTICE_FILE): #お知らせCSVの初期化
    df_notice = pd.DataFrame(columns=["日付", "お知らせ内容"])
    df_notice.to_csv(NOTICE_FILE, index=False)

# --- ページ設定の追加（フッター非表示を安全に設定）---
st.set_page_config(
    page_title="ハムスター観察日記",
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.markdown(
    """
    <style>
    /* 画面下部の「Made with Streamlit」フッターを非表示 */
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)


# --- 共通関数：データ操作 ---

# データを読み込む関数 (IDを振るために使用)
def load_data():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        df = pd.read_csv(DATA_FILE)
        if not df.empty:
            df['id'] = df.index
            return df
    return pd.DataFrame(columns=["日付", "内容", "画像パス", "id"])

def delete_row(row_id):
    current_df = load_data()
    df_after_delete = current_df[current_df['id'] != row_id]
    df_after_delete.drop(columns=['id'], errors='ignore').to_csv(DATA_FILE, index=False)

def update_data(edit_id, new_date, new_content):
    current_df = load_data()
    idx = current_df[current_df['id'] == edit_id].index
    current_df.loc[idx, '日付'] = new_date
    current_df.loc[idx, '内容'] = new_content
    current_df.drop(columns=['id']).to_csv(DATA_FILE, index=False)


# --- 共通関数：お知らせデータ操作 (新規追加) ---

def load_notice_data():
    if os.path.exists(NOTICE_FILE) and os.path.getsize(NOTICE_FILE) > 0:
        df = pd.read_csv(NOTICE_FILE)
        if not df.empty:
            df['id'] = df.index
            return df
    return pd.DataFrame(columns=["日付", "お知らせ内容", "id"])

def delete_notice(row_id):
    current_df = load_notice_data()
    df_after_delete = current_df[current_df['id'] != row_id]
    df_after_delete.drop(columns=['id'], errors='ignore').to_csv(NOTICE_FILE, index=False)

def update_notice(edit_id, new_date, new_content):
    current_df = load_notice_data()
    idx = current_df[current_df['id'] == edit_id].index
    current_df.loc[idx, '日付'] = new_date
    current_df.loc[idx, 'お知らせ内容'] = new_content
    current_df.drop(columns=['id']).to_csv(NOTICE_FILE, index=False)


# --- 画面構成：サイドバーの認証 ---

with st.sidebar:
    st.header("管理者認証")
    
    if st.session_state.authenticated:
        st.success("編集モード：認証済み")
        if st.button("ログアウト", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.edit_id = None
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
st.title("■ハムスターのがむちゃん 観察日記")


# =======================================================
# 📢 【新規追加】全体お知らせ欄 (管理機能付き)
# =======================================================
st.header("by miwa")

# 編集モードの場合、既存のデータを取得
edit_notice = None
# お知らせ編集IDが設定されているかチェック
if st.session_state.edit_id is not None:
    all_notice_data = load_notice_data()
    if not all_notice_data.empty:
        records = all_notice_data[all_notice_data['id'] == st.session_state.edit_id]
        if not records.empty:
            edit_notice = records.iloc[0]

# --- 認証済みの場合のみ、お知らせ作成・編集フォームを表示 ---
if st.session_state.authenticated:
    
    # お知らせフォームはExpander内に格納
    with st.expander(f"⚙️ お知らせ作成/編集 {'(編集中)' if edit_notice is not None else ''}"):
        
        default_notice_date = edit_notice['日付'] if edit_notice is not None else datetime.now()
        default_notice_content = edit_notice['お知らせ内容'] if edit_notice is not None and pd.notna(edit_notice['お知らせ内容']) else "新しいお知らせの内容をここに記載..."

        notice_date = st.date_input("お知らせ日付", default_notice_date, key="notice_date")
        notice_content = st.text_area("お知らせ内容", default_notice_content, height=100, key="notice_content")

        save_notice_button_text = "変更を保存する" if edit_notice is not None else "お知らせを投稿する"

        if st.button(save_notice_button_text, type="primary", key="save_notice"):
            if edit_notice is not None:
                # 編集処理
                update_notice(st.session_state.edit_id, notice_date, notice_content)
                st.session_state.edit_id = None
                st.success("お知らせを変更しました！")
            else:
                # 新規投稿処理
                new_notice_data = pd.DataFrame({"日付": [notice_date], "お知らせ内容": [notice_content]})
                new_notice_data.to_csv(NOTICE_FILE, mode='a', header=False, index=False)
                st.success("新しいお知らせを投稿しました！")
            st.rerun() 
else:
    st.info("📢 お知らせの投稿・編集・削除を行うには、左側のサイドバーで認証してください。")

st.markdown("---")
st.subheader("■管理人掲示板")

# --- 全ユーザー向けのお知らせ一覧表示 ---
df_notice_display = load_notice_data()

if not df_notice_display.empty:
    # 日付の新しい順にソート (最も新しいものが上に来る)
    df_notice_display = df_notice_display.sort_values(by="日付", ascending=False)
    
    for index, row in df_notice_display.iterrows():
        st.write(f"**{row['日付']}**")
        st.markdown(f"> {row['お知らせ内容']}")
        
        # 認証済みの場合のみ編集・削除ボタンを表示
        if st.session_state.authenticated:
            col_a, col_b, col_c = st.columns([0.1, 0.1, 0.8])
            
            with col_a:
                if st.button("編集", key=f"edit_notice_{row['id']}"):
                    st.session_state.edit_id = row['id']
                    st.rerun()
            
            with col_b:
                if st.button("削除", key=f"delete_notice_{row['id']}", type="primary"):
                    delete_notice(row['id'])
                    st.toast(f"{row['日付']}のお知らせを削除しました。")
                    st.rerun()
        st.markdown("---")
else:
    st.info("現在、お知らせはありません。")
# =======================================================


# 1. 入力フォーム (新規作成/編集)
edit_record = None
# 日記編集IDが設定されているかチェック
if st.session_state.edit_id is not None:
    all_data = load_data()
    # 既存の日記編集処理
    if not all_data.empty:
        records = all_data[all_data['id'] == st.session_state.edit_id]
        if not records.empty:
            edit_record = records.iloc[0]


# --- 認証済みの場合のみ、作成・編集フォームを表示 ---
if st.session_state.authenticated:
    
    with st.container():
        # 管理者向けステータス通知 (認証が成功したことの確認用)
        st.success("✅ **管理者モード**：日記の作成・編集が可能です。")
        
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
        
        # ※編集時の画像更新は複雑なため、新規投稿時のみ有効
        if edit_record is None:
            photo = st.file_uploader("写真を追加 (任意)", type=['jpg', 'png', 'jpeg'])
        else:
            st.markdown(f"**💡 編集モードでは、写真の変更はできません。**")
            photo = None 

        # 保存ボタンのテキスト
        save_button_text = "変更を保存する" if edit_record is not None else "日記を保存する"

        if st.button(save_button_text, type="primary"):
            image_path = None
            
            # 1. 新規投稿時の画像保存処理と回転修正
            if edit_record is None and photo is not None:
                file_name = f"{date}_{photo.name}"
                save_path = os.path.join(PHOTO_DIR, file_name)
                
                try:
                    img = Image.open(photo)
                    if hasattr(img, '_getexif'):
                        exif = img._getexif()
                        orientation = exif.get(0x0112) if exif else 1
                        
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
                        
                        img.save(save_path, exif=b'')
                    
                    image_path = save_path
                
                except Exception as e:
                    st.warning(f"画像回転情報の修正中にエラーが発生しました: {e}")
                    with open(save_path, "wb") as f:
                        f.write(photo.getbuffer())
                    image_path = save_path
            
            if edit_record is not None:
                # 2. 編集（上書き保存）処理
                update_data(st.session_state.edit_id, date, content)
                st.session_state.edit_id = None
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
st.subheader("これまでの日記")

df_display = load_data()

if not df_display.empty:
    df_display = df_display.sort_values(by="日付", ascending=False)
    
    for index, row in df_display.iterrows():
        expander_title = f"🗓️ {row['日付']} の日記"
        if pd.notna(row['内容']) and row['内容']:
             expander_title += f" - {row['内容'][:20]}..."

        with st.expander(expander_title):
            st.write(row['内容'])
            
            if pd.notna(row['画像パス']) and row['画像パス']:
                st.image(row['画像パス'])
            
            # 認証済みの場合のみボタンを表示
            if st.session_state.authenticated:
                st.markdown("---")
                
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2]) 
                
                with col2:
                    if st.button("編集", key=f"edit_{row['id']}"):
                        st.session_state.edit_id = row['id']
                        st.rerun() 
                        
                with col3:
                    if st.button("削除", key=f"delete_{row['id']}", type="primary"):
                        delete_row(row['id'])
                        st.toast(f"{row['日付']} の日記を削除しました。")
                        st.rerun()
else:
    st.info("まだ日記がありません。")




