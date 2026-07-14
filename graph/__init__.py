# graph package

# Tự nạp .env (nếu có python-dotenv) để mọi entry point (test scripts, langgraph up)
# đều đọc được NVIDIA_API_KEY, BA_USE_AGENT... mà không cần set env trong shell trước.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass