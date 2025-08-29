import streamlit as st

# Minimal test app to debug 403 issues
st.set_page_config(
    page_title="AI Study Assistant - Test",
    page_icon="📚",
    layout="wide"
)

st.title("🧪 AI Study Assistant - Connection Test")

st.success("✅ Streamlit app is running successfully!")

st.markdown("""
## 🔧 Debugging Information

### Connection Status
- **Server**: Running on localhost:8501
- **Status**: ✅ Connected successfully
- **Time**: Real-time connection established

### Quick Test
If you can see this page, the 403 error has been resolved!

### Next Steps
1. ✅ Basic connectivity works
2. 🔄 Ready to load full app
3. 🚀 Continue with AI Study Assistant

---

**🎯 Test successful! Your AI Study Assistant is ready.**
""")

# Add some interactive elements to test functionality
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎯 Test Button"):
        st.balloons()
        st.success("Button works perfectly!")

with col2:
    test_input = st.text_input("Test Input", placeholder="Type something...")
    if test_input:
        st.info(f"You typed: {test_input}")

with col3:
    st.metric("Status", "Working ✅", "100%")

# Test file upload
uploaded_file = st.file_uploader("Test File Upload", type=['txt', 'pdf'], help="This tests file upload functionality")
if uploaded_file:
    st.success(f"✅ File upload works! Uploaded: {uploaded_file.name}")

st.markdown("---")
st.markdown("🚀 **Ready to launch full AI Study Assistant!**")
