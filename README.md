# 🎭 SadTalker — AI Talking Head Animation

<p align="center">
  <strong>Generate realistic talking head animations from a single portrait image and audio input using deep learning, with GFPGAN face enhancement.</strong>
</p>

<p align="center">
  ![Python](https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python) ![GitHub](https://img.shields.io/badge/GitHub-rafay--byte-181717?style=for-the-badge&logo=github) ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white) ![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white) ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white) ![Gradio](https://img.shields.io/badge/Gradio-F97316?style=for-the-badge&logo=gradio&logoColor=white)
</p>

---

## 📋 Overview

**SadTalker — AI Talking Head Animation** is a project by [Abdul Rafay Khalid (@rafay-byte)](https://github.com/rafay-byte).

Generate realistic talking head animations from a single portrait image and audio input using deep learning, with GFPGAN face enhancement.

---

## ✨ Features

- 🎭 Single-image talking head animation
- 🎭 Audio-driven facial animation
- 🎭 GFPGAN face enhancement
- 🎭 Web interface with Gradio
- 🎭 Custom avatar creator application

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python |
| **Streamlit** | 🎈 Framework/Library |
| **PyTorch** | 🔥 Framework/Library |
| **TensorFlow** | 🧠 Framework/Library |
| **OpenCV** | 📷 Framework/Library |
| **Gradio** | 🖼️ Framework/Library |
| **Pillow (PIL)** | 🖼️ Framework/Library |
| **Pandas** | 🐼 Framework/Library |
| **NumPy** | 🔢 Framework/Library |


### Key Dependencies
  - `numpy==1.23.4`
  - `face_alignment==1.3.5`
  - `imageio==2.19.3`
  - `imageio-ffmpeg==0.4.7`
  - `librosa==0.9.2 #`
  - `numba`
  - `resampy==0.3.1`
  - `pydub==0.25.1`
  - `scipy==1.10.1`
  - `kornia==0.6.8`
  - `tqdm`
  - `yacs==0.1.8`
  - `pyyaml`
  - `joblib==1.1.0`
  - `scikit-image==0.19.3`

---

## 📁 Project Structure

```
SadTalker/
├── 📄 AI Avatar Creator Application.txt
├── 📄 app_sadtalker.py
├── 📁 checkpoints/
├── 📄 cog.yaml
├── 📁 gfpgan/
├── 📁 image_training_results/
├── 📄 inference.py
├── 📄 launcher.py
├── 📄 predict.py
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 requirements_backup.txt
├── 📁 results/
├── 📁 scripts/
├── 📁 src/
├── 📁 temp_uploads/
├── 📁 TEST-UI/
└── 📄 test.py
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (or relevant runtime)
- **pip** package manager
- **Git** for version control

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rafay-byte/SadTalker.git
   cd SadTalker
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux/Mac
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

Refer to the project structure above and run the main script:
```bash
python app.py    # or the main entry point
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is provided as-is for educational and development purposes.

---

## 👤 Author

**Abdul Rafay Khalid**

- GitHub: [@rafay-byte](https://github.com/rafay-byte)
- BS AI Student @ PAF-IAST

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/rafay-byte">Abdul Rafay Khalid</a>
</p>
