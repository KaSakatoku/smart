import streamlit as st
import json
from github import Github, GithubException

# GitHub連携情報
REPO_NAME = "KaSakatoku/smart"
FILE_PATH = "rack.json"
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo(REPO_NAME)

# ラック定義
RACKS = {
    "No1": (16, 5),
    "No2": (16, 5),
    "No3": (16, 5),
    "No4": (16, 5),
    "Stock Box": (10, 10),
}

# 初期データ取得
try:
    file = repo.get_contents(FILE_PATH, ref="heads/main")
    data = json.loads(file.decoded_content)
except GithubException as e:
    if e.status == 404:
        data = {name: {} for name in RACKS}
    else:
        st.error(f"初期読み込みエラー：{e}")
        raise e

st.set_page_config(layout="wide")
st.title("🧪 抗体ラック管理アプリ（スマホ最適化）")

if "selected" not in st.session_state:
    st.session_state.selected = None

search = st.text_input("🔍 検索（抗体名・クローン・蛍光色素）", "")

# ラックを縦並びで表示（st.columns 使用）
for rack_name in RACKS:
    ROWS, COLS = RACKS[rack_name]
    st.subheader(f"🧊 {rack_name}")
    rack = data.get(rack_name, {})

    for i in range(ROWS):
        cols = st.columns(COLS)
        for j in range(COLS):
            pos = f"{chr(65+i)}{j+1}"
            ab = rack.get(pos, {"name": "", "clone": "", "fluor": "", "in_use": False})
            label = ab["name"] if ab["name"] else pos
            highlight = search.lower() in f"{ab['name']} {ab['clone']} {ab['fluor']}".lower()
            button_label = f"✅ {label}" if ab.get("in_use") else label
            if cols[j].button(button_label, key=f"{rack_name}_{pos}"):
                st.session_state.selected = (rack_name, pos)
            if highlight:
                cols[j].markdown("<div style='height:5px;background-color:lime;'></div>", unsafe_allow_html=True)

# 編集フォーム
if st.session_state.selected:
    rack_name, pos = st.session_state.selected
    st.markdown("---")
    st.subheader(f"✏️ 編集: {rack_name} - {pos}")
    ab = data[rack_name].get(pos, {"name": "", "clone": "", "fluor": "", "in_use": False})

    ab["name"] = st.text_input("抗体名", ab["name"])
    ab["clone"] = st.text_input("クローン", ab["clone"])
    ab["fluor"] = st.text_input("蛍光色素", ab["fluor"])
    ab["in_use"] = st.checkbox("使用中", ab.get("in_use", False))

    if st.button("保存"):
        data[rack_name][pos] = ab
        try:
            file = repo.get_contents(FILE_PATH, ref="heads/main")
            repo.update_file(
                path=FILE_PATH,
                message=f"update {rack_name} {pos}",
                content=json.dumps(data, indent=2),
                sha=file.sha
            )
        except GithubException as e:
            if e.status == 409:
                st.error("GitHub上のファイルが別のセッションで更新されました。ページを更新してください。")
            elif e.status == 404:
                repo.create_file(
                    path=FILE_PATH,
                    message=f"create {rack_name} {pos}",
                    content=json.dumps(data, indent=2)
                )
            else:
                st.error(f"保存に失敗しました（{e.status}）：{e.data.get('message', '詳細不明')}。")
                raise e

        st.success("保存しました。ページを更新して反映を確認してください。")
