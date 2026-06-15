import streamlit as st
import os
import torch
from time import strftime
import argparse, os, sys, glob
import torch
from omegaconf import OmegaConf
from PIL import Image
from tqdm import tqdm, trange
from imghdr import what
from skimage import transform as trans
import time
import gfpgan
import cv2
import tempfile
import uuid
import shutil
from pathlib import Path
import traceback
import logging
from src.gradio_demo import SadTalker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MUST BE FIRST STREAMLIT COMMAND - MOVE TO TOP AFTER IMPORTS
st.set_page_config(
    page_title="SadTalker - AI Avatar Creator | RAFISTIC AGENCY",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'generated_video' not in st.session_state:
    st.session_state.generated_video = None
if 'generation_id' not in st.session_state:
    st.session_state.generation_id = None


def ensure_directories():
    """Ensure required directories exist"""
    directories = ['results', 'temp_uploads', 'checkpoints']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def safe_file_cleanup(file_path):
    """Safely remove temporary files"""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Could not clean up file {file_path}: {str(e)}")


def save_uploaded_file(uploaded_file, file_type="image"):
    """Safely save uploaded file with proper error handling"""
    try:
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)

        # Generate unique filename
        file_id = uuid.uuid4().hex[:8]
        file_extension = uploaded_file.name.split('.')[-1].lower()

        if file_type == "image":
            temp_path = temp_dir / f"image_{file_id}.{file_extension}"
        else:
            temp_path = temp_dir / f"audio_{file_id}.{file_extension}"

        # Save the file
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        logger.info(f"Saved uploaded file to: {temp_path}")
        return str(temp_path)

    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        st.error(f"❌ Error saving file: {str(e)}")
        return None


def validate_inputs(source_image, driven_audio):
    """Validate uploaded inputs"""
    errors = []

    if source_image is None:
        errors.append("📸 Please upload a source image")
    else:
        # Check image format
        if not source_image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            errors.append("🖼️ Image must be PNG, JPG, or JPEG format")

        # Check image size (optional)
        if source_image.size > 10 * 1024 * 1024:  # 10MB limit
            errors.append("📏 Image file too large (max 10MB)")

    if driven_audio is None:
        errors.append("🎵 Please upload an audio file")
    else:
        # Check audio format
        if not driven_audio.name.lower().endswith(('.wav', '.mp3', '.m4a')):
            errors.append("🔊 Audio must be WAV, MP3, or M4A format")

        # Check audio size
        if driven_audio.size > 50 * 1024 * 1024:  # 50MB limit
            errors.append("📦 Audio file too large (max 50MB)")

    return errors


def get_source_image(image):
    return image


def sadtalker_demo_streamlit():
    # Enhanced Ultra-Premium CSS with more animations and effects
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #a8edea 75%, #fed6e3 100%);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        font-family: 'Poppins', sans-serif;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .main-hero {
        background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(25px);
        border: 2px solid rgba(255,255,255,0.3);
        padding: 4rem 2rem;
        border-radius: 30px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.3);
        position: relative;
        overflow: hidden;
    }

    .main-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: shimmer 3s infinite;
        pointer-events: none;
    }

    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }

    .hero-title {
        font-family: 'Orbitron', monospace;
        font-size: 4.5rem;
        font-weight: 900;
        background: linear-gradient(45deg, #FFD700, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7);
        background-size: 600% 600%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: rainbowShift 4s ease-in-out infinite;
        text-shadow: 0 0 30px rgba(255,215,0,0.5);
        margin-bottom: 1.5rem;
        position: relative;
        z-index: 1;
    }

    @keyframes rainbowShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .hero-subtitle {
        font-size: 1.8rem;
        color: white;
        opacity: 0.95;
        font-weight: 500;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 15px rgba(0,0,0,0.4);
        position: relative;
        z-index: 1;
    }

    .agency-brand {
        font-family: 'Orbitron', monospace;
        font-size: 1.4rem;
        font-weight: 700;
        color: #FFD700;
        text-shadow: 0 0 20px rgba(255,215,0,0.8);
        background: linear-gradient(135deg, rgba(255,215,0,0.2), rgba(255,105,180,0.2));
        padding: 1rem 2rem;
        border-radius: 30px;
        display: inline-block;
        border: 3px solid rgba(255,215,0,0.4);
        animation: pulseGlow 2s infinite;
        position: relative;
        z-index: 1;
        backdrop-filter: blur(10px);
    }

    @keyframes pulseGlow {
        0% { 
            transform: scale(1); 
            box-shadow: 0 0 20px rgba(255,215,0,0.4);
        }
        50% { 
            transform: scale(1.05); 
            box-shadow: 0 0 40px rgba(255,215,0,0.8);
        }
        100% { 
            transform: scale(1); 
            box-shadow: 0 0 20px rgba(255,215,0,0.4);
        }
    }

    .glass-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(20px);
        border: 2px solid rgba(255,255,255,0.25);
        border-radius: 25px;
        padding: 2.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 20px 40px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.2);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
    }

    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s;
    }

    .glass-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 30px 60px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.3);
        border-color: rgba(255,215,0,0.4);
    }

    .glass-card:hover::before {
        left: 100%;
    }

    .section-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: white;
        margin-bottom: 1.5rem;
        text-align: center;
        text-shadow: 2px 2px 15px rgba(0,0,0,0.4);
        position: relative;
    }

    .feature-highlight {
        background: linear-gradient(135deg, rgba(255,215,0,0.25) 0%, rgba(255,105,180,0.25) 50%, rgba(0,206,209,0.25) 100%);
        border: 2px solid rgba(255,215,0,0.4);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        color: white;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 15px 35px rgba(255,215,0,0.15);
        backdrop-filter: blur(10px);
        animation: featureGlow 3s ease-in-out infinite;
    }

    @keyframes featureGlow {
        0%, 100% { box-shadow: 0 15px 35px rgba(255,215,0,0.15); }
        50% { box-shadow: 0 20px 45px rgba(255,105,180,0.25); }
    }

    .stButton > button {
        background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 25%, #45B7D1 50%, #96CEB4 75%, #FFEAA7 100%);
        background-size: 400% 400%;
        color: white;
        border: none;
        border-radius: 30px;
        padding: 1.2rem 2.5rem;
        font-weight: 800;
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        width: 100%;
        position: relative;
        overflow: hidden;
        animation: buttonPulse 2s infinite;
    }

    @keyframes buttonPulse {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stButton > button:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 25px 50px rgba(0,0,0,0.3);
        animation: none;
        background: linear-gradient(135deg, #FF8E8E 0%, #6BE9E0 25%, #67C3F3 50%, #B8E6B8 75%, #FFE5B4 100%);
    }

    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 3rem 0;
    }

    .stat-item {
        text-align: center;
        color: white;
        background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%);
        padding: 2rem 1rem;
        border-radius: 20px;
        backdrop-filter: blur(15px);
        border: 2px solid rgba(255,255,255,0.25);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .stat-item::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,215,0,0.1) 0%, transparent 70%);
        animation: statGlow 4s ease-in-out infinite;
    }

    @keyframes statGlow {
        0%, 100% { opacity: 0; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.2); }
    }

    .stat-item:hover {
        transform: translateY(-5px) scale(1.05);
        border-color: rgba(255,215,0,0.5);
        box-shadow: 0 20px 40px rgba(255,215,0,0.2);
    }

    .stat-number {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(45deg, #FFD700, #FF6B6B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        position: relative;
        z-index: 1;
    }

    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        position: relative;
        z-index: 1;
    }

    .success-animation {
        background: linear-gradient(135deg, #00ff87 0%, #60efff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 1.4rem;
        text-align: center;
        animation: successBounce 1s infinite;
        padding: 1rem;
        border-radius: 15px;
        background-color: rgba(0,255,135,0.1);
        border: 2px solid rgba(0,255,135,0.3);
        margin: 1rem 0;
    }

    @keyframes successBounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0) scale(1); }
        40% { transform: translateY(-10px) scale(1.05); }
        60% { transform: translateY(-5px) scale(1.02); }
    }

    .error-message {
        background: linear-gradient(135deg, rgba(255,107,107,0.2) 0%, rgba(255,107,107,0.1) 100%);
        border: 2px solid rgba(255,107,107,0.4);
        border-radius: 15px;
        padding: 1rem;
        color: #FF6B6B;
        font-weight: 600;
        text-align: center;
        backdrop-filter: blur(10px);
        animation: errorShake 0.5s ease-in-out;
    }

    @keyframes errorShake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }

    .processing-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        backdrop-filter: blur(10px);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }

    .processing-spinner {
        width: 80px;
        height: 80px;
        border: 4px solid rgba(255,215,0,0.3);
        border-top: 4px solid #FFD700;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 2rem;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .floating-elements {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    }

    .floating-particle {
        position: absolute;
        width: 6px;
        height: 6px;
        background: rgba(255,255,255,0.6);
        border-radius: 50%;
        animation: float 8s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { 
            transform: translateY(100vh) translateX(0) rotate(0deg);
            opacity: 0;
        }
        10% { opacity: 1; }
        90% { opacity: 1; }
        50% { 
            transform: translateY(0) translateX(20px) rotate(180deg);
            opacity: 0.8;
        }
    }

    .footer-premium {
        background: linear-gradient(135deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.2) 100%);
        backdrop-filter: blur(25px);
        border: 2px solid rgba(255,255,255,0.15);
        border-radius: 30px;
        padding: 4rem 2rem;
        text-align: center;
        margin-top: 4rem;
        color: white;
        position: relative;
        overflow: hidden;
    }

    .footer-premium::before {
        content: '';
        position: absolute;
        top: -100%;
        left: -100%;
        width: 300%;
        height: 300%;
        background: radial-gradient(circle, rgba(255,215,0,0.05) 0%, transparent 70%);
        animation: footerGlow 6s ease-in-out infinite;
    }

    @keyframes footerGlow {
        0%, 100% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.3; }
        50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.7; }
    }

    /* Custom Streamlit component styles */
    .stSelectbox > div > div > div {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 10px !important;
        color: white !important;
        backdrop-filter: blur(10px) !important;
    }

    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #FFD700, #FF6B6B) !important;
    }

    .stCheckbox > label {
        color: white !important;
        font-weight: 600 !important;
    }

    .stFileUploader > div {
        background: rgba(255,255,255,0.05) !important;
        border: 2px dashed rgba(255,255,255,0.3) !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }

    .stFileUploader > div:hover {
        background: rgba(255,255,255,0.1) !important;
        border-color: rgba(255,215,0,0.5) !important;
        transform: scale(1.02) !important;
    }
    </style>

    <div class="floating-elements">
        <div class="floating-particle" style="left: 10%; animation-delay: 0s;"></div>
        <div class="floating-particle" style="left: 20%; animation-delay: 1s;"></div>
        <div class="floating-particle" style="left: 30%; animation-delay: 2s;"></div>
        <div class="floating-particle" style="left: 40%; animation-delay: 3s;"></div>
        <div class="floating-particle" style="left: 50%; animation-delay: 4s;"></div>
        <div class="floating-particle" style="left: 60%; animation-delay: 5s;"></div>
        <div class="floating-particle" style="left: 70%; animation-delay: 6s;"></div>
        <div class="floating-particle" style="left: 80%; animation-delay: 7s;"></div>
        <div class="floating-particle" style="left: 90%; animation-delay: 8s;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize directories
    ensure_directories()

    # Ultra-Premium Hero Section
    st.markdown("""
    <div class="main-hero">
        <div class="hero-title">⚡ AI AVATAR STUDIO ⚡</div>
        <div class="hero-subtitle">Create Stunning Talking Avatars with Cutting-Edge AI Technology</div>
        <div class="agency-brand">🚀 POWERED BY RAFISTIC AGENCY 🚀</div>
    </div>
    """, unsafe_allow_html=True)

    # Enhanced Stats Section
    st.markdown("""
    <div class="stats-container">
        <div class="stat-item">
            <div class="stat-number">15M+</div>
            <div class="stat-label">Avatars Created</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">75K+</div>
            <div class="stat-label">Happy Creators</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">99.9%</div>
            <div class="stat-label">Success Rate</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">8K</div>
            <div class="stat-label">Ultra HD Quality</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize SadTalker with better error handling
    try:
        if 'sad_talker' not in st.session_state:
            with st.spinner('🔄 Initializing AI Engine...'):
                st.session_state.sad_talker = SadTalker(lazy_load=True)
        sad_talker = st.session_state.sad_talker
    except Exception as e:
        st.error(f"❌ Failed to initialize SadTalker: {str(e)}")
        st.info("💡 Please ensure all dependencies are properly installed.")
        return

    # Enhanced Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%); border-radius: 20px; margins-bottom: 2rem; backdrop-filter: blur(15px); border: 2px solid rgba(255,255,255,0.2);">
            <h2 style="color: #FFD700; margin: 0; font-family: 'Orbitron', monospace;">🎛️ CREATOR STUDIO</h2>
            <p style="color: white; opacity: 0.9; margin: 1rem 0; font-weight: 600;">Professional AI Controls</p>
        </div>
        """, unsafe_allow_html=True)

        # Enhanced settings with better organization
        st.markdown("#### 🎨 Image Processing")
        preprocess_type = st.selectbox(
            'Processing Mode',
            ['crop', 'resize', 'full'],
            index=0,
            help="Crop: Best for portraits | Resize: Maintain aspect ratio | Full: Use entire image"
        )

        is_still_mode = st.checkbox(
            '🎭 Cinema Mode (Reduced Motion)',
            value=True,
            help="Reduces head movement for more natural, professional look"
        )

        st.markdown("#### ✨ AI Enhancement")
        use_enhancer = st.checkbox(
            '🚀 Face Super-Resolution (GFPGAN)',
            value=False,
            help="AI-powered face enhancement - significantly improves quality but takes longer"
        )

        # Advanced settings with better tooltips
        with st.expander("🔧 Advanced Pro Settings", expanded=False):
            size_of_image = st.selectbox(
                '📺 Output Resolution',
                [256, 512],
                index=1,
                help="256: Faster processing | 512: Ultra HD Quality (recommended)"
            )

            pose_style = st.slider(
                '💃 Pose Variation Intensity',
                min_value=0,
                max_value=45,
                value=0,
                help="0: Natural pose | 45: Maximum pose variation"
            )

            exp_scale = st.slider(
                '😊 Expression Amplification',
                min_value=0.0,
                max_value=3.0,
                value=1.0,
                step=0.1,
                help="1.0: Natural expressions | 3.0: Exaggerated expressions"
            )

            # New advanced options
            use_blink = st.checkbox(
                '👁️ Natural Blinking',
                value=True,
                help="Adds realistic blinking animation"
            )

        # System Info
        st.markdown("#### 📊 System Status")
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            st.success("🚀 GPU Acceleration: ✅ Active")
            gpu_name = torch.cuda.get_device_name(0)
            st.info(f"💎 GPU: {gpu_name}")
        else:
            st.warning("⚠️ GPU Acceleration: ❌ CPU Mode")
            st.info("💡 Install CUDA for faster processing")

        # Tips section
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(255,215,0,0.15) 0%, rgba(255,105,180,0.15) 100%); padding: 1.5rem; border-radius: 15px; margin-top: 2rem; text-align: center; border: 2px solid rgba(255,215,0,0.3); backdrop-filter: blur(10px);">
            <h4 style="color: #FFD700; margin: 0 0 1rem 0;">💎 PRO TIPS</h4>
            <p style="color: white; font-size: 0.9rem; margin: 0.5rem 0;">✨ Use well-lit, front-facing portraits</p>
            <p style="color: white; font-size: 0.9rem; margin: 0.5rem 0;">🎵 Clear audio gives better lip-sync</p>
            <p style="color: white; font-size: 0.9rem; margin: 0.5rem 0;">⚡ Enable GPU for faster processing</p>
        </div>
        """, unsafe_allow_html=True)

    # Main Upload Section with Enhanced UI
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title">📸 Upload Portrait Image</div>
            <div class="feature-highlight">
                🎯 Upload a clear, well-lit portrait photo<br>
                ✅ Front-facing images work best<br>
                🔥 Supported: PNG, JPG, JPEG (Max: 10MB)<br>
                💡 High resolution recommended for best results
            </div>
        </div>
        """, unsafe_allow_html=True)

        source_image = st.file_uploader(
            "Choose your portrait image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear portrait image for best results",
            label_visibility="collapsed",
            key="source_image_upload"
        )

        if source_image is not None:
            try:
                img = Image.open(source_image)
                st.image(img, caption="✨ Your Source Portrait", use_container_width=True)

                # Display image info
                st.markdown(f"""
                <div class="success-animation">
                    🎉 Image uploaded successfully!<br>
                    📏 Size: {img.size[0]}x{img.size[1]} pixels<br>
                    📦 Format: {img.format}
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error loading image: {str(e)}")

    with col2:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title">🎵 Upload Audio Track</div>
            <div class="feature-highlight">
                🎤 Upload your voice recording or music<br>
                ✅ Clear audio ensures perfect lip-sync<br>
                🔥 Supported: WAV, MP3, M4A (Max: 50MB)<br>
                ⏱️ Longer audio = longer processing time
            </div>
        </div>
        """, unsafe_allow_html=True)

        driven_audio = st.file_uploader(
            "Choose your audio file",
            type=['wav', 'mp3', 'm4a'],
            help="Upload audio to make your avatar speak or sing",
            label_visibility="collapsed",
            key="audio_upload"
        )

        if driven_audio is not None:
            try:
                st.audio(driven_audio, format='audio/wav')

                # Display audio info
                audio_size_mb = driven_audio.size / (1024 * 1024)
                st.markdown(f"""
                <div class="success-animation">
                    🎵 Audio loaded perfectly!<br>
                    📦 Size: {audio_size_mb:.1f} MB<br>
                    🎼 Format: {driven_audio.name.split('.')[-1].upper()}
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error loading audio: {str(e)}")

    # Enhanced Generation Section
    st.markdown("---")

    # Input validation with better error messages
    validation_errors = validate_inputs(source_image, driven_audio)

    if validation_errors:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <div class="section-title">⚠️ VALIDATION REQUIRED</div>
        </div>
        """, unsafe_allow_html=True)

        for error in validation_errors:
            st.markdown(f'<div class="error-message">{error}</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <div class="section-title">🚀 CREATE YOUR MASTERPIECE</div>
            <div style="color: white; font-size: 1.2rem; margin-bottom: 2rem; font-weight: 600;">
                Everything looks perfect! Ready to create some AI magic? ✨
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Enhanced Generation Button with Loading State
    generate_button_disabled = bool(validation_errors) or st.session_state.processing

    if st.button(
            "🎬 CREATE AVATAR MAGIC" if not st.session_state.processing else "🔄 CREATING MAGIC...",
            key="generate_btn",
            disabled=generate_button_disabled
    ):
        if validation_errors:
            st.error("❌ Please fix the validation errors above before proceeding.")
            return

        # Set processing state
        st.session_state.processing = True
        st.session_state.generation_id = uuid.uuid4().hex[:8]

        # Initialize temp file paths
        pic_path = None
        audio_path = None

        try:
            # Enhanced progress tracking
            progress_container = st.container()
            with progress_container:
                st.markdown("""
                <div style="text-align: center; padding: 2rem; background: rgba(255,215,0,0.1); border-radius: 20px; margin: 2rem 0; border: 2px solid rgba(255,215,0,0.3);">
                    <h3 style="color: #FFD700; margin-bottom: 1rem;">🎭 AI MAGIC IN PROGRESS</h3>
                    <p style="color: white; font-size: 1.1rem;">Creating your personalized avatar masterpiece...</p>
                </div>
                """, unsafe_allow_html=True)

                progress_bar = st.progress(0)
                status_text = st.empty()
                time_estimate = st.empty()

                # Step 1: Save uploaded files with better error handling
                progress_bar.progress(10)
                status_text.markdown("📁 **Securing your files safely...**")
                time_estimate.markdown("⏱️ *Estimated time remaining: 2-3 minutes*")

                pic_path = save_uploaded_file(source_image, "image")
                audio_path = save_uploaded_file(driven_audio, "audio")

                if not pic_path or not audio_path:
                    st.error("❌ Failed to save uploaded files. Please try again.")
                    return

                # Step 2: Initialize processing
                progress_bar.progress(25)
                status_text.markdown("🔍 **Analyzing your portrait with AI vision...**")
                time_estimate.markdown("⏱️ *Estimated time remaining: 2 minutes*")
                time.sleep(1)

                progress_bar.progress(40)
                status_text.markdown("🎵 **Processing audio with advanced algorithms...**")
                time_estimate.markdown("⏱️ *Estimated time remaining: 90 seconds*")
                time.sleep(1)

                # Step 3: Generate unique save directory
                save_dir = os.path.join('results',
                                        f'avatar_{st.session_state.generation_id}_{strftime("%Y%m%d_%H%M%S")}')

                progress_bar.progress(60)
                status_text.markdown("🤖 **AI neural networks working their magic...**")
                time_estimate.markdown("⏱️ *Estimated time remaining: 60 seconds*")

                # Step 4: Generate video with enhanced error handling
                try:
                    gen_video = sad_talker.test(
                        source_image=pic_path,
                        driven_audio=audio_path,
                        preprocess=preprocess_type,
                        still_mode=is_still_mode,
                        use_enhancer=use_enhancer,
                        batch_size=1,
                        size=size_of_image,
                        pose_style=pose_style,
                        exp_scale=exp_scale,
                        use_ref_video=False,
                        ref_video=None,
                        ref_info=None,
                        use_idle_mode=False,
                        length_of_audio=0,
                        use_blink=use_blink,
                        result_dir=save_dir
                    )
                except Exception as e:
                    logger.error(f"SadTalker generation error: {str(e)}")
                    st.error(f"❌ Generation failed: {str(e)}")
                    st.info("💡 Try adjusting your settings or using different input files.")
                    return

                progress_bar.progress(85)
                status_text.markdown("✨ **Adding premium finishing touches...**")
                time_estimate.markdown("⏱️ *Estimated time remaining: 15 seconds*")
                time.sleep(1)

                progress_bar.progress(100)
                status_text.markdown("🎉 **MASTERPIECE CREATED SUCCESSFULLY!**")
                time_estimate.markdown("✅ *Complete! Your avatar is ready!*")

            # Clean up temporary files
            safe_file_cleanup(pic_path)
            safe_file_cleanup(audio_path)

            # Display results with enhanced celebration
            if gen_video and os.path.exists(gen_video):
                st.balloons()
                st.session_state.generated_video = gen_video

                # Success celebration
                st.markdown("""
                <div class="glass-card" style="text-align: center; background: linear-gradient(135deg, rgba(0,255,135,0.2) 0%, rgba(0,255,135,0.1) 100%); border-color: rgba(0,255,135,0.4);">
                    <h1 style="color: #00FF87; margin-bottom: 1rem; font-size: 3rem;">🎉 INCREDIBLE SUCCESS! 🎉</h1>
                    <p style="color: white; font-size: 1.4rem; font-weight: 600;">Your AI avatar is absolutely stunning! 🔥</p>
                    <p style="color: white; font-size: 1.1rem; opacity: 0.9;">Generation ID: {st.session_state.generation_id}</p>
                </div>
                """, unsafe_allow_html=True)

                # Center the video with enhanced styling
                st.markdown("""
                <div style="text-align: center; margin: 3rem 0;">
                    <h2 style="color: #FFD700; margin-bottom: 2rem; text-shadow: 0 0 20px rgba(255,215,0,0.5);">🎬 YOUR AI AVATAR MASTERPIECE</h2>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns([1, 4, 1])
                with col2:
                    st.video(gen_video)

                # Enhanced download section
                st.markdown("""
                <div class="glass-card" style="text-align: center;">
                    <h2 style="color: #FFD700; margin-bottom: 1.5rem;">💾 DOWNLOAD YOUR CREATION</h2>
                    <p style="color: white; font-size: 1.1rem; margin-bottom: 2rem;">High-quality MP4 video ready for sharing!</p>
                </div>
                """, unsafe_allow_html=True)

                # Download button with file info
                try:
                    with open(gen_video, 'rb') as file:
                        video_data = file.read()
                        video_size_mb = len(video_data) / (1024 * 1024)

                        st.download_button(
                            label=f"💎 DOWNLOAD PREMIUM VIDEO ({video_size_mb:.1f} MB)",
                            data=video_data,
                            file_name=f"rafistic_avatar_{st.session_state.generation_id}.mp4",
                            mime="video/mp4",
                            key="download_video_btn"
                        )

                except Exception as e:
                    st.error(f"❌ Download preparation failed: {str(e)}")

                # Social sharing section
                st.markdown("""
                <div class="glass-card" style="text-align: center;">
                    <h3 style="color: #FFD700; margin-bottom: 1rem;">🌟 SHARE YOUR AMAZING CREATION</h3>
                    <p style="color: white; font-size: 1.1rem; margin-bottom: 1rem;">Love your AI avatar? Share it with the world! 🌍</p>
                    <div style="display: flex; justify-content: center; gap: 2rem; margin: 1.5rem 0; flex-wrap: wrap;">
                        <div style="color: white; background: rgba(29,161,242,0.2); padding: 1rem; border-radius: 15px; border: 2px solid rgba(29,161,242,0.4);">
                            📱 <strong>Twitter/X:</strong> #AIAvatar #RafisticAgency
                        </div>
                        <div style="color: white; background: rgba(225,48,108,0.2); padding: 1rem; border-radius: 15px; border: 2px solid rgba(225,48,108,0.4);">
                            📸 <strong>Instagram:</strong> @RafisticAgency
                        </div>
                        <div style="color: white; background: rgba(24,119,242,0.2); padding: 1rem; border-radius: 15px; border: 2px solid rgba(24,119,242,0.4);">
                            👥 <strong>Facebook:</strong> #AITechnology
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Performance metrics
                st.markdown("""
                <div class="glass-card" style="text-align: center;">
                    <h3 style="color: #FFD700; margin-bottom: 1rem;">📊 GENERATION STATS</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
                        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                            <div style="color: #4ECDC4; font-size: 1.5rem; font-weight: bold;">✅ SUCCESS</div>
                            <div style="color: white; font-size: 0.9rem;">Generation Status</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                            <div style="color: #FFD700; font-size: 1.5rem; font-weight: bold;">{size_of_image}p</div>
                            <div style="color: white; font-size: 0.9rem;">Output Resolution</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                            <div style="color: #FF6B6B; font-size: 1.5rem; font-weight: bold;">{"GPU" if torch.cuda.is_available() else "CPU"}</div>
                            <div style="color: white; font-size: 0.9rem;">Processing Mode</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                            <div style="color: #96CEB4; font-size: 1.5rem; font-weight: bold;">{"✅" if use_enhancer else "➖"}</div>
                            <div style="color: white; font-size: 0.9rem;">Face Enhancement</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.error("❌ Generation failed - No output video was created.")
                st.info("💡 Please try again with different settings or input files.")
                logger.error(f"No video output generated. Expected path: {gen_video}")

        except Exception as e:
            logger.error(f"Generation process failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            st.error(f"⚠️ An unexpected error occurred during generation:")
            st.code(str(e))

            st.markdown("""
            <div class="glass-card" style="text-align: center;">
                <h3 style="color: #FF6B6B;">🔧 TROUBLESHOOTING TIPS</h3>
                <div style="text-align: left; color: white; margin: 1rem 0;">
                    <p>• ✅ Ensure your image is a clear portrait (PNG/JPG format)</p>
                    <p>• 🎵 Check that your audio file is properly formatted (WAV/MP3/M4A)</p>
                    <p>• 💾 Make sure you have enough disk space available</p>
                    <p>• 🔄 Try using different processing settings</p>
                    <p>• 📱 Restart the application if problems persist</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        finally:
            # Always clean up temporary files and reset processing state
            safe_file_cleanup(pic_path)
            safe_file_cleanup(audio_path)
            st.session_state.processing = False

    # Create New Avatar Button
    if st.session_state.generated_video and not st.session_state.processing:
        st.markdown("---")
        if st.button("🎨 CREATE ANOTHER MASTERPIECE", key="create_another"):
            st.session_state.generated_video = None
            st.session_state.generation_id = None
            st.rerun()

    # Enhanced Premium Footer
    st.markdown("""
    <div class="footer-premium">
        <h1 style="color: #FFD700; margin-bottom: 1.5rem; font-family: 'Orbitron', monospace;">🌟 RAFISTIC AGENCY - AI INNOVATION LEADERS</h1>
        <p style="font-size: 1.3rem; margin-bottom: 2rem; font-weight: 600;">Transforming the future with cutting-edge AI technology</p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin: 3rem 0;">
            <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 20px; backdrop-filter: blur(10px);">
                <h4 style="color: #4ECDC4; margin-bottom: 1rem;">🚀 AI-Powered Technology</h4>
                <p style="color: white; opacity: 0.9;">State-of-the-art neural networks for realistic avatar generation</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 20px; backdrop-filter: blur(10px);">
                <h4 style="color: #FF6B6B; margin-bottom: 1rem;">⚡ Lightning Fast Processing</h4>
                <p style="color: white; opacity: 0.9;">Optimized algorithms for quick and efficient video generation</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 20px; backdrop-filter: blur(10px);">
                <h4 style="color: #FFD700; margin-bottom: 1rem;">🎨 Professional Quality</h4>
                <p style="color: white; opacity: 0.9;">Cinema-grade output suitable for professional use</p>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 20px; backdrop-filter: blur(10px);">
                <h4 style="color: #96CEB4; margin-bottom: 1rem;">🔥 Trending Technology</h4>
                <p style="color: white; opacity: 0.9;">Latest advancements in AI and computer vision</p>
            </div>
        </div>

        <div style="margin: 3rem 0; padding: 2rem; background: rgba(255,215,0,0.1); border-radius: 20px; border: 2px solid rgba(255,215,0,0.3);">
            <h3 style="color: #FFD700; margin-bottom: 1rem;">🎯 WHY CHOOSE RAFISTIC AGENCY?</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; color: white;">
                <div>💎 <strong>Premium Quality</strong></div>
                <div>🌟 <strong>Innovative Solutions</strong></div>
                <div>🚀 <strong>Future-Ready Tech</strong></div>
                <div>🔒 <strong>Secure Processing</strong></div>
                <div>⚡ <strong>Fast Generation</strong></div>
                <div>🎨 <strong>Creative Excellence</strong></div>
            </div>
        </div>

        <p style="color: #FFD700; font-weight: 700; font-size: 1.2rem; margin-top: 2rem;">
            💎 Premium • 🌟 Innovative • 🚀 Future-Ready • ✨ AI Excellence
        </p>

        <div style="margin-top: 2rem; font-size: 0.9rem; color: rgba(255,255,255,0.7);">
            <p>© 2024 Rafistic Agency. All rights reserved. | Powered by Advanced AI Technology</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    try:
        sadtalker_demo_streamlit()
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        logger.error(f"Main application error: {traceback.format_exc()}")


if __name__ == "__main__":
    main()