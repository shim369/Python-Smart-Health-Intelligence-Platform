"""Streamlitアプリのエントリーポイント(ルーター)。

`st.navigation()` + `st.Page()`により、ファイル名(ASCII)と
サイドバー表示名(日本語)を分離する。未認証時はログインページのみを
ナビゲーションに含めることで、実質的な認証ガードとしても機能させる
(architecture.md Section 9.1 Session Lifecycle)。

認証はStreamlit標準の`st.login()`が発行する認証Cookieに一本化する。
ブラウザ更新で`st.session_state`(`AuthSessionState`)が失われても、
Cookie自体は残るため`st.user["is_logged_in"]`はTrueのままとなる。
その場合はここで許可リストチェック→User取得/作成をやり直し、
`AuthSessionState`へ再度ログイン状態を反映する。

各ページ内の`auth_guard.require_login()`は、直接URLアクセス等に
対する防御として残す(多層防御)。
"""

from __future__ import annotations

import streamlit as st
from i18n import t
from services import get_user_service

from health_intelligence.auth import AuthSessionState, is_email_allowed, parse_allowed_emails
from health_intelligence.config import load_environment
from health_intelligence.logging_config import configure_logging

load_environment()
configure_logging()

# ブラウザのタブ情報
st.set_page_config(page_title="Smart Health Intelligence Platform")

# 全ページ共通の見た目調整。h1サイズの調整に加え、.streamlit/config.tomlの
# ヘルスケア系配色(エメラルド×スカイブルー)に合わせて、背景グラデーションと
# カード・ボタン・タブのモダン/ミニマルな装飾を適用する。
# data-testid依存のセレクタはStreamlitのバージョンアップで変わりうるため、
# 見た目が崩れても機能には影響しない範囲(装飾のみ)に留めている。
st.markdown(
    """
    <style>
    h1 {
        font-size: clamp(18px, 4vw, 28px) !important;
    }

    /* 見出し(h1〜h3、アイコン込み)は黒文字だと地味なので、テーマのアクセント
       カラーで塗る。h1はページの顔なのでグラデーション、h2/h3は可読性を
       優先して単色の濃いティールにする。 */
    h1 {
        background: linear-gradient(135deg, #0d9488, #0284c7);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    h2, h3 {
        color: #0f766e !important;
    }

    :root {
        --shi-accent-1: #10b981;
        --shi-accent-2: #0ea5e9;
        --shi-card-bg: rgba(255, 255, 255, 0.70);
        --shi-card-border: rgba(15, 23, 42, 0.07);
        --shi-shadow: 0 8px 30px rgba(15, 23, 42, 0.07);
    }

    [data-testid="stApp"] {
        background:
            radial-gradient(1200px 600px at 8% -10%, rgba(16, 185, 129, 0.16), transparent 60%),
            radial-gradient(1000px 700px at 100% 0%, rgba(14, 165, 233, 0.16), transparent 55%),
            linear-gradient(180deg, #f7fbfa 0%, #eef7f5 45%, #eaf4fb 100%);
        background-attachment: fixed;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
    }

    [data-testid="stSidebarNavLink"] {
        border-radius: 999px !important;
        transition: background 0.15s ease, color 0.15s ease;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        background: linear-gradient(135deg, var(--shi-accent-1), var(--shi-accent-2)) !important;
        box-shadow: var(--shi-shadow);
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] * {
        color: #fff !important;
    }

    [data-testid="stForm"],
    [data-testid="stExpander"],
    [class*="st-key-workout-entry-"],
    [class*="st-key-recipe-card-"],
    [class*="st-key-dashboard-chart-"] {
        background: var(--shi-card-bg) !important;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-radius: 20px !important;
        box-shadow: var(--shi-shadow);
    }

    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-primaryFormSubmit"] {
        background: linear-gradient(135deg, var(--shi-accent-1), var(--shi-accent-2)) !important;
        border: none !important;
        color: #fff !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stBaseButton-primaryFormSubmit"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
        color: #fff !important;
    }

    [data-testid="stTab"] {
        padding: 6px 16px !important;
        border-radius: 999px !important;
        margin: 0 2px 4px !important;
        transition: background 0.15s ease, color 0.15s ease;
    }
    [data-testid="stTab"]:hover {
        background: rgba(15, 23, 42, 0.05);
    }
    [data-testid="stTab"][aria-selected="true"] {
        background: linear-gradient(135deg, var(--shi-accent-1), var(--shi-accent-2)) !important;
    }
    [data-testid="stTab"][aria-selected="true"]:hover {
        background: linear-gradient(135deg, var(--shi-accent-1), var(--shi-accent-2)) !important;
    }
    [data-testid="stTab"][aria-selected="true"] p {
        color: #fff !important;
    }
    [data-testid="stTab"] .react-aria-SelectionIndicator {
        display: none;
    }

    [data-testid="stDialog"] [role="dialog"] {
        border-radius: 24px !important;
        box-shadow: 0 20px 60px rgba(15, 23, 42, 0.25);
    }
    </style>
""",
    unsafe_allow_html=True,
)

auth_state = AuthSessionState(st.session_state)
auth_state.initialize()

if st.user.get("is_logged_in", False) and not auth_state.is_authenticated:
    allowed_emails = parse_allowed_emails(st.secrets.get("auth", {}).get("allowed_emails", ""))
    if not is_email_allowed(st.user.email, allowed_emails):
        st.error(t("このアプリは招待制です。"))
        st.button(t("ログアウト"), on_click=st.logout)
        st.stop()

    user = get_user_service().get_or_create_user(
        email=st.user.email, display_name=st.user.name or st.user.email
    )
    auth_state.login(user.user_id, user.locale)

login_page = st.Page("pages/login.py", title=t("ログイン"), icon=":material/login:")

if not auth_state.is_authenticated:
    pg = st.navigation([login_page])
else:
    dashboard_page = st.Page(
        "pages/dashboard.py",
        title=t("ダッシュボード"),
        icon=":material/dashboard:",
        default=True,
    )
    today_page = st.Page("pages/today.py", title=t("今日"), icon=":material/today:")
    goals_page = st.Page("pages/goals.py", title=t("長期目標"), icon=":material/track_changes:")
    csv_import_page = st.Page(
        "pages/csv_import.py", title=t("CSVインポート"), icon=":material/upload_file:"
    )
    recipe_page = st.Page("pages/recipe.py", title=t("レシピ"), icon=":material/restaurant_menu:")
    pg = st.navigation(
        [
            dashboard_page,
            today_page,
            goals_page,
            csv_import_page,
            recipe_page,
        ]
    )

pg.run()
