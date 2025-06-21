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
st.title("🧪 抗体ラック管理アプリ（スマホ対応済み）")

if "selected" not in st.session_state:
    st.session_state.selected = None

search = st.text_input("🔍 検索（抗体名・クローン・蛍光色素）", "")

# ラックを縦並びで表示
for rack_name in RACKS:
    ROWS, COLS = RACKS[rack_name]
    st.subheader(f"🧊 {rack_name}")
    rack = data.get(rack_name, {})

    grid_html = "<div style='display: flex; flex-wrap: wrap; gap: 4px;'>"
    for i in range(ROWS):
        for j in range(COLS):
            pos = f"{chr(65+i)}{j+1}"
            ab = rack.get(pos, {"name": "", "clone": "", "fluor": "", "in_use": False})
            label = ab["name"] if ab["name"] else pos
            highlight = search.lower() in f"{ab['name']} {ab['clone']} {ab['fluor']}").lower()
            button_label = f"✅ {label}" if ab.get("in_use") else label
            color = "lime" if highlight else "white"
            grid_html += f"<button style='flex: 0 0 calc(20% - 4px); height: 32px; background-color: black; color: {color}; border: 1px solid #888;' onclick=\"window.location.href='?rack={rack_name}&pos={pos}'\">{button_label}</button>"
    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

# クエリ取得
query = st.query_params
rack_param = query.get("rack")
pos_param = query.get("pos")

if rack_param and pos_param:
    rack_name = rack_param
    pos = pos_param
    st.session_state.selected = (rack_name, pos)

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
