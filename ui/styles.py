import streamlit as st


def load_styles():
    st.markdown("""
    <style>
    :root{
      --bg:#ffffff;
      --panel:#f7f7f8;
      --border:#e5e7eb;
      --muted:#6b7280;
      --text:#111827;
    }

    .stApp{
      background:var(--bg);
      color:var(--text);
    }

    .block-container{
      max-width:980px;
      padding-top:1.25rem;
      padding-bottom:2rem;
    }

    section[data-testid="stSidebar"]{
      width:280px !important;
      min-width:280px !important;
      max-width:280px !important;
      background:var(--panel);
      border-right:1px solid var(--border);
    }

    .sidebar-title{
      font-weight:700;
      font-size:18px;
      margin-bottom:6px;
    }

    .sidebar-sub{
      color:var(--muted);
      font-size:13px;
      margin-bottom:12px;
    }

    .history-h{
      font-size:12px;
      color:var(--muted);
      margin:12px 0 6px 2px;
      font-weight:700;
      text-transform:uppercase;
    }

    .chat-shell{
      max-width:900px;
      margin:0 auto;
    }

    .row{
      display:flex;
      margin-bottom:12px;
    }

    .row.user{
      justify-content:flex-end;
    }

    .row.assistant{
      justify-content:flex-start;
    }

    .bubble{
      max-width:75%;
      border:1px solid var(--border);
      border-radius:16px;
      padding:12px 14px;
      line-height:1.6;
      background:#fff;
      white-space:pre-wrap;
      word-break:break-word;
    }

    .thinking{
      color:var(--muted);
      font-style:italic;
    }

    .empty{
      text-align:center;
      margin-top:20vh;
    }

    .empty h1{
      font-size:42px;
      margin-bottom:8px;
    }

    .empty p{
      color:var(--muted);
    }

    .quiz-card{
      border:1px solid var(--border);
      border-radius:16px;
      padding:16px;
      margin-bottom:14px;
      background:#fff;
    }

    .q-title{
      font-weight:600;
      margin-bottom:10px;
      line-height:1.5;
      font-size:18px;
    }

    .feedback{
      margin-top:10px;
      border:1px solid var(--border);
      border-radius:12px;
      padding:10px;
      background:#fafafa;
      line-height:1.6;
    }

    .report{
      border:1px solid var(--border);
      border-radius:18px;
      padding:20px;
      text-align:center;
      margin:16px 0;
      background:#fff;
    }

    .report .score{
      font-size:34px;
      font-weight:800;
    }

    button[kind="secondary"]{
      background:transparent !important;
      border:none !important;
      padding:0 !important;
      min-height:auto !important;
    }

    .dots{
      font-size:18px;
      color:#9ca3af;
      cursor:pointer;
      text-align:center;
      user-select:none;
    }

    .dots:hover{
      color:#111827;
    }

    @media (max-width: 768px){
      section[data-testid="stSidebar"]{
        width:auto !important;
        min-width:auto !important;
        max-width:none !important;
      }
      .bubble{
        max-width:92%;
      }
      .empty h1{
        font-size:34px;
      }
    }
    </style>
    """, unsafe_allow_html=True)