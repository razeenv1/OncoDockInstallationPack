import sys
import json
import time
import os
import tempfile
import subprocess
import requests
import ctypes
from ctypes import wintypes
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QFormLayout,QLabel, QLineEdit, QPushButton, QTextEdit,
    QFileDialog,QMessageBox, QHBoxLayout,
    QSplitter, QComboBox,QCheckBox,QTabWidget,QSizePolicy,
    QDialog,QStackedWidget,QFrame,QProgressBar,
    QGroupBox,QDialogButtonBox,
    QSpacerItem,QSpinBox,QSlider)

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QCoreApplication,
    QTimer,QRect, pyqtProperty,QPropertyAnimation,
    QSettings,QSize,QObject,pyqtSlot,QUrl,
    QLoggingCategory,QPoint,QRectF,QTranslator,
    QEvent)

from PyQt6.QtGui import (QPainter, QColor, QIcon,QPixmap,
                         QTextCursor, QPen,
                         QPainterPath, QRegion,QMouseEvent)
from PIL import Image

import cv2
import imutils
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input # type: ignore

import numpy as np
import tensorflow as tf
# ==========================================================
# STYLING AND HTML TEMPLATE (From Viewer)
# ==========================================================

DARK_STYLE = """
QWidget { background-color: #1E1E1E; color: #EAEAEA; font-family: 'Segoe UI', sans-serif; font-size: 14px; border: none; }
QMainWindow { background-color: #1E1E1E; }
QLineEdit { background-color: #2A2A2A; border: 1px solid #3A3A3A; border-radius: 6px; padding: 6px 8px; selection-background-color: #0078D7; selection-color: #fff; }
QPushButton { background-color: #2D2D2D; border: 1px solid #3C3C3C; border-radius: 6px; padding: 6px 12px; color: #EAEAEA; }
QPushButton:hover { background-color: #3A3A3A; }
QPushButton:pressed { background-color: #0078D7; border: 1px solid #0078D7; color: white; }
QLabel { color: #EAEAEA; font-size: 14px; }
QComboBox { background-color: #2A2A2A; border: 1px solid #3A3A3A; border-radius: 6px; padding: 6px 8px; }
QComboBox::drop-down { border: none; }
QTextEdit { background-color: #1C1C1C; border: 1px solid #333; border-radius: 6px; font-family: 'Consolas', monospace; font-size: 13px; }
QSplitter::handle { background-color: #333; }
QSplitter::handle:hover { background-color: #444; }
QTabWidget::pane { border: 1px solid #333; border-radius: 6px; margin: 2px; }
QTabBar::tab { background-color: #1E1E1E; border: 1px solid #333; padding: 6px 14px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:hover { background-color: #2D2D2D; }
QTabBar::tab:selected { background-color: #0078D7; color: white; }
"""

LIGHT_STYLE = """
QWidget { background-color: #FAFAFA; color: #2A2A2A; font-family: 'Segoe UI', sans-serif; font-size: 14px; border: none; }
QMainWindow { background-color: #FAFAFA; }
QLineEdit { background-color: #FFFFFF; border: 1px solid #CCC; border-radius: 6px; padding: 6px 8px; selection-background-color: #0078D7; selection-color: white; }
QPushButton { background-color: #F2F2F2; border: 1px solid #CCC; border-radius: 6px; padding: 6px 12px; color: #2A2A2A; }
QPushButton:hover { background-color: #E6E6E6; }
QPushButton:pressed { background-color: #0078D7; border: 1px solid #0078D7; color: white; }
QLabel { color: #2A2A2A; font-size: 14px; }
QComboBox { background-color: #FFFFFF; border: 1px solid #CCC; border-radius: 6px; padding: 6px 8px; }
QComboBox::drop-down { border: none; }
QTextEdit { background-color: #FFFFFF; border: 1px solid #CCC; border-radius: 6px; font-family: 'Consolas', monospace; font-size: 13px; }
QSplitter::handle { background-color: #CCC; }
QSplitter::handle:hover { background-color: #BBB; }
QTabWidget::pane { border: 1px solid #CCC; border-radius: 6px; margin: 2px; }
QTabBar::tab { background-color: #FAFAFA; border: 1px solid #CCC; padding: 6px 14px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:hover { background-color: #EDEDED; }
QTabBar::tab:selected { background-color: #0078D7; color: white; }
"""

DARK_MODE_ACTIVE_BUTTON_STYLESHEET = "background-color: #0078D7; color: white; border-radius: 6px;"
DARK_MODE_INACTIVE_BUTTON_STYLESHEET = "background-color: #2D2D2D; color: #aaa; border-radius: 6px;"
LIGHT_MODE_ACTIVE_BUTTON_STYLESHEET = "background-color: #0078D7; color: white; border-radius: 6px;"
LIGHT_MODE_INACTIVE_BUTTON_STYLESHEET = "background-color: #F2F2F2; color: #555; border-radius: 6px;"
DARK_STYLE_BC = """
QWidget { background-color: #212121; color: #EAEAEA; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
#titleLabel { background-color: transparent; font-size: 28px; font-weight: bold; color: #EAEAEA; }
#subtitleLabel { background-color: transparent; font-size: 16px; color: #BDBDBD; font-style: italic; margin-bottom: 20px; }
QPushButton { background-color: #337ab7; border: none; border-radius: 8px; padding: 15px 30px; font-size: 16px; font-weight: bold; color: white; }
QPushButton:hover { background-color: #286090; }
QPushButton:pressed { background-color: #1a476f; }
#statusLabel { background-color: transparent; font-size: 14px; color: #8E8E8E; }
#resultLabel { font-size: 22px; font-weight: bold; color: #4CAF50; padding: 10px; border-radius: 8px; background-color: #333333; min-height: 50px; }
#imageFrame { border: 2px dashed #424242; background-color: #303030; border-radius: 12px; }

/* --- Style for the Progress Bar (Dark Mode) --- */
QProgressBar {
    border: 1px solid #4CAF50;
    border-radius: 6px;
    background-color: #2A2A2A; /* Dark background for the trough */
    text-align: center;
    color: #EAEAEA; /* Light text */
}
QProgressBar::chunk {
    background-color: #4CAF50; /* Color of the progress itself */
    border-radius: 6px;
}
"""

LIGHT_STYLE_BC = """
QWidget { background-color: #F0F0F0; color: #333333; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
#titleLabel { background-color: transparent; font-size: 28px; font-weight: bold; color: #333333; }
#subtitleLabel { background-color: transparent; font-size: 16px; color: #555555; font-style: italic; margin-bottom: 20px; }
QPushButton { background-color: #337ab7; border: none; border-radius: 8px; padding: 15px 30px; font-size: 16px; font-weight: bold; color: white; }
QPushButton:hover { background-color: #286090; }
QPushButton:pressed { background-color: #1a476f; }
#statusLabel { background-color: transparent; font-size: 14px; color: #888888; }
#resultLabel { font-size: 22px; font-weight: bold; color: #4CAF50; padding: 10px; border-radius: 8px; background-color: #E0E0E0; min-height: 50px; }
#imageFrame { border: 2px dashed #CCCCCC; background-color: #E0E0E0; border-radius: 12px; }

/* --- Style for the Progress Bar (Light Mode) --- */
QProgressBar {
    border: 1px solid #4CAF50;
    border-radius: 6px;
    background-color: #F0F0F0; /* Light background for the trough */
    text-align: center;
    color: black; /* Dark text */
}
QProgressBar::chunk {
    background-color: #4CAF50; /* Color of the progress itself */
    border-radius: 6px;
}
"""
THEME = True

breast_cancer_model = None
brain_tumor_model = None
lung_cancer_model = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <script src="https://3dmol.org/build/3Dmol.js"></script>
    <style>
      html, body {{ 
        overflow:hidden; 
        height:100%; margin:0; background:{bg_color};
        animation: fadein 0.18s ease-in;
      }}
      @keyframes fadein {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
      #viewer {{ width:100vw; height:100vh; overflow:hidden;}}
    </style>
  </head>
  <body>
    <div id="viewer"></div>
    <script>
      // ---------- Lightweight viewer init ----------
      const element = document.getElementById("viewer");
      let viewer = null;
      let config = {{
        backgroundColor: "{bg_color}",
        antialias: false,
        cartoonQuality: 4,
        disableFog: true
      }};

      try {{
        // Try WebGL first
        viewer = $3Dmol.createViewer(element, config);
      }} catch (e) {{
        console.error("WebGL failed, falling back to Canvas:", e);
        config.renderer = "canvas";
        viewer = $3Dmol.createViewer(element, config);
      }}

      try {{ viewer.setViewStyle({{ fog: false }}); }} catch(e) {{ /* ignore */ }}

      // ---------- state ----------
      let currentModel = null;
      let currentSourceHash = "";
      let renderPending = false;
      let pendingSurfaceTimer = null;

      // ---------- utilities ----------
      function requestRender() {{
        if (renderPending) return;
        renderPending = true;
        requestAnimationFrame(() => {{
          try {{ viewer.render(); }} catch(e) {{ console.warn('render error', e); }}
          renderPending = false;
        }});
      }}

      function hashShort(s) {{
        if (!s) return "";
        let h = 0;
        for (let i = 0; i < Math.min(200, s.length); i++) {{
          h = ((h << 5) - h) + s.charCodeAt(i);
          h |= 0;
        }}
        return h.toString(36);
      }}

      function makeStyle(styleName, colorSpec) {{
        const colorProp = (colorSpec === 'spectrum') ? {{ color: 'spectrum' }} : {{ colorscheme: colorSpec }};
        if (styleName === 'cartoon') {{
          return {{ cartoon: Object.assign({{ thick:0.18, ribbon:true, arrows:false }}, colorProp) }};
        }} else if (styleName === 'stick') {{
          return {{ stick: Object.assign({{ radius:0.10, linewidth:0.5 }}, colorProp) }};
        }} else if (styleName === 'sphere') {{
          return {{ sphere: Object.assign({{ scale:0.22 }}, colorProp) }};
        }} else {{
          return {{ line: Object.assign({{ linewidth:1 }}, colorProp) }};
        }}
      }}

      // ---------- surface scheduling ----------
      function clearPendingSurface() {{
        if (pendingSurfaceTimer) {{
          clearTimeout(pendingSurfaceTimer);
          pendingSurfaceTimer = null;
        }}
      }}

      function scheduleSurface(showSurface, surfaceDelayMs) {{
        clearPendingSurface();
        if (!showSurface) {{
          try {{ viewer.removeAllSurfaces(); }} catch(e) {{/* ignore */}}
          return;
        }}
        pendingSurfaceTimer = setTimeout(() => {{
          try {{
            viewer.removeAllSurfaces();
            viewer.addSurface($3Dmol.SurfaceType.VDW, {{ opacity: 0.6 }}, {{ hetflag: false }});
            requestRender();
          }} catch(e) {{ console.warn('surface error', e); }}
          pendingSurfaceTimer = null;
        }}, surfaceDelayMs || 180);
      }}

      // ---------- load remote PDB ----------
      function loadPDB(pdbcode, styleName, colorSpec, showSurface, options) {{
        if (!pdbcode) return;
        options = options || {{}};
        const surfaceDelayMs = options.surfaceDelayMs || 180;

        if (currentSourceHash === ('pdbid:' + pdbcode) && currentModel) {{
          applySettings(styleName, colorSpec, showSurface);
          return;
        }}

        clearPendingSurface();
        currentModel = null;
        currentSourceHash = '';

        try {{ viewer.removeAllSurfaces(); viewer.removeAllModels(); }} catch(e) {{}}

        $3Dmol.download('bcif:' + pdbcode, viewer, {{}}, function() {{
          try {{
            currentModel = viewer.getModel();
            currentSourceHash = 'pdbid:' + pdbcode;
            viewer.setStyle({{}}, makeStyle(styleName, colorSpec));
            viewer.zoomTo();
            scheduleSurface(showSurface, surfaceDelayMs);
            requestRender();
          }} catch(e) {{
            console.error('model setup error', e);
          }}
        }});
      }}

      // ---------- load raw PDB ----------
      function loadFile(moldataOrUrl, format, styleName, colorSpec, showSurface, options) {{
        options = options || {{}};
        const surfaceDelayMs = options.surfaceDelayMs || 180;
        format = (format || 'pdb').toLowerCase();

        function applyLoadedText(pdbText) {{
          if (!pdbText || pdbText.trim().length === 0) {{ console.warn('Empty pdb text'); return; }}
          const newHash = 'pdbtxt:' + hashShort(pdbText);
          const forceReload = !!options.forceReload;
          const needReload = forceReload || (newHash !== currentSourceHash);

          if (needReload) {{
            clearPendingSurface();
            try {{ viewer.removeAllModels(); viewer.removeAllSurfaces(); }} catch(e){{/*ignore*/}}
            currentModel = viewer.addModel(pdbText, "pdb");
            currentSourceHash = newHash;
            viewer.setStyle({{}}, makeStyle(styleName, colorSpec));
            viewer.zoomTo();
            scheduleSurface(showSurface, surfaceDelayMs);
            requestRender();
          }} else {{
            viewer.setStyle({{}}, makeStyle(styleName, colorSpec));
            scheduleSurface(showSurface, surfaceDelayMs);
            requestRender();
          }}
        }}

        try {{
          if (typeof moldataOrUrl === 'string' && (moldataOrUrl.startsWith('http://') || moldataOrUrl.startsWith('https://') || moldataOrUrl.startsWith('file://'))) {{
            fetch(moldataOrUrl).then(r => r.text()).then(text => applyLoadedText(text)).catch(e => console.error('fetch error', e));
          }} else {{
            applyLoadedText(moldataOrUrl);
          }}
        }} catch(e) {{
          console.error('loadFile error', e);
        }}
      }}
      function loadPDBData(pdbText, styleName, colorSpec, showSurface, options) {{
        loadFile(pdbText, 'pdb', styleName, colorSpec, showSurface, options);
      }}

      function applySettings(styleName, colorSpec, showSurface) {{
        try {{
          if (!currentModel) return;
          viewer.setStyle({{}}, makeStyle(styleName, colorSpec));
          scheduleSurface(showSurface, 120);
          requestRender();
        }} catch(e) {{
          console.error('applySettings error', e);
        }}
      }}

      // expose API
      window._3dmol_api = {{
        loadPDB: loadPDB,
        loadFile: loadFile,
        loadPDBData: loadPDBData,
        applySettings: applySettings
      }};
    </script>
  </body>
</html>
"""

html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-s8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OncoDock | Initializing</title>
    <style>
        :root {
            --primary-color: #6ee7ff;
            --secondary-color: #a78bfa;
            --text-color: #e5e7eb;
            --stage-size: 500px;
        }
        * { box-sizing: border-box; }
        html, body {
            height: 100%; margin: 0; overflow: hidden; font-family: system-ui, sans-serif;
            color: var(--text-color); background-color: #0c0a1b; position: relative; z-index: 0;
        }
        body::before {
            content: ""; position: fixed; inset: 0;
            background: url('https://images.unsplash.com/photo-1576086213369-97a306d36557?crop=entropy&cs=tinysrgb&fit=max&fm=jpg') center/cover no-repeat;
            opacity: 0.25; z-index: -1;
        }
        .stage {
            width: var(--stage-size); height: var(--stage-size); position: relative;
            perspective: 1500px; transform-style: preserve-3d;
            top: 50%; left: 50%; transform: translate(-50%, -50%);
        }
        #viewer3d { position: absolute; inset: 0; z-index: 1; }
        .ring {
            position: absolute; top: 50%; left: 50%; width: 90%; height: 90%;
            margin-left: -45%; margin-top: -45%; border-radius: 50%;
            transform: rotateX(70deg); animation: spin 18s linear infinite; will-change: transform;
            border: 2px solid transparent;
            border-image: conic-gradient(from 90deg, var(--primary-color), transparent 40%, var(--secondary-color)) 1;
        }
        .ring-2 {
            width: 75%; height: 75%; margin-left: -37.5%; margin-top: -37.5%;
            animation-duration: 12s; animation-direction: reverse;
        }
        .title-container {
            position: absolute; bottom: 25%; left: 0; right: 0;
            text-align: center; z-index: 5; pointer-events: none;
        }
        .title {
            font-size: 42px; font-weight: 700; letter-spacing: 3px;
            margin: 0 0 15px 0; text-shadow: 0 0 20px rgba(167, 139, 250, 0.7);
        }
        .subtitle { font-size: 14px; letter-spacing: 2px; text-transform: uppercase; color: #94a3b8; }
        .progress-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-top: 20px;
        }
        .progress-bar {
            width: 250px; height: 4px; background: rgba(110, 231, 255, 0.15);
            border-radius: 2px; overflow: hidden;
        }
        .progress {
            width: 100%; height: 100%;
            background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
            transform-origin: left;
            transform: scaleX(0);
            /* This easing function is now replicated in the JavaScript */
            transition: transform 6s cubic-bezier(0.2, 0.8, 0.2, 1);
        }
        #progress-percentage {
            font-size: 14px;
            font-family: monospace;
            color: #94a3b8;
            min-width: 40px;
            text-align: left;
        }
        .credits {
            position: fixed; bottom: 15px; right: 20px;
            font-size: 12px; color: #94a3b8; opacity: 0.7;
        }
        @keyframes spin {
            from { transform: rotateX(70deg) rotateZ(0deg); }
            to { transform: rotateX(70deg) rotateZ(360deg); }
        }
    </style>
</head>
<body>
    <div class="stage">
        <div id="viewer3d"></div>
        <div class="ring ring-1"></div>
        <div class="ring ring-2"></div>
    </div>
    <div class="title-container">
        <h1 class="title">OncoDock</h1>
        <p class="subtitle">Initializing Interface</p>
        <div class="progress-container">
            <div class="progress-bar"><div class="progress"></div></div>
            <span id="progress-percentage">0%</span>
        </div>
    </div>
    <div class="credits">By Razeen, Arjun, Nilay, Sinan</div>
    <script src="https://unpkg.com/3dmol/build/3dmol-min.js"></script>
    <script>
        // --- Make functions global ---
        window.currentPercentage = 0;
        let animationFrameId = null;

        // Easing function for smooth progress
        function cubicBezier(mX1, mY1, mX2, mY2) {
            function A(aA1, aA2) { return 1.0 - 3.0*aA2 + 3.0*aA1; }
            function B(aA1, aA2) { return 3.0*aA2 - 6.0*aA1; }
            function C(aA1) { return 3.0*aA1; }
            function CalcBezier(aT, aA1, aA2) { return ((A(aA1,aA2)*aT + B(aA1,aA2))*aT + C(aA1))*aT; }
            function GetSlope(aT,aA1,aA2){ return 3.0*A(aA1,aA2)*aT*aT + 2.0*B(aA1,aA2)*aT + C(aA1); }

            const NEWTON_ITERATIONS = 4;
            const NEWTON_MIN_SLOPE = 0.001;
            const kSplineTableSize = 11;
            const kSampleStepSize = 1.0/(kSplineTableSize-1.0);
            const sampleValues = new Float32Array(kSplineTableSize);
            for (let i=0;i<kSplineTableSize;i++) sampleValues[i] = CalcBezier(i*kSampleStepSize,mX1,mX2);

            function getTForX(aX){
                let intervalStart=0.0;
                let currentSample=1;
                const lastSample = kSplineTableSize-1;
                for (;currentSample!==lastSample && sampleValues[currentSample]<=aX; currentSample++) intervalStart+=kSampleStepSize;
                --currentSample;
                const dist=(aX - sampleValues[currentSample])/(sampleValues[currentSample+1]-sampleValues[currentSample]);
                let guessForT=intervalStart + dist*kSampleStepSize;
                const initialSlope = GetSlope(guessForT,mX1,mX2);
                if(initialSlope>=NEWTON_MIN_SLOPE){
                    for(let i=0;i<NEWTON_ITERATIONS;i++){
                        const currentSlope = GetSlope(guessForT,mX1,mX2);
                        if(currentSlope===0.0) return guessForT;
                        const currentX = CalcBezier(guessForT,mX1,mX2)-aX;
                        guessForT-=currentX/currentSlope;
                    }
                }
                return guessForT;
            }
            return (x)=>CalcBezier(getTForX(x),mY1,mY2);
        }

        const ease = cubicBezier(0.2,0.8,0.2,1);

        // --- Animate counter text ---
        window.animateCounter = function(targetValue, duration){
            const textElement = document.getElementById('progress-percentage');
            if(!textElement) return;
            if(animationFrameId) cancelAnimationFrame(animationFrameId);
            const startValue = window.currentPercentage;
            let startTime = null;

            function step(timestamp){
                if(!startTime) startTime = timestamp;
                const linearProgress = Math.min((timestamp-startTime)/duration, 1);
                const easedProgress = ease(linearProgress);
                const currentValue = Math.round(startValue + (targetValue-startValue)*easedProgress);
                textElement.textContent = `${currentValue}%`;
                if(linearProgress<1) animationFrameId=requestAnimationFrame(step);
            }
            animationFrameId=requestAnimationFrame(step);
        }

        // --- Update progress bar ---
        window.updateProgressBar = function(percentage){
            const progressElement = document.querySelector('.progress');
            if(!progressElement) return;
            // Transition duration
            const duration = (percentage>window.currentPercentage && percentage<100)?7000:400;
            progressElement.style.transition = `transform ${duration/1000}s cubic-bezier(0.2,0.8,0.2,1)`;
            window.animateCounter(percentage,duration);
            progressElement.style.transform = `scaleX(${percentage/100})`;
            window.currentPercentage = percentage;
        }

        // --- Update subtitle/status text ---
        window.updateStatusText = function(text){
            const subtitleElement = document.querySelector('.subtitle');
            if(subtitleElement) subtitleElement.textContent = text;
        }

        // --- 3D viewer (unchanged) ---
        const viewer = $3Dmol.createViewer(document.getElementById('viewer3d'), {
            backgroundColor:'black', backgroundAlpha:0, antialias:false
        });
        $3Dmol.download('pdb:1A3N', viewer, {}, function(){
            viewer.setStyle({}, { cartoon:{ color:'spectrum' } });
            const presetView=[-14.45,-1.99,-13.16,-223.89,0.78,0,0,0.62];
            viewer.setView(presetView);
            viewer.render();
            viewer.spin("y",0.4);
            viewer.spin("x",0.1);
        });
    </script>

</body>
</html>
"""

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# NEW: Helper function from your Brain Tumor example
def crop_brain_contour(image, plot=False):
    """
    Crops the brain contour from an MRI image.
    (This function is identical to your training script)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(gray, 45, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.erode(thresh, None, iterations=2)
    thresh = cv2.dilate(thresh, None, iterations=2)

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    
    if not cnts:
        print("Warning: No contours found. Using original image.")
        return image
        
    c = max(cnts, key=cv2.contourArea)
    extLeft = tuple(c[c[:, :, 0].argmin()][0])
    extRight = tuple(c[c[:, :, 0].argmax()][0])
    extTop = tuple(c[c[:, :, 1].argmin()][0])
    extBot = tuple(c[c[:, :, 1].argmax()][0])
    
    new_image = image[extTop[1]:extBot[1], extLeft[0]:extRight[0]]
    return new_image

class LanguageManager:
    """Manages loading and installing QTranslator objects."""
    def __init__(self, app: QApplication):
        self.app = app
        # Keep a reference to the *current* translator
        self.translator = QTranslator(self.app)

    def load_language(self, language_name: str) -> bool:
        """
        Loads and installs the translator for the given language.
        This automatically triggers a LanguageChange event.
        """
        # 1. Map the display name (e.g., "Español") to a file code (e.g., "es")
        # You must customize this map to match your .qm file names
        lang_code_map = {
            "English (US)": "en",
            "Français": "fr",
            "Español": "es",
            "Deutsch": "de",        # German
            "العربية": "ar",
        }
        lang_code = lang_code_map.get(language_name, "en")

        # --- THIS IS THE KEY ---
        # 2. Always remove the *previous* translator first.
        self.app.removeTranslator(self.translator)

        # 3. Handle English (the source language)
        if lang_code == "en":
            # No translator is needed for the source language.
            # We've already removed the old one, so we are done.
            # We create a new empty translator for the *next* switch.
            self.translator = QTranslator(self.app)
            return True

        # 4. Load and install the new translator
        
        # Re-create the translator object to be safe
        self.translator = QTranslator(self.app)
        
        # Assumes .qm files are in 'translations/app_es.qm', 'translations/app_fr.qm'
        # You must generate these files using Qt's `pylupdate6` and `lrelease` tools.
        path = f"translations/translations_{lang_code}.qm" 
        
        if self.translator.load(path):
            # 5. Install the new translator on the *entire application*
            self.app.installTranslator(self.translator)
            print(f"Successfully loaded and installed {path}")
            return True
        else:
            print(f"Error: Could not load translation file: {path}")
            return False
class ModelLoaderWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int, str)

    def run(self):
        """Orchestrates loading of all models."""
        global breast_cancer_model
        global brain_tumor_model
        global lung_cancer_model # NEW
        
        try:
            # --- Stage 1: Initial setup ---
            self.progress.emit(10, "Loading assets...")
            time.sleep(0.5) # Simulate loading other small files

            # --- Stage 2: Load Breast Cancer Model ---
            print("Breast Cancer Model loading started...")
            self.progress.emit(40, "Loading Breast Cancer model...")
            
            breast_cancer_model = tf.keras.models.load_model(resource_path('models/best_model_bc.keras'))
            print("Breast Cancer Model loaded.")

            # --- Stage 3: Load Brain Tumor Model ---
            print("Brain Tumor Model loading started...")
            self.progress.emit(70, "Loading Brain Tumor model...")
            
            brain_tumor_model = tf.keras.models.load_model(resource_path('models/best_improved_brain_tumor_model.keras'))
            print("Brain Tumor Model loaded.")
            
            # --- Stage 4: Load Lung Cancer Model ---
            print("Lung Cancer Model loading started...")
            self.progress.emit(95, "Loading Lung Cancer model...")
            
            lung_cancer_model = tf.keras.models.load_model(resource_path('models/best_lung_cancer_model.keras'))
            print("Lung Cancer Model loaded.")
            
            # --- Stage 5: Finish ---
            print("All models loaded successfully.")
            self.progress.emit(100, "Assets loaded successfully")

        except Exception as e:
            # Updated error message to be more general
            error_message = f"Error: A model file was not found"
            print(f"ERROR: Failed to load models: {e}")
            self.progress.emit(100, error_message)
            time.sleep(2)
        
        finally:
            time.sleep(0.5) # A brief pause to let the user see "100%"
            self.finished.emit()

class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OncoDock Loading...")
        self.setMinimumSize(800, 400)
        self.isFirstShow = True

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.browser = QWebEngineView(self)
        self.browser.page().setBackgroundColor(QColor("transparent"))
        self.browser.setHtml(html_code)
        self.setCentralWidget(self.browser)
        self.js_ready = False
        self.pending_updates = []  # store progress calls that arrive too early
        self.browser.loadFinished.connect(self.on_js_ready)

    def on_js_ready(self, ok):
        if ok:
            self.js_ready = True
            print("Splash HTML/JS ready.")
            # flush pending updates
            for percentage, message in self.pending_updates:
                self._send_update_to_js(percentage, message)
            self.pending_updates.clear()

    def update_progress(self, percentage, message):
        if not self.js_ready:
            print("Queueing update until JS ready:", percentage, message)
            self.pending_updates.append((percentage, message))
            return
        self._send_update_to_js(percentage, message)

    def _send_update_to_js(self, percentage, message):
        safe_message = message.replace("'", "\\'")
        js_code_progress = f"updateProgressBar({percentage});"
        js_code_text = f"updateStatusText('{safe_message}');"
        self.browser.page().runJavaScript(js_code_progress)
        self.browser.page().runJavaScript(js_code_text)

# ==========================================================
# MODIFIED: SplashScreen
# ==========================================================



class GradientToggle(QWidget):
    def __init__(self, parent=None, callback=None, light_icon="assets/sun.png", dark_icon="assets/moon.png"):
        super().__init__(parent)
        self.setFixedSize(60, 30)  # smaller, same ratio as 100x50

        # State
        self._checked = False
        self._thumb_pos = 2
        self._pill_light = QColor("#f6f6f6")
        self._pill_dark = QColor("#2e2e2e")
        self._callback = callback

        # Icons
        self.sun_icon = QIcon(light_icon)
        self.moon_icon = QIcon(dark_icon)
        self.icon_scale = 0.55  # slightly smaller icons for compact look

        # Animation
        self._anim = QPropertyAnimation(self, b"thumb_pos")
        self._anim.setDuration(400)
    # NEW: Method to set the state without animation or triggering callback
    def set_initial_state(self, checked):
        self._checked = checked
        self._thumb_pos = self.width() - self.height() + 2 if checked else 2
        self.update()
    # --- Property for animation ---
    def get_thumb_pos(self):
        return self._thumb_pos

    def set_thumb_pos(self, value):
        self._thumb_pos = value
        self.update()

    thumb_pos = pyqtProperty(int, fget=get_thumb_pos, fset=set_thumb_pos)

    def mousePressEvent(self, event):
        self.toggle()

    def toggle(self):
        self._checked = not self._checked
        start = self._thumb_pos
        end = self.width() - self.height() + 2 if self._checked else 2
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()

        if self._callback:
            self._callback(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate animation progress
        min_pos = 2
        max_pos = self.width() - self.height() + 2
        progress = (self._thumb_pos - min_pos) / (max_pos - min_pos)

        # Pill color interpolation
        r = int(self._pill_light.red() * (1 - progress) + self._pill_dark.red() * progress)
        g = int(self._pill_light.green() * (1 - progress) + self._pill_dark.green() * progress)
        b = int(self._pill_light.blue() * (1 - progress) + self._pill_dark.blue() * progress)
        pill_color = QColor(r, g, b)

        # ---- Draw pill ----
        pill_rect = self.rect().adjusted(1, 1, -1, -1)
        p.setBrush(pill_color)

        pen = p.pen()
        pen.setColor(QColor("#888888"))
        pen.setWidth(1)  # thinner outline for smaller size
        p.setPen(pen)

        p.drawRoundedRect(pill_rect, pill_rect.height() // 2, pill_rect.height() // 2)

        # ---- Thumb ----
        thumb_rect = QRect(int(self._thumb_pos), 2, self.height() - 4, self.height() - 4)
        p.setBrush(QColor("white") if not self._checked else QColor("#5d6163"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(thumb_rect)

        # ---- Icon inside thumb ----
        icon = self.moon_icon if self._checked else self.sun_icon
        if not icon.isNull():
            icon_size = int(thumb_rect.width() * self.icon_scale)
            icon_rect = QRect(
                thumb_rect.center().x() - icon_size // 2,
                thumb_rect.center().y() - icon_size // 2,
                icon_size,
                icon_size
            )
            icon.paint(p, icon_rect, Qt.AlignmentFlag.AlignCenter)

        p.end()
# This is optional but helps hide noisy Chromium console messages
QLoggingCategory.setFilterRules("qt.webenginecontext.debug=false")

class JsApi(QObject):
    """A simple helper object to receive signals from JavaScript."""
    mol_data_received = pyqtSignal(str)

    @pyqtSlot(str)
    def receiveMolData(self, mol_data: str):
        """This slot is called from JavaScript with the molecule's MOL data."""
        if mol_data:
            self.mol_data_received.emit(mol_data)

class KetcherDialog(QDialog):
    """A dialog window for creating molecules using a local Ketcher instance."""
    molecule_created = pyqtSignal(str) # Emits the MOL block as a string

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Molecular Editor - Ketcher")
        self.setGeometry(100, 100, 1000, 750)
        self.setLayout(QVBoxLayout())

        # --- Web View and Page ---
        self.browser = QWebEngineView()
        self.page = QWebEnginePage(self)
        self.browser.setPage(self.page)

        # --- Communication Bridge (Python <-> JS) ---
        # 1. Create the Python object that will be exposed to JS
        self.js_api = JsApi()
        self.js_api.mol_data_received.connect(self.on_molecule_data_received)

        # 2. Create a QWebChannel to act as the bridge
        self.channel = QWebChannel()
        self.channel.registerObject("qt_api", self.js_api) # Expose js_api object as "qt_api" in JS

        # 3. Set the channel on the web page
        self.page.setWebChannel(self.channel)

        self.layout().addWidget(self.browser)
        self.load_ketcher()

    def load_ketcher(self):
        """Loads the local Ketcher HTML, injecting the QWebChannel script."""
        ketcher_path_obj = Path("ketcher-standalone-3.3.0/standalone/index.html").resolve()
        if not ketcher_path_obj.exists():
            QMessageBox.critical(self, "Ketcher Not Found", f"Could not find Ketcher at path:\n{ketcher_path_obj}")
            return

        # Read the original HTML content
        html_content = ketcher_path_obj.read_text(encoding='utf-8')

        # Inject the qwebchannel.js script into the <head>
        # This script is required for the JS side to communicate with Python.
        injection_script = '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>'
        modified_html = html_content.replace('</head>', f'{injection_script}</head>')

        # Load the modified HTML, using the original file path as the base URL
        # to ensure relative paths for CSS/JS files still work.
        self.browser.setHtml(modified_html, QUrl.fromLocalFile(str(ketcher_path_obj)))
        self.page.loadFinished.connect(self.inject_custom_js)

    def inject_custom_js(self, ok: bool):
        """Injects JS to add our button and connect it to the QWebChannel."""
        if not ok:
            return

        js_code = """
        var checkKetcher = setInterval(function() {
            if (window.ketcher) {
                clearInterval(checkKetcher);

                // --- Setup QWebChannel ---
                new QWebChannel(qt.webChannelTransport, function (channel) {
                    // Make the Python qt_api object available globally in JS
                    window.qt_api = channel.objects.qt_api;

                    // --- Create the Button ---
                    var saveBtn = document.createElement('button');
                    saveBtn.innerHTML = 'Use This Molecule';
                    saveBtn.style.cssText = `
                        position: fixed; bottom: 10px; right: 10px;

                        padding: 8px 12px; background-color: #4CAF50; color: white;
                        border: none; border-radius: 4px; cursor: pointer; font-weight: bold;
                    `;
                    document.body.appendChild(saveBtn);

                    // --- Add Click Event ---
                    saveBtn.onclick = function() {
                        if (window.qt_api) {
                            window.ketcher.getMolfile().then(molfile => {
                                // Call the Python slot via the exposed object
                                window.qt_api.receiveMolData(molfile);
                            });
                        } else {
                            alert('Error: Python communication channel not established.');
                        }
                    };
                });
            }
        }, 100);
        """
        self.page.runJavaScript(js_code)

    def on_molecule_data_received(self, mol_data: str):
        """Handles the data from Ketcher, emits a signal, and closes."""
        self.molecule_created.emit(mol_data)
        self.accept()

class LigandSelectionDialog(QDialog):
    """A dialog for selecting a ligand via SMILES, file, or drawing."""
    ligand_data_ready = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Ligand Source")
        self.setMinimumWidth(450)
        
        # Main layout for the entire dialog
        main_layout = QVBoxLayout(self)

        # Use a Form Layout for a clean, vertically-aligned look
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 10, 10, 10) # Add some padding
        form_layout.setSpacing(15) # Add vertical space between rows
        main_layout.addLayout(form_layout)

        # --- Row 1: SMILES Input ---
        self.smiles_input = QLineEdit()
        self.smiles_input.setPlaceholderText("e.g., CCO (Ethanol)")
        self.load_smiles_btn = QPushButton("Use")
        smiles_hbox = QHBoxLayout() # Use a HBox to place input and button side-by-side
        smiles_hbox.addWidget(self.smiles_input)
        smiles_hbox.addWidget(self.load_smiles_btn)
        form_layout.addRow("SMILES String:", smiles_hbox)

        # --- Row 2: File Upload ---
        self.upload_file_btn = QPushButton("Browse Files...")
        form_layout.addRow("Load from File:", self.upload_file_btn)

        # --- Row 3: Ketcher Editor ---
        self.create_mol_btn = QPushButton("Open Molecular Editor...")
        form_layout.addRow("Draw Molecule:", self.create_mol_btn)

        # --- Dialog Buttons (Cancel) ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)

        # --- Connect Signals ---
        self.load_smiles_btn.clicked.connect(self.use_smiles)
        self.upload_file_btn.clicked.connect(self.browse_file)
        self.create_mol_btn.clicked.connect(self.open_ketcher)
        self.button_box.rejected.connect(self.reject)
        
        self.ketcher_dialog = None
    def use_smiles(self):
        smiles = self.smiles_input.text().strip()
        if smiles:
            self.ligand_data_ready.emit("smiles", smiles)
            self.accept()
        else:
            QMessageBox.warning(self, "Input Error", "SMILES string cannot be empty.")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Ligand File",
            "",
            "Structure Files (*.sdf *.mol2 *.pdb *.mol *.smi *.smiles)"
        )
        if file_path:
            self.ligand_data_ready.emit("file", file_path)
            self.accept()

    def open_ketcher(self):
        # Lazily create the dialog to save resources
        if self.ketcher_dialog is None:
            self.ketcher_dialog = KetcherDialog(self)
            self.ketcher_dialog.molecule_created.connect(self.handle_ketcher_molecule)
        self.ketcher_dialog.exec()

    def handle_ketcher_molecule(self, mol_data: str):
        if mol_data:
            self.ligand_data_ready.emit("mol_string", mol_data)
            self.accept()# ======================= MOLECULE VIEWER WIDGET =======================

class LigandInputWidget(QWidget):
    """A clean widget to manage ligand selection. Does not include a label."""
    ligand_loaded = pyqtSignal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selection_dialog = None
        
        # Use a horizontal layout directly, no group box
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # No extra margins
        main_layout.setSpacing(10)
        
        self.ligand_display = QLineEdit()
        self.ligand_display.setReadOnly(True)
        # Placeholder text set in retranslateUi
        main_layout.addWidget(self.ligand_display)

        self.select_ligand_btn = QPushButton() # Text set in retranslateUi
        main_layout.addWidget(self.select_ligand_btn)
        
        self.select_ligand_btn.clicked.connect(self.open_selection_dialog)
        
        # Call the new method to set initial translatable strings
        self.retranslateUi()

    def retranslateUi(self):
        """
        Updates all translatable texts in the widget in real time 
        after a language change.
        """
        self.ligand_display.setPlaceholderText(
            QCoreApplication.translate("MolecularDockingWidget", "No ligand selected")
        )
        self.select_ligand_btn.setText(
            QCoreApplication.translate("MolecularDockingWidget", "Select Ligand...")
        )
        
        # Re-apply tooltips if they are currently enabled, ensuring they are translated
        # NOTE: This assumes the parent (MainWindow) calls set_tooltips_enabled 
        # after a language change to fully refresh, but we ensure the strings 
        # are translatable below.

    def set_tooltips_enabled(self, enabled: bool):
        """
        Applies or removes translatable tooltips from the internal widgets.
        """
        # --- MODIFIED: Tooltips are now translatable ---
        display_tip = QCoreApplication.translate(
            "MolecularDockingWidget", 
            "Displays the file name of the currently loaded ligand."
        )
        button_tip = QCoreApplication.translate(
            "MolecularDockingWidget", 
            "Click to open the ligand selection dialog.\nYou can load from a file, draw a molecule, or fetch by name/SMILES."
        )
        
        self.ligand_display.setToolTip(display_tip if enabled else "")
        self.select_ligand_btn.setToolTip(button_tip if enabled else "")
        
    def open_selection_dialog(self):
        if self.selection_dialog is None:
            self.selection_dialog = LigandSelectionDialog(self)
            self.selection_dialog.ligand_data_ready.connect(self.process_ligand_data)
        self.selection_dialog.exec()

    def process_ligand_data(self, input_type: str, data: str):
        try:
            output_path = None
            if input_type == "file":
                output_path = Path(data)
                self.ligand_display.setText(output_path.name)
            elif input_type in ["smiles", "mol_string"]:
                if input_type == "smiles":
                    # Create a temp path without holding the file open
                    fd, temp_path = tempfile.mkstemp(suffix=".sdf")
                    os.close(fd)  # close immediately
                    output_path = Path(temp_path)

                    cmd = ["obabel", f"-:{data}", "-O", str(output_path), "--gen3d"]
                    subprocess.run(cmd, check=True, capture_output=True, text=True)

                else:  # mol_string
                    # First write mol data to a temp file
                    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".mol", encoding='utf-8') as tmp_in:
                        tmp_in.write(data)
                        tmp_in.flush()
                        input_path = Path(tmp_in.name)

                    # Then create another temp file for the 3D SDF/PDB output
                    fd, temp_path = tempfile.mkstemp(suffix=".sdf")
                    os.close(fd)
                    output_path = Path(temp_path)

                    # Use OpenBabel to add 3D coords
                    cmd = ["obabel", str(input_path), "-O", str(output_path), "--gen3d"]
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                        
            if output_path and output_path.exists() and output_path.stat().st_size > 0:
                # Update display with filename (works for smiles, mol_string, or file)
                self.ligand_display.setText(output_path.name)
                # Emit to notify MolecularDockingWidget
                self.ligand_loaded.emit(output_path)
            else:
                if 'tmp_file' in locals() and output_path.exists():
                    output_path.unlink() # Clean up empty file
                raise RuntimeError("Generated ligand file is empty or invalid.")

        except FileNotFoundError:
            QMessageBox.critical(self, QCoreApplication.translate("MolecularDockingWidget", "Dependency Error"), QCoreApplication.translate("MolecularDockingWidget", "OpenBabel not found. Please ensure 'obabel' is in your system PATH to use SMILES strings."))
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, QCoreApplication.translate("MolecularDockingWidget", "OpenBabel Error"), QCoreApplication.translate("MolecularDockingWidget", f"Failed to convert SMILES.\n\nError: {e.stderr}"))
        except Exception as e:
            QMessageBox.critical(self, QCoreApplication.translate("MolecularDockingWidget", "Error"), QCoreApplication.translate("MolecularDockingWidget", f"An unexpected error occurred while processing the ligand: {e}"))

    def set_enabled(self, enabled: bool):
        self.select_ligand_btn.setEnabled(enabled)

class MoleculeViewerWidget(QWidget):
    def __init__(self, parent=None, default_style="Cartoon", tooltips_enabled=True):
        super().__init__(parent)
        self.molecule_loaded = False
        self.current_source = ""
        self.status_label = QLabel()
        self.default_style = default_style
        
        self._tooltips_enabled = tooltips_enabled

        # Widgets assigned to self for retranslation
        self.style_label = QLabel() 
        self.color_label = QLabel()
        self.surface_check = QCheckBox()
        self.launch_pymol_btn = QPushButton()
        self.style_combo = QComboBox()
        self.color_combo = QComboBox()

        self.layout = QVBoxLayout(self)
        self.setup_ui()
        self.init_viewer()
        
        self.retranslateUi()

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(120)
        self._debounce.timeout.connect(self._apply_style)

    # -----------------------------------------------------------
    # 1. NEW: changeEvent to trigger retranslation
    # -----------------------------------------------------------
    def changeEvent(self, event: QEvent):
        """
        Handles widget events, triggering retranslation upon language change.
        """
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    # -----------------------------------------------------------
    # 2. UPDATED: retranslateUi with more robust status check
    # -----------------------------------------------------------
    def retranslateUi(self):
        """
        Updates all translatable text in this widget.
        """
        # 1. Update simple labels
        self.style_label.setText(QCoreApplication.translate("MoleculeViewerWidget", "Style:"))
        self.color_label.setText(QCoreApplication.translate("MoleculeViewerWidget", "Color:"))
        
        # 2. Update button/check text
        self.surface_check.setText(QCoreApplication.translate("MoleculeViewerWidget", "Show Surface"))
        self.launch_pymol_btn.setText(QCoreApplication.translate("MoleculeViewerWidget", "Launch in PyMOL"))

        # 3. Update status label (only if it's in a translatable state)
        if not self.molecule_loaded:
            self.status_label.setText(
                QCoreApplication.translate("MoleculeViewerWidget", "No molecule loaded.")
            )
        else:
            # Re-translate the successful loaded message if applicable
            current_status = self.status_label.text()
            if current_status.startswith("Loaded:"):
                self.status_label.setText(
                    QCoreApplication.translate("MoleculeViewerWidget", "Loaded:") + f" {Path(self.current_source).name}"
                )
            # Add checks for other translated runtime statuses if needed

        # 4. Update all tooltips
        self.update_tooltips()

    # -----------------------------------------------------------
    # 3. UI Setup (Simplified, ensuring widgets are self attributes)
    # -----------------------------------------------------------
    def setup_ui(self):
        controls_layout = QHBoxLayout()
        
        self.style_combo = QComboBox()
        # Combo box items are generally fixed, but if they were translated, 
        # you would clear them and re-add them here, or use a custom model.
        # For simplicity, we assume the items themselves are fine.
        self.style_combo.addItems(["Cartoon", "Stick", "Sphere", "Line"])

        self.style_label = QLabel() 
        controls_layout.addWidget(self.style_label)
        controls_layout.addWidget(self.style_combo)

        self.color_combo = QComboBox()
        self.color_combo.addItems(["Spectrum", "Chain", "ssPyMol", "Residue"])
        
        self.color_label = QLabel() 
        controls_layout.addWidget(self.color_label)
        controls_layout.addWidget(self.color_combo)

        self.surface_check = QCheckBox() 
        controls_layout.addWidget(self.surface_check)
        controls_layout.addStretch()

        bg_color = "#f6f6f6" if THEME else "#2E2E2E"
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.web_view.page().setBackgroundColor(QColor(bg_color))

        self.layout.addLayout(controls_layout)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.web_view, 1)

        self.launch_pymol_btn = QPushButton() 
        self.launch_pymol_btn.setEnabled(False) 
        self.launch_pymol_btn.clicked.connect(self.launch_pymol)
        self.layout.addWidget(self.launch_pymol_btn)

        self.style_combo.currentTextChanged.connect(self.queue_style_update)
        self.color_combo.currentTextChanged.connect(self.queue_style_update)
        self.surface_check.stateChanged.connect(self.queue_style_update)

    # -----------------------------------------------------------
    # 4. Tooltip methods (OK, just keeping them for completeness)
    # -----------------------------------------------------------
    def set_tooltips_enabled(self, enabled: bool):
        """Public method to enable or disable all tooltips in this widget."""
        self._tooltips_enabled = enabled
        self.update_tooltips()

    def update_tooltips(self):
        """Applies or removes tooltips based on the internal flag."""
        tip_on = self._tooltips_enabled
        
        style_tip = QCoreApplication.translate(
            "MoleculeViewerWidget",
            "Select the rendering style for the molecule.\n- Cartoon: Best for proteins.\n- Stick: Shows all bonds."
        )
        color_tip = QCoreApplication.translate(
            "MoleculeViewerWidget",
            "Select the color scheme for the molecule.\n- Spectrum: Colors from N- to C-terminus.\n- Chain: Assigns a unique color per chain."
        )
        surface_tip = QCoreApplication.translate(
            "MoleculeViewerWidget",
            "Toggle the visibility of the solvent-accessible surface."
        )
        pymol_tip = QCoreApplication.translate(
            "MoleculeViewerWidget",
            "Launch the currently loaded molecule in an external PyMOL application.\nRequires PyMOL to be installed and in your system's PATH."
        )
        status_tip = QCoreApplication.translate(
            "MoleculeViewerWidget",
            "Shows the loading status of the molecule viewer."
        )

        self.style_combo.setToolTip(style_tip if tip_on else "")
        self.color_combo.setToolTip(color_tip if tip_on else "")
        self.surface_check.setToolTip(surface_tip if tip_on else "")
        self.launch_pymol_btn.setToolTip(pymol_tip if tip_on else "")
        self.status_label.setToolTip(status_tip if tip_on else "")

    # -----------------------------------------------------------
    # 5. Helper Methods (Ensuring runtime messages are translated)
    # -----------------------------------------------------------

    def set_file_path(self, filepath: str):
        # ... (unchanged initialization logic) ...
        self.molecule_loaded = False
        self.launch_pymol_btn.setEnabled(False)
        
        self.style_combo.setCurrentText(self.default_style)

        path = Path(filepath)
        if not path.exists():
            self.status_label.setText(
                QCoreApplication.translate("MoleculeViewerWidget", "File not found.")
            )
            return

        ext = path.suffix.lower()
        if ext in (".sdf", ".mol2"):
            pdb_path = path.with_suffix(".pdb")
            try:
                subprocess.run(["obabel", str(path), "-O", str(pdb_path), "--gen3d"],
                                check=True, capture_output=True, text=True)
                path = pdb_path
            except FileNotFoundError:
                self.status_label.setText(
                    QCoreApplication.translate("MoleculeViewerWidget", "OpenBabel not found. Install it or put it on PATH.")
                )
                return
            except subprocess.CalledProcessError as e:
                self.status_label.setText(
                    QCoreApplication.translate("MoleculeViewerWidget", "OpenBabel failed:") + f" {e.stderr.strip()[:200]}"
                )
                return

        try:
            pdb_text = path.read_text()
        except Exception as e:
            self.status_label.setText(
                QCoreApplication.translate("MoleculeViewerWidget", "Could not read file:") + f" {e}"
            )
            return

        if not pdb_text or len(pdb_text.strip()) == 0:
            self.status_label.setText(
                QCoreApplication.translate("MoleculeViewerWidget", "File is empty or invalid.")
            )
            return

        if ("ATOM" not in pdb_text) and ("HETATM" not in pdb_text) and ("MODEL" not in pdb_text):
            self.status_label.setText(
                QCoreApplication.translate("MoleculeViewerWidget", "Warning: file doesn't look like a standard PDB. Trying anyway...")
            )

        pdb_json = json.dumps(pdb_text)
        STYLE_MAP, COLOR_MAP = self._maps()
        style = STYLE_MAP.get(self.style_combo.currentText(), "cartoon")
        color = COLOR_MAP.get(self.color_combo.currentText(), "spectrum")
        show_surface = self.surface_check.isChecked()

        js_to_run = (
            f"window._3dmol_api && window._3dmol_api.loadPDBData && "
            f"_3dmol_api.loadPDBData({pdb_json}, '{style}', '{color}', {str(show_surface).lower()});"
        )

        def try_run_js(attempts_left=10):
            if attempts_left <= 0:
                self.status_label.setText(
                    QCoreApplication.translate("MoleculeViewerWidget", "Timed out waiting for viewer to initialize.")
                )
                return

            def on_check(ready):
                if ready:
                    self.web_view.page().runJavaScript(js_to_run)
                    self.molecule_loaded = True
                    self.current_source = str(path)
                    self.launch_pymol_btn.setEnabled(True)
                    self.status_label.setText(
                        QCoreApplication.translate("MoleculeViewerWidget", "Loaded:") + f" {path.name}"
                    )
                else:
                    QTimer.singleShot(200, lambda: try_run_js(attempts_left - 1))
            
            self.web_view.page().runJavaScript("typeof window._3dmol_api !== 'undefined' && typeof window._3dmol_api.loadPDBData === 'function';", on_check)

        self.status_label.setText(
            QCoreApplication.translate("MoleculeViewerWidget", "Loading") + f" {path.name} ..."
        )
        QTimer.singleShot(100, try_run_js)

    def launch_pymol(self):
        """Launches the PyMOL application with the current molecule."""
        if not self.molecule_loaded or not self.current_source:
            QMessageBox.warning(
                self, 
                QCoreApplication.translate("MoleculeViewerWidget", "No File"), 
                QCoreApplication.translate("MoleculeViewerWidget", "No molecule file is currently loaded.")
            )
            return

        try:
            subprocess.Popen(["pymol", self.current_source])

        except FileNotFoundError:
            QMessageBox.critical(
                self,
                QCoreApplication.translate("MoleculeViewerWidget", "Error: PyMOL Not Found"),
                QCoreApplication.translate(
                    "MoleculeViewerWidget",
                    "The 'pymol' command was not found.\n\n"
                    "Please make sure PyMOL is installed and its executable "
                    "is in your system's PATH environment variable."
                )
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                QCoreApplication.translate("MoleculeViewerWidget", "Error"), 
                QCoreApplication.translate("MoleculeViewerWidget", "An unexpected error occurred:") + f" {str(e)}"
            )
            print(e)
            
    # --- Other methods (init_viewer, _maps, queue_style_update, _apply_style) are unchanged ---

    def init_viewer(self):
        bg_color = "#f6f6f6" if THEME else "#2E2E2E"
        html_content = HTML_TEMPLATE.format(bg_color=bg_color)
        self.web_view.setHtml(html_content)

        if self.molecule_loaded and self.current_source:
            QTimer.singleShot(100, lambda: self.set_file_path(self.current_source))

    def _maps(self):
        COLOR_MAP = {"Spectrum": "spectrum", "Chain": "chain", "ssPyMol": "ssPyMol", "Residue": "amino"}
        STYLE_MAP = {"Cartoon": "cartoon", "Stick": "stick", "Sphere": "sphere", "Line": "line"}
        return STYLE_MAP, COLOR_MAP
        
    def queue_style_update(self, *_):
        if self.molecule_loaded:
            self._debounce.start()

    def _apply_style(self):
        if not self.molecule_loaded:
            return
        STYLE_MAP, COLOR_MAP = self._maps()
        style = STYLE_MAP.get(self.style_combo.currentText(), "cartoon")
        color = COLOR_MAP.get(self.color_combo.currentText(), "spectrum")
        show_surface = self.surface_check.isChecked()
        js = (
            f"window._3dmol_api && _3dmol_api.loadPDBData({json.dumps(Path(self.current_source).read_text())},"
            f"'{style}','{color}',{str(show_surface).lower()});"
        )
        self.web_view.page().runJavaScript(js)
# DOCKING WORKER THREAD (From Docker)
# ==========================================================
class DockingWorker(QThread):
    progress_update = pyqtSignal(str)
    progress_replace = pyqtSignal(str)
    completed = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, receptor_pdb_path, ligand_sdf_path):
        super().__init__()
        self.receptor_pdb_path = receptor_pdb_path
        self.ligand_sdf_path = ligand_sdf_path

    def run(self):
        try:
            # --- TOOL PATHS (update if needed) ---
            MGL_PYTHON = resource_path(r"MGLTools-1.5.7\python.exe")
            PREPARE_RECEPTOR = resource_path(r"MGLTools-1.5.7\Lib\site-packages\AutoDockTools\Utilities24\prepare_receptor4.py")
            PREPARE_LIGAND = resource_path(r"MGLTools-1.5.7\Lib\site-packages\AutoDockTools\Utilities24\prepare_ligand4.py")
            OBABEL_EXE = resource_path(r"OpenBabel-3.1.1\obabel.exe")

            # --- FILE NAMES ---
            RECEPTOR_PDBQT = Path("receptor.pdbqt")
            LIGAND_MOL2 = Path("ligand.mol2")
            LIGAND_PDBQT = Path("ligand.pdbqt")
            VINA_CONFIG = Path("config.txt")
            VINA_OUT_PDBQT = Path("docked_output.pdbqt")
            VINA_OUT_PDB = Path("docked_output.pdb")

            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "Starting docking process..."))

            # Step 1: Convert ligand SDF → MOL2
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "Step 1/5: Converting ligand SDF to MOL2 with OpenBabel..."))
            subprocess.run([str(OBABEL_EXE), str(self.ligand_sdf_path), "-O", str(LIGAND_MOL2), "--gen3d"], check=True, capture_output=True, text=True)
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", f"Ligand MOL2 saved as {LIGAND_MOL2}"))

            # Step 2: Prepare receptor
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "Step 2/5: Preparing receptor with MGLTools..."))
            subprocess.run([str(MGL_PYTHON), str(PREPARE_RECEPTOR), "-r", str(self.receptor_pdb_path), "-o", str(RECEPTOR_PDBQT)], check=True, capture_output=True, text=True)
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", f"Receptor PDBQT saved as {RECEPTOR_PDBQT}"))

            # Step 3: Prepare ligand
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "Step 3/5: Preparing ligand with MGLTools..."))
            subprocess.run([str(MGL_PYTHON), str(PREPARE_LIGAND), "-l", str(LIGAND_MOL2), "-o", str(LIGAND_PDBQT)], check=True, capture_output=True, text=True)
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", f"Ligand PDBQT saved as {LIGAND_PDBQT}"))

            # Step 4: Create config file (same as Vina format)
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "Step 4/5: Creating Gnina config file..."))
            config_content = (
                f"receptor = /data/{RECEPTOR_PDBQT.name}\n"
                f"ligand = /data/{LIGAND_PDBQT.name}\n\n"
                f"center_x = -26.0\ncenter_y = 12.0\ncenter_z = 58.0\n\n"
                f"size_x = 20\nsize_y = 20\nsize_z = 20\n\n"
                f"exhaustiveness = 8\nnum_modes = 9"
            )
            VINA_CONFIG.write_text(config_content)
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", f"Gnina config saved as {VINA_CONFIG}"))

            # Step 5: Run Gnina via Docker (CPU-only, CNN scoring enabled)
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "Step 5/5: Running Gnina docking via Docker (with CNN scoring)..."))

            gnina_cmd_string = (
                f"stdbuf -o0 gnina --config /data/{VINA_CONFIG.name} "
                f"--out /data/{VINA_OUT_PDBQT.name} "
                f"--log /data/gnina.log "
                f"--cnn_scoring rescore --cnn fast"
            )

            cmd = [
                "docker", "run", "--rm",
                "-v", f"{Path.cwd()}:/data",
                "gnina/gnina:latest",
                "/bin/sh", "-c",
                gnina_cmd_string
            ]

            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "--- Gnina Output ---"))
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1
            )

            stdout_log = []
            line_buffer = ""

            for char in iter(lambda: process.stdout.read(1), ''):
                if char == '\n':
                    if line_buffer:
                        self.progress_update.emit(line_buffer)
                        stdout_log.append(line_buffer)
                    line_buffer = ""
                elif char == '\r':
                    if line_buffer:
                        self.progress_replace.emit(line_buffer)
                    line_buffer = ""
                else:
                    line_buffer += char

            if line_buffer:
                self.progress_update.emit(line_buffer)
                stdout_log.append(line_buffer)

            process.stdout.close()

            stderr_output = process.stderr.read().strip()
            process.stderr.close()
            return_code = process.wait()

            if return_code != 0:
                raise subprocess.CalledProcessError(
                    return_code,
                    cmd,
                    output="\n".join(stdout_log),
                    stderr=stderr_output
                )

            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "-------------------\nGnina docking complete."))

            # Step 6: Convert docked result to PDB
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "Step 6/7: Converting docked output to PDB..."))
            subprocess.run([str(OBABEL_EXE), str(VINA_OUT_PDBQT), "-O", str(VINA_OUT_PDB)], check=True, capture_output=True, text=True)
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", f"Docked ligand poses saved as PDB: {VINA_OUT_PDB}"))

            # Step 7: Create Complex PDB Files
            self.progress_update.emit(QCoreApplication.translate("DockingWorker", "Step 7/7: Creating docked complex PDB files..."))
            COMPLEX_PDB_ALL = Path("docked_complex_all.pdb")
            COMPLEX_PDB_TOP1 = Path("docked_complex_top1.pdb")

            try:
                receptor_text = Path(self.receptor_pdb_path).read_text()
                ligand_text_all_models = VINA_OUT_PDB.read_text()

                complex_text_all = receptor_text.strip() + "\nEND\n" + ligand_text_all_models
                COMPLEX_PDB_ALL.write_text(complex_text_all)
                self.progress_update.emit(QCoreApplication.translate("DockingWorker", f"Full complex (all poses) saved as: {COMPLEX_PDB_ALL}"))

                ligand_model_1_lines = []
                in_model_1 = False

                if "MODEL" not in ligand_text_all_models:
                    ligand_model_1_text = ligand_text_all_models
                else:
                    for line in ligand_text_all_models.splitlines():
                        if line.startswith("MODEL 1"):
                            in_model_1 = True
                        elif line.startswith("ENDMDL"):
                            if in_model_1:
                                ligand_model_1_lines.append(line)
                                break
                        if in_model_1:
                            ligand_model_1_lines.append(line)
                    ligand_model_1_text = "\n".join(ligand_model_1_lines)

                complex_text_top1 = receptor_text.strip() + "\nEND\n" + ligand_model_1_text
                COMPLEX_PDB_TOP1.write_text(complex_text_top1)
                self.progress_update.emit(QCoreApplication.translate("DockingWorker", f"Top pose complex (for viewer) saved as: {COMPLEX_PDB_TOP1}"))

            except Exception as e:
                self.error.emit(QCoreApplication.translate("DockingWorker", f"Failed to create complex PDB file: {e}"))
                return

            self.completed.emit(QCoreApplication.translate("DockingWorker", "All steps completed successfully!"))

        except FileNotFoundError as e:
            self.error.emit(QCoreApplication.translate("DockingWorker", f"Error: A required tool was not found.\nMissing file: {e.filename}"))
        except subprocess.CalledProcessError as e:
            self.error.emit(QCoreApplication.translate("DockingWorker", f"A subprocess command failed.\nCommand: {' '.join(e.cmd)}\n\nSTDERR:\n{e.stderr}"))
        except Exception as e:
            self.error.emit(QCoreApplication.translate("DockingWorker", f"An unexpected error occurred:\n{e}"))

# ==========================================================
# Main Integrated GUI Application Class
# ==========================================================

class MolecularDockingWidget(QWidget):
    def __init__(self, parent=None, tooltips_enabled=True):
        super().__init__(parent)
        self.receptor_file_path = None
        self.ligand_file_path = None
        self.worker_thread = None
        self.settings = None 
        self.last_line_was_progress = False
        self._tooltips_enabled = tooltips_enabled
        
        # New attributes to hold widgets for retranslation (These were already good)
        self.inputs_group = QGroupBox()
        self.process_log_label = QLabel()
        self.receptor_label = QLabel()  # Will hold the label for the receptor row
        self.ligand_label = QLabel()    # Will hold the label for the ligand row
        
        self.initUI()
        self.connect_signals()
        # IMPORTANT: Call retranslateUi to set initial text after initUI is done
        self.retranslateUi() 

    def initUI(self):
        """Initializes the UI structure without setting static, translatable text."""
        main_layout = QHBoxLayout(self)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setMinimumWidth(350)
        left_widget.setMaximumWidth(600)

        # --- Combined Inputs Group ---
        # 1. ASSIGN GroupBox to self.inputs_group for retranslation
        self.inputs_group = QGroupBox() 
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 30, 10, 10)
        form_layout.setVerticalSpacing(15)
        self.inputs_group.setLayout(form_layout)

        # --- Receptor Row ---
        self.receptor_id_input = QLineEdit()
        # 2. ASSIGN QPushButton to self.receptor_download_btn for retranslation
        self.receptor_download_btn = QPushButton() 
        receptor_hbox = QHBoxLayout()
        receptor_hbox.setSpacing(10)
        receptor_hbox.addWidget(self.receptor_id_input)
        receptor_hbox.addWidget(self.receptor_download_btn)
        
        # 3. CREATE a QLabel for the row title and assign to self.receptor_label
        self.receptor_label = QLabel()
        form_layout.addRow(self.receptor_label, receptor_hbox)
        
        # --- Ligand Row ---
        self.ligand_input_widget = LigandInputWidget()
        # 4. CREATE a QLabel for the row title and assign to self.ligand_label
        self.ligand_label = QLabel()
        form_layout.addRow(self.ligand_label, self.ligand_input_widget)
        left_layout.addWidget(self.inputs_group) # Use self.inputs_group now

        # --- Docking Button ---
        # 5. ASSIGN QPushButton to self.run_docking_btn for retranslation
        self.run_docking_btn = QPushButton()
        self.run_docking_btn.setEnabled(False)
        self.run_docking_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        left_layout.addWidget(self.run_docking_btn)

        # --- Process Log Section ---
        # 6. ASSIGN QLabel to self.process_log_label for retranslation
        self.process_log_label = QLabel() 
        left_layout.addWidget(self.process_log_label)
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        left_layout.addWidget(self.output_log, 1)

        # --- Status Label ---
        # 7. ASSIGN QLabel to self.status_label for retranslation
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        left_layout.addWidget(self.status_label)

        # --- Right Side (Tabs and Splitter) ---
        self.tabs = QTabWidget()
        self.receptor_viewer = MoleculeViewerWidget(default_style="Cartoon")
        self.ligand_viewer = MoleculeViewerWidget(default_style="Stick")
        self.docked_viewer = MoleculeViewerWidget(default_style="Stick")

        # 8. Add tabs with EMPTY text, text is set in retranslateUi
        self.tabs.addTab(self.receptor_viewer, "")
        self.tabs.addTab(self.ligand_viewer, "")
        self.tabs.addTab(self.docked_viewer, "")

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.tabs)
        self.splitter.setHandleWidth(6)
        main_layout.addWidget(self.splitter)

    # -----------------------------------------------------------
    ## Retranslation Core 🌐
    # -----------------------------------------------------------

    def retranslateUi(self):
        """Updates all translatable strings in the widget."""
        
        # 1. Widget Titles/Labels
        self.inputs_group.setTitle(QCoreApplication.translate("MolecularDockingWidget", "Inputs:"))
        self.receptor_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Receptor Input:"))
        self.ligand_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Ligand Input:"))
        self.process_log_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Process Log:"))
        
        # 2. Buttons and Placeholders
        self.receptor_id_input.setPlaceholderText(
            QCoreApplication.translate("MolecularDockingWidget", "e.g., 6LU7")
        )
        self.receptor_download_btn.setText(
            QCoreApplication.translate("MolecularDockingWidget", "Download PDB")
        )
        self.run_docking_btn.setText(
            QCoreApplication.translate("MolecularDockingWidget", "Run Docking")
        )
        
        # 3. Status
        # The status label must be checked before translation, otherwise we lose runtime status messages.
        # Only translate if it matches one of the known static/completion statuses.
        current_status = self.status_label.text()
        if current_status in ["Ready.", "Receptor downloaded.", "Ligand is ready.", "Docking finished successfully!", "Docking failed!"]:
             self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", current_status))
        elif current_status == "Downloading...":
             self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Downloading..."))
        elif current_status == "Docking in progress...":
             self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Docking in progress..."))

        # 4. Tab Titles
        self.tabs.setTabText(0, QCoreApplication.translate("MolecularDockingWidget", "Receptor"))
        self.tabs.setTabText(1, QCoreApplication.translate("MolecularDockingWidget", "Ligand"))
        self.tabs.setTabText(2, QCoreApplication.translate("MolecularDockingWidget", "Docked Output"))

        # 5. Tooltips (Applies both UI tooltips and propagates to children)
        self.update_tooltips()
        
        # 6. Propagate to Custom Child Widgets
        # Call retranslateUi on child widgets if they support it
        if hasattr(self.ligand_input_widget, 'retranslateUi'):
            self.ligand_input_widget.retranslateUi()
        if hasattr(self.receptor_viewer, 'retranslateUi'):
            self.receptor_viewer.retranslateUi()
        if hasattr(self.ligand_viewer, 'retranslateUi'):
            self.ligand_viewer.retranslateUi()
        if hasattr(self.docked_viewer, 'retranslateUi'):
            self.docked_viewer.retranslateUi()

    def changeEvent(self, event):
        """Handles widget events, triggering retranslation upon language change."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)
        
    # -----------------------------------------------------------
    ## Helper Methods (Translation added to runtime messages) 💬
    # -----------------------------------------------------------
        
    def download_receptor(self):
        pdb_id = self.receptor_id_input.text().strip().upper()
        if not pdb_id:
            # Translated Error Message
            title = QCoreApplication.translate("MolecularDockingWidget", "Input Error")
            msg = QCoreApplication.translate("MolecularDockingWidget", "Please enter a valid PDB ID.")
            self.show_message_box(title, msg)
            return

        self.output_log.clear()
        self.output_log.append(
            QCoreApplication.translate("MolecularDockingWidget", "Downloading PDB ID: {pdb_id}...").format(pdb_id=pdb_id)
        )
        self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Downloading..."))
        QCoreApplication.processEvents()

        try:
            url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            if "not found" in response.text.lower():
                # Translated Download Error
                title = QCoreApplication.translate("MolecularDockingWidget", "Download Error")
                msg = QCoreApplication.translate("MolecularDockingWidget", "PDB ID '{pdb_id}' not found.").format(pdb_id=pdb_id)
                self.show_message_box(title, msg)
                return

            self.receptor_file_path = Path(f"{pdb_id}.pdb")
            self.receptor_file_path.write_text(response.text)
            self.output_log.append(
                QCoreApplication.translate("MolecularDockingWidget", "Receptor saved as {file_path}").format(file_path=self.receptor_file_path)
            )
            self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Receptor downloaded."))
            self.receptor_viewer.set_file_path(str(self.receptor_file_path))
            self.check_inputs()

        except requests.exceptions.RequestException as e:
            # Translated Network Error
            title = QCoreApplication.translate("MolecularDockingWidget", "Network Error")
            msg = QCoreApplication.translate("MolecularDockingWidget", "Could not download receptor: {error}").format(error=e)
            self.show_message_box(title, msg, is_error=True)

    def on_ligand_loaded(self, file_path: Path):
        """Handles a newly loaded ligand file from the input widget."""
        self.ligand_file_path = file_path
        self.output_log.append(
            QCoreApplication.translate("MolecularDockingWidget", "Ligand loaded: {file_name}").format(file_name=self.ligand_file_path.name)
        )
        self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Ligand is ready."))
        self.ligand_viewer.set_file_path(str(self.ligand_file_path))
        self.check_inputs()

    def run_docking(self):
        if self.receptor_file_path and self.ligand_file_path:
            self.set_buttons_enabled(False)
            self.output_log.clear()
            self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Docking in progress..."))
            self.last_line_was_progress = False 

            self.worker_thread = DockingWorker(self.receptor_file_path, self.ligand_file_path)
            self.worker_thread.progress_update.connect(self.update_log)
            self.worker_thread.progress_replace.connect(self.replace_log_line) 
            self.worker_thread.completed.connect(self.docking_completed)
            self.worker_thread.error.connect(self.docking_failed)
            self.worker_thread.start()
        else:
            # Translated Input Error
            title = QCoreApplication.translate("MolecularDockingWidget", "Input Error")
            msg = QCoreApplication.translate("MolecularDockingWidget", "Please select both a receptor and a ligand file.")
            self.show_message_box(title, msg)

    def docking_completed(self, message):
        self.update_log(message)
        self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Docking finished successfully!"))
        self.set_buttons_enabled(True)
        
        # Translated Success Message
        title = QCoreApplication.translate("MolecularDockingWidget", "Success")
        msg = QCoreApplication.translate("MolecularDockingWidget", "Docking process completed successfully!")
        self.show_message_box(title, msg)

        docked_file = Path("docked_output.pdb")
        if docked_file.exists():
            self.docked_viewer.set_file_path(str(docked_file))
            self.tabs.setCurrentWidget(self.docked_viewer)
            
    def docking_failed(self, message):
        self.update_log(message)
        self.status_label.setText(QCoreApplication.translate("MolecularDockingWidget", "Docking failed!"))
        self.set_buttons_enabled(True)
        
        # Translated Failure Message
        title = QCoreApplication.translate("MolecularDockingWidget", "Docking Failed")
        # 'message' here is already translated by DockingWorker.error
        self.show_message_box(title, message, is_error=True)

    # -----------------------------------------------------------
    ## Remaining Methods (Tooltips and others)
    # -----------------------------------------------------------
    
    # Tooltip methods are already structured correctly for translation
    def set_tooltips_enabled(self, enabled: bool):
        self._tooltips_enabled = enabled
        self.update_tooltips()

    def update_tooltips(self):
        tip_on = self._tooltips_enabled
        
        # --- Define Tooltip Texts (Already correctly wrapped) ---
        receptor_id_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "Enter a 4-character PDB ID (e.g., 6LU7) for the receptor."
        )
        receptor_btn_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "Download the specified receptor PDB file from the RCSB database."
        )
        ligand_widget_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "Controls for loading the ligand.\nClick the button to select a file or input a SMILES string."
        )
        run_btn_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "Start the molecular docking simulation.\nRequires both a receptor and a ligand to be loaded."
        )
        log_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "Shows the detailed log, progress, and any errors from the docking process."
        )
        status_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "Displays the current status of the application."
        )
        tabs_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "Container for viewing the different molecular structures."
        )
        receptor_tab_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "View the 3D structure of the loaded receptor."
        )
        ligand_tab_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "View the 3D structure of the loaded ligand."
        )
        docked_tab_tip = QCoreApplication.translate(
            "MolecularDockingWidget",
            "View the 3D structure of the docked ligand-receptor complex after a successful run."
        )


        # --- Apply or Remove Tooltips ---
        self.receptor_id_input.setToolTip(receptor_id_tip if tip_on else "")
        self.receptor_download_btn.setToolTip(receptor_btn_tip if tip_on else "")
        self.ligand_input_widget.setToolTip(ligand_widget_tip if tip_on else "")
        self.run_docking_btn.setToolTip(run_btn_tip if tip_on else "")
        self.output_log.setToolTip(log_tip if tip_on else "")
        self.status_label.setToolTip(status_tip if tip_on else "")
        self.tabs.setToolTip(tabs_tip if tip_on else "")

        # Apply to individual tabs
        self.tabs.setTabToolTip(0, receptor_tab_tip if tip_on else "")
        self.tabs.setTabToolTip(1, ligand_tab_tip if tip_on else "")
        self.tabs.setTabToolTip(2, docked_tab_tip if tip_on else "")

        # --- Propagate to Custom Child Widgets ---
        if hasattr(self.ligand_input_widget, 'set_tooltips_enabled'):
            self.ligand_input_widget.set_tooltips_enabled(tip_on)
        if hasattr(self.receptor_viewer, 'set_tooltips_enabled'):
            self.receptor_viewer.set_tooltips_enabled(tip_on)
        if hasattr(self.ligand_viewer, 'set_tooltips_enabled'):
            self.ligand_viewer.set_tooltips_enabled(tip_on)
        if hasattr(self.docked_viewer, 'set_tooltips_enabled'):
            self.docked_viewer.set_tooltips_enabled(tip_on)
            
    # --- Other methods remain unchanged, or were only slightly modified above ---
    def connect_signals(self):
        self.receptor_download_btn.clicked.connect(self.download_receptor)
        self.ligand_input_widget.ligand_loaded.connect(self.on_ligand_loaded)
        self.run_docking_btn.clicked.connect(self.run_docking)
        self.receptor_id_input.textChanged.connect(self.check_inputs)
        
    def check_inputs(self):
        """Checks if both receptor and ligand are ready to enable docking."""
        receptor_ready = self.receptor_file_path is not None and self.receptor_file_path.exists()
        ligand_ready = self.ligand_file_path is not None and self.ligand_file_path.exists()
        is_ready = receptor_ready and ligand_ready
        self.run_docking_btn.setEnabled(is_ready)
    
    def update_log(self, message):
        self.output_log.append(message)
        self.last_line_was_progress = False # Mark this as a normal line
        QCoreApplication.processEvents()

    def replace_log_line(self, message):
        """Replaces the last line in the log with the new message."""
        cursor = self.output_log.textCursor()
        
        if self.last_line_was_progress:
            # If the last line was a progress bar, remove it
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
        
        # Append the new progress line
        self.output_log.append(message) 
        
        self.last_line_was_progress = True # Mark this as a progress line
        self.output_log.ensureCursorVisible()
        QCoreApplication.processEvents()
        
    def set_buttons_enabled(self, enabled: bool):
        """Enables or disables input buttons during processing."""
        self.receptor_download_btn.setEnabled(enabled)
        # Update to control the new ligand widget's button
        self.ligand_input_widget.set_enabled(enabled)

        if enabled:
            # Re-check if the run button should be enabled
            self.check_inputs()
        else:
            # Always disable the run button when processing
            self.run_docking_btn.setEnabled(False)
            
    def show_message_box(self, title, message, is_error=False):
        # This helper is now part of the translation framework
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title) # Title is expected to be translated by the caller
        msg_box.setText(message)     # Message is expected to be translated by the caller
        msg_box.setIcon(QMessageBox.Icon.Critical if is_error else QMessageBox.Icon.Information)
        msg_box.exec()

    def save_splitter_state(self, settings):
        if settings:
            splitter_state = self.splitter.saveState()
            settings.setValue("splitterState", splitter_state)
            
    def restore_splitter_state(self, settings):
        self.settings = settings
        if self.settings:
            state = self.settings.value("splitterState")
            if state:
                self.splitter.restoreState(state)
            else:
                self.splitter.setSizes([400, 800])

class BreastCancerWidget(QWidget):
    def __init__(self, parent=None, tooltips_enabled=True):
        super().__init__(parent)
        self.theme = THEME
        
        # Define all variables within the class
        self.class_names = ['benign', 'malignant', 'normal']
        self.image_size = (256, 256)
        
        self._tooltips_enabled = tooltips_enabled
        
        # Instantiate widgets 
        self.title_label = QLabel()
        self.subtitle_label = QLabel()
        self.select_button = QPushButton()
        self.status_label = QLabel()
        self.image_label = QLabel()
        self.result_label = QLabel()
        self.confidence_title = QLabel()
        self.progress_bars = {} # Dictionary of QProgressBars

        self.create_widgets()
        self.setObjectName("breast_cancer_widget")
        
        # Call retranslateUi to set initial text and tooltips
        self.retranslateUi() 

    # -----------------------------------------------------------
    # 1. changeEvent to trigger retranslation (Correct)
    # -----------------------------------------------------------
    def changeEvent(self, event: QEvent):
        """
        Handles widget events, triggering retranslation upon language change.
        """
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    # -----------------------------------------------------------
    # 2. retranslateUi (FIXED LOGIC)
    # -----------------------------------------------------------
    def retranslateUi(self):
        """
        Updates all translatable text and tooltips in this widget.
        
        FIX: The conditional logic for status/image/prediction placeholders 
        is now based on the presence of dynamic data rather than fragile 
        string comparison of translated texts.
        """
        # 1. Titles and Static Labels (Always update)
        self.title_label.setText(QCoreApplication.translate("BreastCancerWidget", "Breast Cancer Detector"))
        self.subtitle_label.setText(QCoreApplication.translate("BreastCancerWidget", "An AI-powered tool for classifying breast cancer images."))
        self.confidence_title.setText(QCoreApplication.translate("BreastCancerWidget", "Confidence Scores"))
        
        # 2. Buttons (Always update)
        self.select_button.setText(QCoreApplication.translate("BreastCancerWidget", "Select Image"))
        
        # 3. Default/Initial Statuses and Results (Conditional updates for real-time translation)
        
        # --- FIX 1: Ready Status Text ---
        # Resets the status to 'Ready...' unless it's an active dynamic status (i.e., 'Processing: /path')
        ready_text = QCoreApplication.translate("BreastCancerWidget", "Ready to classify images...")
        current_status_text = self.status_label.text()
        
        # We assume if the status contains a path delimiter ('/' or '\'), it's a dynamic 'Processing' message 
        # that should not be interrupted/reset during a language change. Otherwise, reset to 'Ready...'.
        if not current_status_text or (not ('/' in current_status_text or '\\' in current_status_text)):
            self.status_label.setText(ready_text)

        # --- FIX 2: Image Preview Text ---
        # Updates only if no image pixmap is currently loaded.
        preview_text = QCoreApplication.translate("BreastCancerWidget", "Image preview will appear here.")
        if self.image_label.pixmap() is None or self.image_label.pixmap().isNull():
            self.image_label.setText(preview_text)
        
        # --- FIX 3: Prediction Default Text ---
        # Updates the placeholder unless an actual prediction result (containing a colon ':') is displayed.
        prediction_text = QCoreApplication.translate("BreastCancerWidget", "Prediction will appear here.")
        # An actual prediction contains a colon (e.g., "Prediction: malignant\nConfidence: 99.99%").
        # If a colon is NOT present, it's a default/placeholder text and should be updated.
        if ":" not in self.result_label.text():
            self.result_label.setText(prediction_text)

        # 4. Progress Bars (Format)
        for class_name in self.class_names:
            progress_bar = self.progress_bars.get(class_name)
            if progress_bar:
                # Class name itself is translated within the format string
                translated_class = QCoreApplication.translate("BreastCancerWidget", class_name.capitalize())
                translated_format = f"{translated_class}: %p%" 
                progress_bar.setFormat(translated_format)

        # 5. Tooltips
        self.update_tooltips()


    # -----------------------------------------------------------
    # 3. MODIFIED: create_widgets (Structural) - FIXED IMAGE LABEL VISIBILITY
    # -----------------------------------------------------------
    def create_widgets(self):
        """
        Sets up the layout and widgets of the application, 
        assigning them to self attributes.
        """
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(40)

        # Left-side vertical layout for all controls and the image
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)

        # Title and Subtitle
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("titleLabel")
        
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setObjectName("subtitleLabel")
        
        left_layout.addWidget(self.title_label)
        left_layout.addWidget(self.subtitle_label)

        # Select Button
        self.select_button.setObjectName("selectButton")
        self.select_button.clicked.connect(self.select_image)
        left_layout.addWidget(self.select_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status Label
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        left_layout.addWidget(self.status_label)

        # Image display area
        self.image_frame = QFrame()
        self.image_frame.setObjectName("imageFrame")
        self.image_frame.setFixedSize(QSize(400, 400))
        image_layout = QVBoxLayout(self.image_frame)
        
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # FIX: Ensure QLabel expands to fill the QFrame when no pixmap is loaded.
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        image_layout.addWidget(self.image_label)
        
        left_layout.addWidget(self.image_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addStretch(1)
        main_layout.addLayout(left_layout)

        # Right-side vertical layout for the result label and confidence breakdown
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)

        # Result Label
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.result_label.setObjectName("resultLabel")
        right_layout.addWidget(self.result_label)

        # Create a container for the confidence breakdown
        self.confidence_frame = QFrame()
        self.confidence_frame.setObjectName("confidenceFrame")
        self.confidence_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        confidence_layout = QVBoxLayout(self.confidence_frame)
        confidence_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Confidence Title
        self.confidence_title.setObjectName("confidenceTitle")
        confidence_layout.addWidget(self.confidence_title)

        # Progress Bars
        for class_name in self.class_names:
            progress_bar = QProgressBar()
            progress_bar.setValue(0)
            
            self.progress_bars[class_name] = progress_bar
            confidence_layout.addWidget(progress_bar)

        right_layout.addWidget(self.confidence_frame)
        right_layout.addStretch(1)
        main_layout.addLayout(right_layout)

    # -----------------------------------------------------------
    # 4. MODIFIED: select_image (Translates runtime messages)
    # -----------------------------------------------------------
    def select_image(self):
        """
        Opens a file dialog, processes the selected image, and displays the prediction.
        """
        global breast_cancer_model 

        if breast_cancer_model is None:
            title = QCoreApplication.translate("BreastCancerWidget", "Error")
            msg = QCoreApplication.translate("BreastCancerWidget", "Model is not loaded. Cannot make a prediction.")
            QMessageBox.warning(self, title, msg)
            return

        file_dialog_title = QCoreApplication.translate("BreastCancerWidget", "Select an Image")
        file_path, _ = QFileDialog.getOpenFileName(
            self, file_dialog_title, "", "Image Files (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        self.status_label.setText(
            QCoreApplication.translate("BreastCancerWidget", "Processing: {file_path}").format(file_path=file_path)
        )

        try:
            # Placeholder for actual model interaction logic
            img = Image.open(file_path).convert('RGB')
            img_resized = img.resize(self.image_size)

            pixmap = QPixmap(file_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_frame.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.image_label.setText("") # Clear placeholder text when image is loaded

            # Placeholder prediction logic
            img_array = np.array(img_resized)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0

            # Mock predictions for demonstration if model is not truly available
            if breast_cancer_model:
                predictions = breast_cancer_model.predict(img_array)
                scores = tf.nn.softmax(predictions[0])
            else:
                # Mock scores for testing translation updates
                # Fallback to numpy if tensorflow is not available for softmax (mock logic)
                raw_scores = np.array([0.15, 0.70, 0.15])
                exp_scores = np.exp(raw_scores - np.max(raw_scores))
                scores = exp_scores / exp_scores.sum()
                
            predicted_index = np.argmax(scores)
            predicted_class_name = self.class_names[predicted_index]
            confidence = 100 * scores[predicted_index]

            # Translation of the predicted class name
            translated_class = QCoreApplication.translate("BreastCancerWidget", predicted_class_name.capitalize())

            self.result_label.setText(
                QCoreApplication.translate("BreastCancerWidget", "Prediction: {class_name}\nConfidence: {confidence:.2f}%").format(
                    class_name=translated_class, 
                    confidence=confidence
                )
            )
            self.status_label.setText(QCoreApplication.translate("BreastCancerWidget", "Prediction complete."))

            for i, class_name in enumerate(self.class_names):
                self.progress_bars[class_name].setValue(int(scores[i] * 100))

        except Exception as e:
            title = QCoreApplication.translate("BreastCancerWidget", "Error")
            msg = QCoreApplication.translate("BreastCancerWidget", "An error occurred during prediction: {error}").format(error=e)
            QMessageBox.critical(self, title, msg)
            self.status_label.setText(QCoreApplication.translate("BreastCancerWidget", "Error occurred."))
            
    # -----------------------------------------------------------
    # 5. Tooltip Methods 
    # -----------------------------------------------------------
    def set_tooltips_enabled(self, enabled: bool):
        self._tooltips_enabled = enabled
        self.update_tooltips()

    def update_tooltips(self):
        tip_on = self._tooltips_enabled
        
        select_btn_tip = QCoreApplication.translate("BreastCancerWidget", "Click to open a file dialog and select a breast histopathology image (.png, .jpg) for AI classification.")
        status_tip = QCoreApplication.translate("BreastCancerWidget", "Displays the current operational status of the detector (e.g., Ready, Processing, Error).")
        image_tip = QCoreApplication.translate("BreastCancerWidget", "Preview area for the selected breast tissue image (resized to 256x256 for prediction).")
        result_tip = QCoreApplication.translate("BreastCancerWidget", "Shows the AI model's final prediction and the overall percentage confidence score.")
        confidence_frame_tip = QCoreApplication.translate("BreastCancerWidget", "Detailed breakdown of the model's prediction confidence across all classification classes.")
        benign_tip = QCoreApplication.translate("BreastCancerWidget", "The model's confidence that the tissue is Benign (non-cancerous).")
        malignant_tip = QCoreApplication.translate("BreastCancerWidget", "The model's confidence that the tissue is Malignant (cancerous).")
        normal_tip = QCoreApplication.translate("BreastCancerWidget", "The model's confidence that the tissue is Normal (healthy).")

        self.select_button.setToolTip(select_btn_tip if tip_on else "")
        self.status_label.setToolTip(status_tip if tip_on else "")
        self.image_frame.setToolTip(image_tip if tip_on else "")
        self.image_label.setToolTip(image_tip if tip_on else "")
        self.result_label.setToolTip(result_tip if tip_on else "")
        self.confidence_frame.setToolTip(confidence_frame_tip if tip_on else "")
        self.confidence_title.setToolTip(confidence_frame_tip if tip_on else "")
        
        if 'benign' in self.progress_bars:
            self.progress_bars['benign'].setToolTip(benign_tip if tip_on else "")
        if 'malignant' in self.progress_bars:
            self.progress_bars['malignant'].setToolTip(malignant_tip if tip_on else "")
        if 'normal' in self.progress_bars:
            self.progress_bars['normal'].setToolTip(normal_tip if tip_on else "")


class LungCancerWidget(QWidget):
    def __init__(self, parent=None, tooltips_enabled=True):
        super().__init__(parent)
        
        self.theme = THEME
        
        # --- Configuration ---
        self.class_names = ['Adenocarcinoma', 'Benign', 'Squamous Carcinoma']
        self.image_size = (224, 224)
        self._tooltips_enabled = tooltips_enabled
        
        # --- Attributes for Translatable Widgets (Mandatory for i18n) ---
        self.title_label = QLabel()
        self.subtitle_label = QLabel()
        self.select_button = QPushButton()
        self.status_label = QLabel()
        self.image_label = QLabel()
        self.result_label = QLabel()
        self.confidence_title = QLabel()
        self.progress_bars = {} # Dictionary of QProgressBars
        
        self.create_widgets()
        self.setObjectName("lung_cancer_widget")
        
        # Set initial text and tooltips via the new i18n method
        self.retranslateUi() 

    # -----------------------------------------------------------
    # 1. changeEvent to trigger retranslation (Correct)
    # -----------------------------------------------------------
    def changeEvent(self, event: QEvent):
        """
        Handles widget events, triggering retranslation upon language change.
        """
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    # -----------------------------------------------------------
    # 2. FIXED: retranslateUi method with robust logic
    # -----------------------------------------------------------
    def retranslateUi(self):
        """
        Updates all translatable text, formats, and tooltips in this widget.
        The logic is now state-based to ensure correct real-time translation.
        """
        # 1. Titles and Static Labels (Always update)
        self.title_label.setText(QCoreApplication.translate("LungCancerWidget", "Lung Cancer Detector"))
        self.subtitle_label.setText(QCoreApplication.translate("LungCancerWidget", "An AI-powered tool for classifying lung histopathology images."))
        self.confidence_title.setText(QCoreApplication.translate("LungCancerWidget", "Confidence Scores"))
        
        # 2. Buttons (Always update)
        self.select_button.setText(QCoreApplication.translate("LungCancerWidget", "Select Image"))
        
        # 3. Conditional Placeholder Text (State-based updates)
        
        # --- FIX 1: Ready Status Text ---
        # Only update if the current status is not a dynamic 'Processing' message.
        # We identify a dynamic message by checking for file path separators.
        ready_text = QCoreApplication.translate("LungCancerWidget", "Ready to classify images...")
        current_status_text = self.status_label.text()
        if not current_status_text or ('/' not in current_status_text and '\\' not in current_status_text):
            self.status_label.setText(ready_text)

        # --- FIX 2: Image Preview Text ---
        # Only show the placeholder if no image (pixmap) is currently displayed.
        preview_text = QCoreApplication.translate("LungCancerWidget", "Image preview will appear here.")
        if self.image_label.pixmap() is None or self.image_label.pixmap().isNull():
            self.image_label.setText(preview_text)
        
        # --- FIX 3: Prediction Default Text ---
        # Only update the placeholder if no actual prediction (identified by a ':') is shown.
        prediction_text = QCoreApplication.translate("LungCancerWidget", "Prediction will appear here.")
        if ":" not in self.result_label.text():
            self.result_label.setText(prediction_text)

        # 4. Progress Bars (Format)
        for class_name in self.class_names:
            progress_bar = self.progress_bars.get(class_name)
            if progress_bar:
                # The class name is part of the format string and must be translated.
                translated_class = QCoreApplication.translate("LungCancerWidget", class_name.replace(" ", ""))
                translated_format = f"{translated_class}: %p%"
                progress_bar.setFormat(translated_format)

        # 5. Tooltips
        self.update_tooltips()


    # -----------------------------------------------------------
    # 3. MODIFIED: create_widgets (No direct translation calls)
    # -----------------------------------------------------------
    def create_widgets(self):
        """
        Sets up the layout and widgets of the application, 
        assigning them to self attributes. Text is set in retranslateUi.
        """
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(40)

        # Left-side vertical layout for all controls and the image
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)

        # Title and Subtitle 
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("titleLabel")
        
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setObjectName("subtitleLabel")
        
        left_layout.addWidget(self.title_label)
        left_layout.addWidget(self.subtitle_label)

        # Select image button 
        self.select_button.setObjectName("selectButton")
        self.select_button.clicked.connect(self.select_image)
        left_layout.addWidget(self.select_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status label
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        left_layout.addWidget(self.status_label)

        # Image display area
        self.image_frame = QFrame()
        self.image_frame.setObjectName("imageFrame")
        self.image_frame.setFixedSize(QSize(400, 400))
        image_layout = QVBoxLayout(self.image_frame)
        
        # Image label
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.image_label)
        
        left_layout.addWidget(self.image_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        left_layout.addStretch(1)
        main_layout.addLayout(left_layout)

        # Right-side vertical layout for the result label and confidence breakdown
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)

        # Main result label
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.result_label.setObjectName("resultLabel")
        right_layout.addWidget(self.result_label)

        # Create a container for the confidence breakdown
        self.confidence_frame = QFrame()
        self.confidence_frame.setObjectName("confidenceFrame")
        self.confidence_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        confidence_layout = QVBoxLayout(self.confidence_frame)
        confidence_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Confidence title
        self.confidence_title.setObjectName("confidenceTitle")
        confidence_layout.addWidget(self.confidence_title)

        # Labels and progress bars for each class
        for class_name in self.class_names:
            progress_bar = QProgressBar()
            progress_bar.setValue(0)
            
            # Format is set in retranslateUi
            self.progress_bars[class_name] = progress_bar
            confidence_layout.addWidget(progress_bar)

        right_layout.addWidget(self.confidence_frame)
        right_layout.addStretch(1)
        main_layout.addLayout(right_layout)

    # -----------------------------------------------------------
    # 4. MODIFIED: update_tooltips (Structure remains, call handled by retranslateUi)
    # -----------------------------------------------------------
    def set_tooltips_enabled(self, enabled: bool):
        """Public method to enable or disable all tooltips."""
        self._tooltips_enabled = enabled
        self.update_tooltips()

    def update_tooltips(self):
        """Applies or removes tooltips based on the enabled flag."""
        tip_on = self._tooltips_enabled
        
        # --- Define Tooltip Texts (Already translatable) ---
        select_btn_tip = QCoreApplication.translate("LungCancerWidget", "Click to open a file dialog and select a lung histopathology image for AI classification.")
        status_tip = QCoreApplication.translate("LungCancerWidget", "Displays the current operational status of the detector (Ready, Processing, Error).")
        image_tip = QCoreApplication.translate("LungCancerWidget", "Preview area for the selected lung tissue image (resized to 224x224 for prediction).")
        result_tip = QCoreApplication.translate("LungCancerWidget", "Shows the AI model's final prediction for lung cancer type and the overall percentage confidence score.")
        confidence_frame_tip = QCoreApplication.translate("LungCancerWidget", "Detailed breakdown of the model's prediction confidence across all lung cancer classification classes.")

        adeno_tip = QCoreApplication.translate("LungCancerWidget", "The model's confidence that the tissue is Adenocarcinoma (a type of lung cancer).")
        benign_tip = QCoreApplication.translate("LungCancerWidget", "The model's confidence that the tissue is Benign (non-cancerous).")
        squamous_tip = QCoreApplication.translate("LungCancerWidget", "The model's confidence that the tissue is Squamous Cell Carcinoma (a type of lung cancer).")

        # --- Apply or Remove Tooltips ---
        self.select_button.setToolTip(select_btn_tip if tip_on else "")
        self.status_label.setToolTip(status_tip if tip_on else "")
        self.image_frame.setToolTip(image_tip if tip_on else "")
        self.image_label.setToolTip(image_tip if tip_on else "")
        self.result_label.setToolTip(result_tip if tip_on else "")
        self.confidence_frame.setToolTip(confidence_frame_tip if tip_on else "")
        self.confidence_title.setToolTip(confidence_frame_tip if tip_on else "")
        
        if 'Adenocarcinoma' in self.progress_bars:
             self.progress_bars['Adenocarcinoma'].setToolTip(adeno_tip if tip_on else "")
        if 'Benign' in self.progress_bars:
             self.progress_bars['Benign'].setToolTip(benign_tip if tip_on else "")
        if 'Squamous Carcinoma' in self.progress_bars:
             self.progress_bars['Squamous Carcinoma'].setToolTip(squamous_tip if tip_on else "")

    # -----------------------------------------------------------
    # 5. MODIFIED: select_image (Runtime strings are translated)
    # -----------------------------------------------------------
    def select_image(self):
        """
        Opens a file dialog, processes the selected image using the
        lung cancer preprocessing pipeline, and displays the prediction.
        """
        global lung_cancer_model

        if lung_cancer_model is None:
            title = QCoreApplication.translate("LungCancerWidget", "Error")
            msg = QCoreApplication.translate("LungCancerWidget", "Model is not loaded. Cannot make a prediction.")
            QMessageBox.warning(self, title, msg)
            return

        file_dialog_title = QCoreApplication.translate("LungCancerWidget", "Select an Image")
        file_path, _ = QFileDialog.getOpenFileName(
            self, file_dialog_title, "", "Image Files (*.png *.jpg *.jpeg *.tif *.bmp)"
        )

        if not file_path:
            return

        # Status update (using format string for translatability)
        self.status_label.setText(
            QCoreApplication.translate("LungCancerWidget", "Processing: {file_path}").format(file_path=file_path)
        )

        try:
            # --- Lung Cancer Preprocessing (from your standalone app) ---
            image_cv = cv2.imread(file_path)
            if image_cv is None:
                raise Exception(QCoreApplication.translate("LungCancerWidget", "Could not read image file with OpenCV."))
                
            image_cv_resized = cv2.resize(image_cv, self.image_size, interpolation=cv2.INTER_CUBIC)
            
            # --- Display Image ---
            pixmap = QPixmap(file_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_frame.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.image_label.setText("")

            # --- Prepare for Model ---
            img_array = np.array(image_cv_resized)
            img_array_normalized = img_array / 255.0
            img_batch = np.expand_dims(img_array_normalized, axis=0)
            
            # --- Make Prediction ---
            predictions = lung_cancer_model.predict(img_batch)
            # NOTE: Mock model returns [[0.1, 0.8, 0.1]] -> index 1 ('Benign')
            scores = predictions[0]
            
            predicted_index = np.argmax(scores)
            predicted_class_name = self.class_names[predicted_index]
            confidence = 100 * np.max(scores)

            # Translate the predicted class name for display
            translated_class = QCoreApplication.translate("LungCancerWidget", predicted_class_name)

            # --- Display Result ---
            self.result_label.setText(
                QCoreApplication.translate("LungCancerWidget", "Prediction: {class_name}\nConfidence: {confidence:.2f}%").format(
                    class_name=translated_class, 
                    confidence=confidence
                )
            )
            self.status_label.setText(QCoreApplication.translate("LungCancerWidget", "Prediction complete."))

            # Add color based on prediction (Logic uses internal class name)
            if predicted_class_name == 'Benign':
                self.result_label.setStyleSheet("color: #4CAF50;") # Green
            else: # Adenocarcinoma or Squamous Carcinoma
                self.result_label.setStyleSheet("color: #E03B3B;") # Red

            # Update the progress bars
            for i, class_name in enumerate(self.class_names):
                self.progress_bars[class_name].setValue(int(scores[i] * 100))

        except Exception as e:
            title = QCoreApplication.translate("LungCancerWidget", "Error")
            msg_format = QCoreApplication.translate("LungCancerWidget", "An error occurred during prediction: {error}")
            QMessageBox.critical(self, title, msg_format.format(error=e))
            self.status_label.setText(QCoreApplication.translate("LungCancerWidget", "Error occurred."))
            self.result_label.setStyleSheet("")

class BrainTumorWidget(QWidget):
    def __init__(self, parent=None, tooltips_enabled=True):
        super().__init__(parent)
        
        self.theme = THEME
        
        # --- Configuration ---
        self.class_names = ['No Tumor', 'Tumor'] 
        self.image_size = (224, 224) 
        self._tooltips_enabled = tooltips_enabled
        
        # --- Attributes for Translatable Widgets ---
        self.title_label = QLabel()
        self.subtitle_label = QLabel()
        self.select_button = QPushButton()
        self.status_label = QLabel()
        self.image_label = QLabel()
        self.result_label = QLabel()
        self.confidence_title = QLabel()
        self.progress_bars = {} 
        
        self.create_widgets()
        self.setObjectName("brain_tumor_widget")
        
        # Set initial text and tooltips via the i18n method
        self.retranslateUi()

    # -----------------------------------------------------------
    # 1. changeEvent to trigger retranslation (Correct)
    # -----------------------------------------------------------
    def changeEvent(self, event: QEvent):
        """
        Handles widget events, triggering retranslation upon language change.
        """
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    # -----------------------------------------------------------
    # 2. FIXED: retranslateUi with robust, state-based logic
    # -----------------------------------------------------------
    def retranslateUi(self):
        """
        Updates all translatable text, formats, and tooltips in this widget.
        """
        # 1. Titles and Static Labels (Always update)
        self.title_label.setText(QCoreApplication.translate("BrainTumorWidget", "Brain Tumor Detector"))
        self.subtitle_label.setText(QCoreApplication.translate("BrainTumorWidget", "An AI-powered tool for classifying brain MRI images."))
        self.confidence_title.setText(QCoreApplication.translate("BrainTumorWidget", "Confidence Scores"))
        
        # 2. Buttons (Always update)
        self.select_button.setText(QCoreApplication.translate("BrainTumorWidget", "Select Image"))
        
        # 3. Conditional Placeholder Text (State-based updates)
        
        # --- FIX 1: Ready Status Text ---
        # Only update if the current status is not a dynamic 'Processing' message.
        ready_text = QCoreApplication.translate("BrainTumorWidget", "Ready to classify images...")
        current_status_text = self.status_label.text()
        if not current_status_text or ('/' not in current_status_text and '\\' not in current_status_text):
            self.status_label.setText(ready_text)

        # --- FIX 2: Image Preview Text ---
        # Only show the placeholder if no image (pixmap) is currently displayed.
        preview_text = QCoreApplication.translate("BrainTumorWidget", "Image preview will appear here.")
        if self.image_label.pixmap() is None or self.image_label.pixmap().isNull():
            self.image_label.setText(preview_text)
        
        # --- FIX 3: Prediction Default Text ---
        # Only update the placeholder if no actual prediction (identified by a ':') is shown.
        prediction_text = QCoreApplication.translate("BrainTumorWidget", "Prediction will appear here.")
        if ":" not in self.result_label.text():
            self.result_label.setText(prediction_text)

        # 4. Progress Bars (Format)
        for class_name in self.class_names:
            progress_bar = self.progress_bars.get(class_name)
            if progress_bar:
                translated_class = QCoreApplication.translate("BrainTumorWidget", class_name.replace(" ", ""))
                translated_format = f"{translated_class}: %p%"
                progress_bar.setFormat(translated_format)

        # 5. Tooltips
        self.update_tooltips()

    # -----------------------------------------------------------
    # 3. MODIFIED: create_widgets (No direct translation calls)
    # -----------------------------------------------------------
    def create_widgets(self):
        """
        Sets up the layout and widgets of the application.
        Text is set in retranslateUi.
        """
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(40)

        # Left-side vertical layout for all controls and the image
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)

        # Title and Subtitle 
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("titleLabel")
        
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setObjectName("subtitleLabel")
        
        left_layout.addWidget(self.title_label)
        left_layout.addWidget(self.subtitle_label)

        # Select image button 
        self.select_button.setObjectName("selectButton")
        self.select_button.clicked.connect(self.select_image)
        left_layout.addWidget(self.select_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status label
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")
        left_layout.addWidget(self.status_label)

        # Image display area
        self.image_frame = QFrame()
        self.image_frame.setObjectName("imageFrame")
        self.image_frame.setFixedSize(QSize(400, 400))
        image_layout = QVBoxLayout(self.image_frame)
        
        # Image label
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.image_label)
        
        left_layout.addWidget(self.image_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        left_layout.addStretch(1)
        main_layout.addLayout(left_layout)

        # Right-side vertical layout for the result label and confidence breakdown
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)

        # Main result label
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.result_label.setObjectName("resultLabel")
        right_layout.addWidget(self.result_label)

        # Create a container for the confidence breakdown
        self.confidence_frame = QFrame()
        self.confidence_frame.setObjectName("confidenceFrame")
        self.confidence_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        confidence_layout = QVBoxLayout(self.confidence_frame)
        confidence_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Confidence title
        self.confidence_title.setObjectName("confidenceTitle")
        confidence_layout.addWidget(self.confidence_title)

        # Labels and progress bars for each class
        for class_name in self.class_names:
            progress_bar = QProgressBar()
            progress_bar.setValue(0)
            
            # Format is set in retranslateUi
            self.progress_bars[class_name] = progress_bar
            confidence_layout.addWidget(progress_bar)

        right_layout.addWidget(self.confidence_frame)
        right_layout.addStretch(1)
        main_layout.addLayout(right_layout)

    # -----------------------------------------------------------
    # 4. MODIFIED: update_tooltips (Structure remains)
    # -----------------------------------------------------------
    def set_tooltips_enabled(self, enabled: bool):
        """Public method to enable or disable all tooltips."""
        self._tooltips_enabled = enabled
        self.update_tooltips()

    def update_tooltips(self):
        """Applies or removes tooltips based on the enabled flag."""
        tip_on = self._tooltips_enabled
        
        # --- Define Tooltip Texts (Already translatable) ---
        select_btn_tip = QCoreApplication.translate("BrainTumorWidget", "Click to open a file dialog and select a brain MRI image for AI classification.")
        status_tip = QCoreApplication.translate("BrainTumorWidget", "Displays the current operational status of the detector (Ready, Processing, Error).")
        image_tip = QCoreApplication.translate("BrainTumorWidget", "Preview area for the selected brain MRI image (resized to 224x224 for prediction).")
        result_tip = QCoreApplication.translate("BrainTumorWidget", "Shows the AI model's final prediction (Tumor or No Tumor) and the overall percentage confidence score.")
        confidence_frame_tip = QCoreApplication.translate("BrainTumorWidget", "Detailed breakdown of the model's prediction confidence across both classification classes.")

        no_tumor_tip = QCoreApplication.translate("BrainTumorWidget", "The model's confidence that the MRI image shows No Tumor.")
        tumor_tip = QCoreApplication.translate("BrainTumorWidget", "The model's confidence that the MRI image shows a Tumor.")

        # --- Apply or Remove Tooltips ---
        self.select_button.setToolTip(select_btn_tip if tip_on else "")
        self.status_label.setToolTip(status_tip if tip_on else "")
        self.image_frame.setToolTip(image_tip if tip_on else "")
        self.image_label.setToolTip(image_tip if tip_on else "")
        self.result_label.setToolTip(result_tip if tip_on else "")
        self.confidence_frame.setToolTip(confidence_frame_tip if tip_on else "")
        self.confidence_title.setToolTip(confidence_frame_tip if tip_on else "")
        
        if 'No Tumor' in self.progress_bars:
             self.progress_bars['No Tumor'].setToolTip(no_tumor_tip if tip_on else "")
        if 'Tumor' in self.progress_bars:
             self.progress_bars['Tumor'].setToolTip(tumor_tip if tip_on else "")
             
    # -----------------------------------------------------------
    # 5. MODIFIED: select_image (Runtime strings are translated)
    # -----------------------------------------------------------
    def select_image(self):
        """
        Opens a file dialog, processes the selected image using the
        brain tumor preprocessing pipeline, and displays the prediction.
        """
        global brain_tumor_model

        if brain_tumor_model is None:
            title = QCoreApplication.translate("BrainTumorWidget", "Error")
            msg = QCoreApplication.translate("BrainTumorWidget", "Model is not loaded. Cannot make a prediction.")
            QMessageBox.warning(self, title, msg)
            return

        file_dialog_title = QCoreApplication.translate("BrainTumorWidget", "Select an Image")
        file_path, _ = QFileDialog.getOpenFileName(
            self, file_dialog_title, "", "Image Files (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        # Status update (using format string for translatability)
        self.status_label.setText(
            QCoreApplication.translate("BrainTumorWidget", "Processing: {file_path}").format(file_path=file_path)
        )

        try:
            # --- Brain Tumor Preprocessing ---
            image_cv = cv2.imread(file_path)
            if image_cv is None:
                raise Exception(QCoreApplication.translate("BrainTumorWidget", "Could not read image file with OpenCV."))
                
            # 2. Crop the brain contour
            try:
                image_cv_cropped = crop_brain_contour(image_cv)
            except Exception as e:
                # Translating the warning message
                print(QCoreApplication.translate("BrainTumorWidget", "Warning: Could not crop image. Using original. Error: {e}").format(e=e))
                image_cv_cropped = image_cv # Fallback

            # 3. Resize to model's expected input
            image_cv_resized = cv2.resize(image_cv_cropped, self.image_size, interpolation=cv2.INTER_CUBIC)
            
            # --- Display Image ---
            pixmap = QPixmap(file_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_frame.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.image_label.setText("")

            # --- Prepare for Model ---
            img_array = np.array(image_cv_resized)
            img_batch = np.expand_dims(img_array, axis=0)
            img_array_preprocessed = preprocess_input(img_batch) 

            # --- Make Prediction ---
            predictions = brain_tumor_model.predict(img_array_preprocessed)
            probability_tumor = predictions[0][0] 
            
            # Create a 2-class score array: Index 0: No Tumor, Index 1: Tumor
            scores = np.array([1 - probability_tumor, probability_tumor])
            
            predicted_index = np.argmax(scores)
            predicted_class_name = self.class_names[predicted_index]
            confidence = 100 * scores[predicted_index]

            # Translate the predicted class name for display
            translated_class = QCoreApplication.translate("BrainTumorWidget", predicted_class_name)

            # --- Display Result ---
            self.result_label.setText(
                QCoreApplication.translate("BrainTumorWidget", "Prediction: {class_name}\nConfidence: {confidence:.2f}%").format(
                    class_name=translated_class, 
                    confidence=confidence
                )
            )
            self.status_label.setText(QCoreApplication.translate("BrainTumorWidget", "Prediction complete."))

            # Optional: Add color based on prediction
            if predicted_index == 1: # Tumor
                self.result_label.setStyleSheet("color: #E03B3B;") 
            else: # No Tumor
                self.result_label.setStyleSheet("color: #4CAF50;") 

            # Update the progress bars
            for i, class_name in enumerate(self.class_names):
                self.progress_bars[class_name].setValue(int(scores[i] * 100))

        except Exception as e:
            title = QCoreApplication.translate("BrainTumorWidget", "Error")
            msg_format = QCoreApplication.translate("BrainTumorWidget", "An error occurred during prediction: {error}")
            QMessageBox.critical(self, title, msg_format.format(error=e))
            self.status_label.setText(QCoreApplication.translate("BrainTumorWidget", "Error occurred."))
            self.result_label.setStyleSheet("")

def create_molecular_docking_tab() -> QWidget:
    """Creates and returns the fully-featured molecular docking widget."""
    return MolecularDockingWidget()

def create_cancer_detection_tab():
    """
    Creates the QTabWidget but does NOT set the translatable tab titles.
    This is handled by MainWindow's retranslateUi method.
    """
    tab_widget = QTabWidget()
    
    breast_cancer_widget = BreastCancerWidget()
    lung_cancer_widget = LungCancerWidget()
    brain_tumor_widget = BrainTumorWidget()
    
    # --- FIX: Add tabs with placeholder text, or no text at all ---
    # The actual text will be set and updated in retranslateUi.
    tab_widget.addTab(breast_cancer_widget, "...") 
    tab_widget.addTab(lung_cancer_widget, "...")
    tab_widget.addTab(brain_tumor_widget, "...")
    
    return tab_widget

# ==========================================================
# NEW: Main Application Window
# This class sets up the main window with tabs and the theme switcher.
# ==========================================================

class SettingsWindow(QDialog):
    # --- MODIFIED: Signal to emit the specific setting key and its state ---
    tooltips_changed = pyqtSignal(str, bool)
    theme_changed = pyqtSignal(str)# Emits "light", "dark", or "system_default"
    language_changed = pyqtSignal(str) # Emits the new language name (e.g., "Español")

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # --- Settings and Initialization ---
        if parent and hasattr(parent, 'settings'):
            self.settings = parent.settings
        else:
            # Fallback to an IniFormat QSettings
            self.settings = QSettings("settings.ini", QSettings.Format.IniFormat)

        # Assuming parent has an is_dark_mode attribute for initial theme check
        self.theme = 'dark' if parent and hasattr(parent, 'is_dark_mode') and parent.is_dark_mode else 'light'
        
        self.font_family = 'Poppins' 
        self.corner_radius = 14
        self.dragging = False
        self.drag_position = QPoint()
        
        # --- Translatable Widget Attributes (Initialized in _build_ui/pages) ---
        self.close_btn = None
        self.title_icon_label = None
        self.title_text_label = None
        self.sidebar_buttons = []
        
        # General Page Widgets
        self.language_combo = None
        self.language_label = None # <-- NEW
        self.log_level_combo = None
        self.log_level_label = None # <-- NEW
        self.log_path_edit = None
        self.log_path_label = None # <-- NEW
        self.updates_check = None
        
        # Preferences Page Widgets
        self.theme_combo = None
        self.theme_label = None # <-- NEW
        self.tooltips_group = None # <-- NEW
        self.tooltips_viewers_check = None
        self.tooltips_viewers_label = None # <-- NEW
        self.tooltips_docking_check = None
        self.tooltips_docking_label = None # <-- NEW
        self.tooltips_settings_check = None
        self.tooltips_settings_label = None # <-- NEW
        self.default_style_combo = None
        self.default_style_label = None # <-- NEW
        self.docking_precision_slider = None
        self.docking_precision_label = None # <-- NEW
        self.cache_size_spin = None
        self.cache_size_label = None # <-- NEW

        # Account Page Widgets
        self.username_edit = None
        self.username_label = None # <-- NEW
        self.api_key_edit = None
        self.api_key_label = None # <-- NEW
        self.clear_cache_button = None

        # About Page Widgets
        self.about_title_label = None
        self.about_version_label = None
        self.about_desc_label = None
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(900, 600)
        
        # Build UI first, which initializes all widget attributes
        self._build_ui() 
        
        # Set initial text via the i18n method
        self.retranslateUi()
        
        # Load all saved values into the UI controls
        self._load_settings()
        
        QTimer.singleShot(30, self._apply_mask)

    # -----------------------------------------------------------
    # NEW: changeEvent and retranslateUi for i18n
    # -----------------------------------------------------------
    def changeEvent(self, event: QEvent):
        """Triggers retranslation on language change events."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)
        
    def retranslateUi(self):
        """Updates all translatable text in the window."""
        # 1. Top Bar
        self.title_text_label.setText(QCoreApplication.translate("SettingsWidget", "Settings"))
        
        # 2. Sidebar Buttons
        options = [
            QCoreApplication.translate("SettingsWidget", "General"),
            QCoreApplication.translate("SettingsWidget", "Preferences"),
            QCoreApplication.translate("SettingsWidget", "Account"),
            QCoreApplication.translate("SettingsWidget", "About")
        ]
        for i, text in enumerate(options):
            if i < len(self.sidebar_buttons):
                self.sidebar_buttons[i].setText(text)
        
        # 3. General Page Labels & Placeholders
        if self.language_label:
            self.language_label.setText(QCoreApplication.translate("SettingsWidget", "Language:"))
            self.log_level_label.setText(QCoreApplication.translate("SettingsWidget", "Logging Level:"))
            self.log_path_label.setText(QCoreApplication.translate("SettingsWidget", "Log File Path:"))
            
            # Update Comboboxes (Requires care to preserve selected item)
            
            # Language Combo
            self.language_combo.blockSignals(True)
            current_lang = self.language_combo.currentText()
            self.language_combo.clear()
            self.language_combo.addItems([
                QCoreApplication.translate("SettingsWidget", "English (US)"),
                QCoreApplication.translate("SettingsWidget", "Français"),
                QCoreApplication.translate("SettingsWidget", "Español"),
                QCoreApplication.translate("SettingsWidget", "Deutsch"), # German
                QCoreApplication.translate("SettingsWidget", "العربية")  #
            ])
            # Restore selection based on translated string
            index = self.language_combo.findText(current_lang) 
            if index != -1: self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)
            
            # Log Level Combo
            self.log_level_combo.blockSignals(True)
            current_level = self.log_level_combo.currentText()
            self.log_level_combo.clear()
            self.log_level_combo.addItems([
                QCoreApplication.translate("SettingsWidget", "DEBUG"),
                QCoreApplication.translate("SettingsWidget", "INFO"),
                QCoreApplication.translate("SettingsWidget", "WARNING"),
                QCoreApplication.translate("SettingsWidget", "ERROR")
            ])
            index = self.log_level_combo.findText(current_level)
            if index != -1: self.log_level_combo.setCurrentIndex(index)
            self.log_level_combo.blockSignals(False)

            self.log_path_edit.setPlaceholderText(QCoreApplication.translate("SettingsWidget", "e.g., C:/Users/YourUser/app.log"))
            self.updates_check.setText(QCoreApplication.translate("SettingsWidget", "Check for updates automatically"))
            
        # 4. Preferences Page Labels & Placeholders
        if self.theme_label:
            self.theme_label.setText(QCoreApplication.translate("SettingsWidget", "Application Theme:"))
            self.default_style_label.setText(QCoreApplication.translate("SettingsWidget", "Default Molecule Style:"))
            self.docking_precision_label.setText(QCoreApplication.translate("SettingsWidget", "Docking Precision:"))
            self.cache_size_label.setText(QCoreApplication.translate("SettingsWidget", "Max Cache Size:"))
            
            # Theme Combo
            self.theme_combo.blockSignals(True)
            current_theme = self.theme_combo.currentText()
            self.theme_combo.clear()
            self.theme_combo.addItems([
                QCoreApplication.translate("SettingsWidget", "Light"),
                QCoreApplication.translate("SettingsWidget", "Dark"),
                QCoreApplication.translate("SettingsWidget", "System Default")
            ])
            index = self.theme_combo.findText(current_theme)
            if index != -1: self.theme_combo.setCurrentIndex(index)
            self.theme_combo.blockSignals(False)
            
            # Tooltips GroupBox title
            self.tooltips_group.setTitle(QCoreApplication.translate("SettingsWidget", "Module Tooltips"))
            
            # Tooltip Checkbox Labels
            self.tooltips_viewers_label.setText(QCoreApplication.translate("SettingsWidget", "Detector Modules (Lung/Breast/Brain):"))
            self.tooltips_docking_label.setText(QCoreApplication.translate("SettingsWidget", "Molecular Docking Station:"))
            self.tooltips_settings_label.setText(QCoreApplication.translate("SettingsWidget", "Settings Window Elements:"))

            # Default Style Combo
            self.default_style_combo.blockSignals(True)
            current_style = self.default_style_combo.currentText()
            self.default_style_combo.clear()
            self.default_style_combo.addItems([
                QCoreApplication.translate("SettingsWidget", "Cartoon"),
                QCoreApplication.translate("SettingsWidget", "Stick"),
                QCoreApplication.translate("SettingsWidget", "Sphere"),
                QCoreApplication.translate("SettingsWidget", "Line")
            ])
            index = self.default_style_combo.findText(current_style)
            if index != -1: self.default_style_combo.setCurrentIndex(index)
            self.default_style_combo.blockSignals(False)

            self.cache_size_spin.setSuffix(QCoreApplication.translate("SettingsWidget", " MB"))

        # 5. Account Page Labels & Placeholders
        if self.username_label:
            self.username_label.setText(QCoreApplication.translate("SettingsWidget", "Username:"))
            self.api_key_label.setText(QCoreApplication.translate("SettingsWidget", "API Key:"))
            self.username_edit.setPlaceholderText(QCoreApplication.translate("SettingsWidget", "Enter your username"))
            self.api_key_edit.setPlaceholderText(QCoreApplication.translate("SettingsWidget", "Enter your PDB/API key"))
            self.clear_cache_button.setText(QCoreApplication.translate("SettingsWidget", "Clear Local Cache"))

        # 6. About Page Labels
        if self.about_title_label:
            self.about_title_label.setText(QCoreApplication.translate("SettingsWidget", "Cancer Research Application Suite"))
            self.about_version_label.setText(QCoreApplication.translate("SettingsWidget", "Version 1.0.0 (Alpha)"))
            self.about_desc_label.setText(QCoreApplication.translate(
                "SettingsWidget",
                "OncoDock is a cancer research application suite designed for molecular docking "
                "and AI-powered cancer detection. Developed by Razeen, Arjun, Nilay and Sinan.\n\n"
                "This software is provided 'as is' without warranty of any kind."
            ))
            
        # 7. Apply new tooltips (which are also translated strings)
        tooltips_enabled = self.tooltips_settings_check.isChecked() if self.tooltips_settings_check else True
        self._apply_settings_tooltips(tooltips_enabled)

    # -----------------------------------------------------------
    # MODIFIED: _build_ui (Use dedicated attributes, no translation calls)
    # -----------------------------------------------------------
    def _build_ui(self):
        # The main layout for the transparent QDialog
        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 2, 2, 2)
        outer.setSpacing(0)

        # A single background widget
        background_widget = QWidget(self)
        background_widget.setObjectName("background_widget")
        outer.addWidget(background_widget)

        container_layout = QVBoxLayout(background_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # --- Top Bar (Draggable Area) ---
        top_bar = QWidget(self)
        top_bar.setFixedHeight(50)
        top_bar.setObjectName("settings_topbar")
        tlayout = QHBoxLayout(top_bar)
        tlayout.setContentsMargins(12, 0, 12, 0)

        self.close_btn = QPushButton(parent=top_bar)
        self.close_btn.setFixedSize(14, 14)
        self.close_btn.setStyleSheet("QPushButton { border-radius: 7px; background: #FF5F56; } QPushButton:hover { background: #ff7b73; }")
        self.close_btn.clicked.connect(self.close)
        tlayout.addWidget(self.close_btn)

        # Title with Icon
        tlayout.addStretch()
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        self.title_icon_label = QLabel()
        self.title_icon_label.setFixedSize(20, 20)
        self.title_text_label = QLabel() # Use attribute
        self.title_text_label.setObjectName("settings_title")
        title_layout.addWidget(self.title_icon_label)
        title_layout.addWidget(self.title_text_label)
        tlayout.addLayout(title_layout)
        tlayout.addStretch()
        container_layout.addWidget(top_bar)

        # --- Content Area (Sidebar + Main Panel) ---
        content = QWidget(self)
        content.setObjectName("content_area")
        cl = QHBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Sidebar with Navigation Buttons
        self.sidebar = QWidget(content)
        self.sidebar.setFixedWidth(220)
        self.sidebar.setObjectName("settings_sidebar")
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(10, 10, 10, 10)
        sb_layout.setSpacing(8)
        sb_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.sidebar_buttons = []

        # Create buttons with empty text, which will be set in retranslateUi
        for i in range(4):
            btn = QPushButton()
            btn.setObjectName("sidebar_button")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, index=i: self._change_page(index))
            sb_layout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        sb_layout.addStretch()

        # Main Panel with Stacked Pages
        self.main_panel = QStackedWidget(content)
        self.main_panel.setObjectName("main_panel")
        
        # --- Create functional pages ---
        self.main_panel.addWidget(self._create_general_page())
        self.main_panel.addWidget(self._create_preferences_page())
        self.main_panel.addWidget(self._create_account_page())
        self.main_panel.addWidget(self._create_about_page())

        cl.addWidget(self.sidebar)
        cl.addWidget(self.main_panel, 1)
        container_layout.addWidget(content, 1)

        self._top_bar = top_bar
        self._apply_styles()
        self._change_page(0)# Set initial page
        
    # -----------------------------------------------------------
    # CORRECTED: _create_general_page 
    # The fix is ensuring the created QLabel is used in addRow.
    # -----------------------------------------------------------
    def _create_general_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 1. Language
        self.language_combo = QComboBox()
        self.language_combo.setEnabled(True) 
        self.language_combo.currentTextChanged.connect(self._on_language_change_and_emit)
        self.language_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.language_label, self.language_combo) # <--- FIXED: Now adds the label!
        
        # 2. Log Level
        self.log_level_combo = QComboBox()
        self.log_level_combo.currentTextChanged.connect(self._on_log_level_change)
        self.log_level_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.log_level_label, self.log_level_combo) # <--- FIXED: Now adds the label!

        # 3. Log Path
        self.log_path_edit = QLineEdit()
        self.log_path_edit.textChanged.connect(self._on_log_path_change)
        self.log_path_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.log_path_label, self.log_path_edit) # <--- FIXED: Now adds the label!

        # 4. Updates Check
        self.updates_check = QCheckBox() # Text set in retranslateUi
        self.updates_check.toggled.connect(self._on_updates_check_change)
        layout.addRow(QLabel(), self.updates_check) # Use an empty QLabel for alignment

        layout.setVerticalSpacing(20)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        return page

    # -----------------------------------------------------------
    # CORRECTED: _create_preferences_page 
    # The fix is ensuring the created QLabel is used in addRow.
    # -----------------------------------------------------------
    def _create_preferences_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 1. Theme Switcher
        self.theme_combo = QComboBox()
        self.theme_combo.currentTextChanged.connect(self._on_theme_change)
        self.theme_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.theme_label, self.theme_combo) # <--- FIXED: Now adds the label!

        # --- Tooltips Group ---
        self.tooltips_group = QGroupBox() # Title set in retranslateUi
        tooltips_layout = QFormLayout(self.tooltips_group)
        tooltips_layout.setContentsMargins(10, 15, 10, 10)
        tooltips_layout.setSpacing(10)
        tooltips_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Viewer Tooltips (Breast, Lung, Brain)
        self.tooltips_viewers_check = QCheckBox()
        self.tooltips_viewers_check.toggled.connect(
            lambda state: self._on_specific_tooltip_change("tooltips/Detectors", state)
        )
        self.tooltips_viewers_label = QLabel() # Text set in retranslateUi
        tooltips_layout.addRow(self.tooltips_viewers_label, self.tooltips_viewers_check) # <--- FIXED

        # Docking Tooltips
        self.tooltips_docking_check = QCheckBox()
        self.tooltips_docking_check.toggled.connect(
            lambda state: self._on_specific_tooltip_change("tooltips/Docking", state)
        )
        self.tooltips_docking_label = QLabel() # Text set in retranslateUi
        tooltips_layout.addRow(self.tooltips_docking_label, self.tooltips_docking_check) # <--- FIXED

        # Settings Window Tooltips
        self.tooltips_settings_check = QCheckBox()
        self.tooltips_settings_check.toggled.connect(
            lambda state: self._on_specific_tooltip_change("tooltips/SettingsWindow", state)
        )
        self.tooltips_settings_label = QLabel() # Text set in retranslateUi
        tooltips_layout.addRow(self.tooltips_settings_label, self.tooltips_settings_check) # <--- FIXED
        
        layout.addRow(self.tooltips_group)
        # --- End Tooltips Group ---
        
        # 3. Default Molecule Style
        self.default_style_combo = QComboBox()
        self.default_style_combo.currentTextChanged.connect(self._on_default_style_change)
        self.default_style_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.default_style_label, self.default_style_combo) # <--- FIXED: Now adds the label!

        # 4. Docking Precision
        self.docking_precision_slider = QSlider(Qt.Orientation.Horizontal)
        self.docking_precision_slider.setRange(1, 100)
        self.docking_precision_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.docking_precision_slider.valueChanged.connect(self._on_docking_precision_change)
        self.docking_precision_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.docking_precision_label, self.docking_precision_slider) # <--- FIXED: Now adds the label!
        
        # 5. Cache Size
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 5000) 
        self.cache_size_spin.valueChanged.connect(self._on_cache_size_change)
        self.cache_size_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.cache_size_label, self.cache_size_spin) # <--- FIXED: Now adds the label!

        layout.setVerticalSpacing(20)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        return page
        
    # -----------------------------------------------------------
    # CORRECTED: _create_account_page
    # The fix is ensuring the created QLabel is used in addRow.
    # -----------------------------------------------------------
    def _create_account_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 1. Username
        self.username_edit = QLineEdit()
        self.username_edit.textChanged.connect(self._on_username_change)
        self.username_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.username_label, self.username_edit) # <--- FIXED: Now adds the label!

        # 2. API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.textChanged.connect(self._on_api_key_change)
        self.api_key_label = QLabel() # Text set in retranslateUi
        layout.addRow(self.api_key_label, self.api_key_edit) # <--- FIXED: Now adds the label!
        
        # 3. Clear Cache
        self.clear_cache_button = QPushButton() # Text set in retranslateUi
        self.clear_cache_button.setDisabled(True) 
        layout.addRow(QLabel(), self.clear_cache_button) # Use an empty QLabel for alignment
        
        layout.setVerticalSpacing(20)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        return page

    # -----------------------------------------------------------
    # Unchanged or minor parts below for context completeness
    # -----------------------------------------------------------
    def _create_about_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.about_title_label = QLabel() # Text set in retranslateUi
        self.about_title_label.setObjectName("settings_title") 
        self.about_title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.about_title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        
        self.about_version_label = QLabel() # Text set in retranslateUi
        self.about_version_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.about_version_label.setStyleSheet("font-size: 14px; color: #888;")
        
        self.about_desc_label = QLabel() # Text set in retranslateUi
        self.about_desc_label.setWordWrap(True)
        self.about_desc_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.about_desc_label.setStyleSheet("font-size: 14px; padding-top: 20px;")
        
        layout.addWidget(self.about_title_label)
        layout.addWidget(self.about_version_label)
        layout.addSpacing(20)
        layout.addWidget(self.about_desc_label)
        layout.addStretch()
        
        return page

    def _on_language_change_and_emit(self, text):
        """Saves the language setting and emits the language_changed signal."""
        if not text:
            return
        self.settings.setValue("general/language", text)
        # Emit the signal so the main application can react and reload translator
        self.language_changed.emit(text)

    # ... (Rest of the methods like _load_settings, _apply_styles, _on_*_change are unchanged from your last valid code block, but are included below for completeness.)

    def _load_settings(self):
        # --- General Tab ---
        # Load language setting
        language = self.settings.value("general/language", "English (US)")
        # Block signals during load to prevent premature signal emission
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentText(language)
        self.language_combo.blockSignals(False)

        log_level = self.settings.value("general/log_level", "INFO")
        self.log_level_combo.blockSignals(True)
        self.log_level_combo.setCurrentText(log_level)
        self.log_level_combo.blockSignals(False)
        
        log_path = self.settings.value("general/log_path", "")
        self.log_path_edit.setText(log_path)
        
        updates = self.settings.value("general/updates", True, type=bool)
        self.updates_check.setChecked(updates)
        
        # --- Preferences Tab ---
        theme_value = self.settings.value("theme", "system_default")
        self.set_theme_combo_index(theme_value)
        
        # Load individual tooltip settings
        viewers_tooltips = self.settings.value("tooltips/Detectors", True, type=bool)
        self.tooltips_viewers_check.setChecked(viewers_tooltips)
        
        docking_tooltips = self.settings.value("tooltips/Docking", True, type=bool)
        self.tooltips_docking_check.setChecked(docking_tooltips)

        settings_tooltips = self.settings.value("tooltips/SettingsWindow", True, type=bool)
        self.tooltips_settings_check.setChecked(settings_tooltips)
        
        # Apply tooltips to the settings window controls immediately upon loading
        self._apply_settings_tooltips(settings_tooltips)
        
        default_style = self.settings.value("prefs/default_style", "Cartoon")
        self.default_style_combo.blockSignals(True)
        self.default_style_combo.setCurrentText(default_style)
        self.default_style_combo.blockSignals(False)
        
        docking_precision = self.settings.value("prefs/docking_precision", 50, type=int)
        self.docking_precision_slider.setValue(docking_precision)
        
        cache_size = self.settings.value("prefs/cache_size", 1000, type=int)
        self.cache_size_spin.setValue(cache_size)
        
        # --- Account Tab ---
        username = self.settings.value("account/username", "")
        self.username_edit.setText(username)
        
        api_key = self.settings.value("account/api_key", "")
        self.api_key_edit.setText(api_key)

    def set_theme_combo_index(self, theme_value: str):
        """Sets the QComboBox index without triggering the signal."""
        
        # Temporarily block signals to prevent a recursive call to _on_theme_change
        self.theme_combo.blockSignals(True) 
        
        # Translate theme values for internal comparison
        light_t = QCoreApplication.translate("SettingsWidget", "Light").lower().replace(" ", "_")
        dark_t = QCoreApplication.translate("SettingsWidget", "Dark").lower().replace(" ", "_")
        system_t = QCoreApplication.translate("SettingsWidget", "System Default").lower().replace(" ", "_")

        # NOTE: This logic assumes that "Light" is index 0, "Dark" is 1, etc., after retranslateUi()
        if theme_value.lower().replace(" ", "_") == light_t:
            self.theme_combo.setCurrentIndex(0)
        elif theme_value.lower().replace(" ", "_") == dark_t:
            self.theme_combo.setCurrentIndex(1)
        elif theme_value.lower().replace(" ", "_") == system_t:
            self.theme_combo.setCurrentIndex(2)
        
        # Re-enable signals
        self.theme_combo.blockSignals(False)
        
    # --- Live-update slots (emit signals) ---
    def _on_theme_change(self, theme_text):
        if not theme_text: 
            return
        theme_value = theme_text.lower().replace(" ", "_")
        self.settings.setValue("theme", theme_value)
        self.theme_changed.emit(theme_value)

    # --- NEW: Unified slot for specific tooltip changes ---
    def _on_specific_tooltip_change(self, key: str, enabled: bool):
        self.settings.setValue(key, enabled)
        # Apply tooltips for the settings window immediately
        if key == "tooltips/SettingsWindow":
            self._apply_settings_tooltips(enabled)
            
        # Emit the specific key and state so MainWindow knows what to update
        self.tooltips_changed.emit(key, enabled)

    def _apply_settings_tooltips(self, enabled: bool):
        """Applies or removes tooltips from the SettingsWindow's internal controls."""
        
        # Only create the map if widgets are initialized (e.g., after _build_ui)
        if not self.close_btn or not self.sidebar_buttons: # Check if essential widgets exist
             return

        tooltip_map = {
            self.close_btn: QCoreApplication.translate("SettingsWidget", "Close the settings window."),
            # Sidebar
            self.sidebar_buttons[0]: QCoreApplication.translate("SettingsWidget", "Settings related to application core functionality (Language, Logging)."),
            self.sidebar_buttons[1]: QCoreApplication.translate("SettingsWidget", "Settings related to user experience (Theme, Tooltips, Display Style)."),
            self.sidebar_buttons[2]: QCoreApplication.translate("SettingsWidget", "Settings related to user account (Username, API Key, Cache)."),
            self.sidebar_buttons[3]: QCoreApplication.translate("SettingsWidget", "Information about the application and version details."),
            # General Page controls
            self.language_combo: QCoreApplication.translate("SettingsWidget", "The language used for application text (Requires restart to fully apply)."),
            self.log_level_combo: QCoreApplication.translate("SettingsWidget", "Set the minimum severity level for messages written to the log file."),
            self.log_path_edit: QCoreApplication.translate("SettingsWidget", "Specify the file path where application logs should be saved."),
            self.updates_check: QCoreApplication.translate("SettingsWidget", "Enable or disable automatic checks for new application versions."),
            # Preferences Page controls
            self.theme_combo: QCoreApplication.translate("SettingsWidget", "Select the visual theme for the application (Light, Dark, System Default)."),
            self.tooltips_viewers_check: QCoreApplication.translate("SettingsWidget", "Enable/disable contextual help for Breast, Lung, and Brain Viewer modules."),
            self.tooltips_docking_check: QCoreApplication.translate("SettingsWidget", "Enable/disable contextual help for the Molecular Docking Station."),
            self.tooltips_settings_check: QCoreApplication.translate("SettingsWidget", "Enable/disable contextual help for all elements within this Settings window."),
            self.default_style_combo: QCoreApplication.translate("SettingsWidget", "Set the default rendering style for molecules in the viewer."),
            self.docking_precision_slider: QCoreApplication.translate("SettingsWidget", "Adjust the resolution/detail level for molecular docking calculations (Higher = Slower, more precise)."),
            self.cache_size_spin: QCoreApplication.translate("SettingsWidget", "Define the maximum size of the local cache for downloaded molecular data."),
            # Account Page controls
            self.username_edit: QCoreApplication.translate("SettingsWidget", "Your registered username for cloud services."),
            self.api_key_edit: QCoreApplication.translate("SettingsWidget", "The API key required for accessing external data sources."),
            self.clear_cache_button: QCoreApplication.translate("SettingsWidget", "Deletes all temporary downloaded molecular data."),
        }

        tooltip_text = lambda tip: tip if enabled else ""

        for widget, tip in tooltip_map.items():
            if widget:
                widget.setToolTip(tooltip_text(tip))
    # --- Simple save-only slots ---
    # NOTE: The original _on_language_change has been replaced by _on_language_change_and_emit
    # The following slots simply save the value without needing to emit a signal.

    def _on_log_level_change(self, text):
        self.settings.setValue("general/log_level", text)

    def _on_log_path_change(self, text):
        self.settings.setValue("general/log_path", text)

    def _on_updates_check_change(self, state):
        self.settings.setValue("general/updates", bool(state))
        
    def _on_default_style_change(self, text):
        self.settings.setValue("prefs/default_style", text)
        
    def _on_docking_precision_change(self, value):
        self.settings.setValue("prefs/docking_precision", value)

    def _on_cache_size_change(self, value):
        self.settings.setValue("prefs/cache_size", value)

    def _on_username_change(self, text):
        self.settings.setValue("account/username", text)

    def _on_api_key_change(self, text):
        self.settings.setValue("account/api_key", text)

    # --- Internal Class Methods (Unchanged) ---
    def _change_page(self, index):
        self.main_panel.setCurrentIndex(index)
        for i, button in enumerate(self.sidebar_buttons):
            is_active = (i == index)
            button.setProperty("active", "true" if is_active else "false")
            button.style().unpolish(button)
            button.style().polish(button)

    # NOTE: _apply_styles method is long but preserved as-is since it contains styling logic
    def _apply_styles(self):
        if self.theme == 'dark':
            glass_bg = "rgba(40, 40, 40, 150)"
            glass_bg_disabled = "rgba(40, 40, 40, 90)" 
            content_bg = "#1E1E1E"
            btn_hover_bg = "rgba(255, 255, 255, 20)"
            btn_active_bg = "#007AFF"
            border_color = "rgba(255, 255, 255, 20)"
            window_border = QColor(255, 255, 255)
            text_color = "#EAEAEA"
            active_text_color = "#FFFFFF"
        else:
            glass_bg = "rgba(255, 255, 255, 180)"
            glass_bg_disabled = "rgba(255, 255, 255, 120)" 
            content_bg = "#F5F5F5"
            btn_hover_bg = "rgba(0, 0, 0, 10)"
            btn_active_bg = "#007AFF"
            border_color = "rgba(0,0,0,12)"
            window_border = QColor(0, 0, 0)
            text_color = "#333333"
            active_text_color = "#FFFFFF"

        self._border_color = window_border
        self._title_color = text_color
        
        self.findChild(QWidget, "background_widget").setStyleSheet("background-color: transparent;")
        self.findChild(QWidget, "content_area").setStyleSheet("background: transparent;")
        
        icon_path = "assets/settings_dark.png" if self.theme == 'dark' else "assets/settings_light.png"
        icon = QIcon(icon_path)
        self.title_icon_label.setPixmap(icon.pixmap(20, 20) if icon.availableSizes() else QPixmap(20, 20))
        
        self._top_bar.setStyleSheet(f"""
            QWidget#settings_topbar {{
                background: {glass_bg};
                border-bottom: 1px solid {border_color};
                border-top-left-radius: {self.corner_radius}px;
                border-top-right-radius: {self.corner_radius}px;
            }}
        """)
        self.findChild(QLabel, "settings_title").setStyleSheet(f"color: {self._title_color}; font-size: 16px; font-weight: 600; background: transparent;")

        self.sidebar.setStyleSheet(f"""
            QWidget#settings_sidebar {{
                background: {glass_bg};
                border-right: 1px solid {border_color};
                border-bottom-left-radius: {self.corner_radius}px;
            }}
            QPushButton#sidebar_button {{
                color: {text_color};
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 10px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton#sidebar_button:hover {{
                background-color: {btn_hover_bg};
            }}
            QPushButton#sidebar_button[active="true"] {{
                background-color: {btn_active_bg};
                color: {active_text_color};
            }}
        """)

        # --- MODIFIED: Apply styles to new form elements ---
        self.main_panel.setStyleSheet(f"""
            QStackedWidget#main_panel {{
                background: {content_bg};
                border-bottom-right-radius: {self.corner_radius}px;
            }}
            QStackedWidget#main_panel > QWidget {{
                background: transparent;
            }}
            /* All labels inside the panel (including placeholders) */
            QStackedWidget#main_panel QLabel {{
                color: {text_color};
                background: transparent;
                padding: 0px;
                font-size: 14px;
            }}
            /* Styles for QGroupBox title (for the new Tooltips section) */
            QGroupBox {{
                color: {text_color};
                font-size: 16px;
                font-weight: 600;
                margin-top: 10px;
                border: 1px solid {border_color};
                border-radius: 8px;
                padding-top: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left; /* Position at top center */
                padding: 0 3px;
                left: 10px;
                color: {text_color};
                font-weight: bold;
            }}
            /* Placeholder title labels in "About" */
            QStackedWidget#main_panel QLabel[alignment="AlignCenter"] {{
                 font-size: 14px;
                 padding: 0px;
            }}
            QStackedWidget#main_panel QCheckBox {{
                color: {text_color};
                font-size: 14px;
            }}
            
            /* --- Style QComboBox --- */
            QStackedWidget#main_panel QComboBox {{
                color: {text_color};
                background-color: {glass_bg};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
            }}
            
            /* --- Style for DISABLED ComboBox --- */
            QStackedWidget#main_panel QComboBox:disabled {{
                color: {text_color}80; /* 50% opacity text */
                background-color: {glass_bg_disabled}; /* Use new disabled bg */
                border: 1px solid {border_color}80; /* 50% opacity border */
            }}
            
            QStackedWidget#main_panel QComboBox::drop-down {{
                border: none;
            }}
            
            /* --- Style the ComboBox Dropdown List --- */
            QComboBox QAbstractItemView {{
                background-color: {content_bg}; /* Solid bg for dropdown */
                border: 1px solid {border_color};
                color: {text_color};
                selection-background-color: {btn_active_bg};
                padding: 4px;
            }}

            /* --- Style QLineEdit & QSpinBox --- */
            QStackedWidget#main_panel QLineEdit,
            QStackedWidget#main_panel QSpinBox {{
                color: {text_color};
                background-color: {glass_bg};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
            }}
            QStackedWidget#main_panel QSpinBox::up-button,
            QStackedWidget#main_panel QSpinBox::down-button {{
                border: none;
                background-color: transparent;
                color: {text_color};
            }}
            QStackedWidget#main_panel QSpinBox::up-arrow {{
                color: {text_color};
            }}
            QStackedWidget#main_panel QSpinBox::down-arrow {{
                color: {text_color};
            }}

            /* --- Style QSlider --- */
            QStackedWidget#main_panel QSlider::groove:horizontal {{
                border: 1px solid transparent;
                height: 4px; 
                background: {glass_bg};
                margin: 2px 0;
                border-radius: 2px;
            }}
            QStackedWidget#main_panel QSlider::handle:horizontal {{
                background: {text_color};
                border: 1px solid {text_color};
                width: 14px;
                height: 14px;
                margin: -6px 0; 
                border-radius: 7px;
            }}
            QStackedWidget#main_panel QSlider::add-page:horizontal {{
                background: {glass_bg};
            }}
            QStackedWidget#main_panel QSlider::sub-page:horizontal {{
                background: {btn_active_bg};
            }}
            
            /* --- Style Placeholder QPushButton --- */
            QStackedWidget#main_panel QPushButton {{
                color: {active_text_color};
                background-color: {btn_active_bg};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QStackedWidget#main_panel QPushButton:hover {{
                background-color: {btn_hover_bg};
            }}
            QStackedWidget#main_panel QPushButton:disabled {{
                background-color: {glass_bg}80;
                color: {text_color}80;
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
        pen_width = 2.0 
        pen = QPen(self._border_color)
        pen.setWidthF(pen_width)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inset = pen_width / 2.0
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        path = QPainterPath()
        path.addRoundedRect(rect, float(self.corner_radius), float(self.corner_radius))
        painter.translate(0.5, 0.5)
        painter.drawPath(path)
        painter.end()


    def _apply_mask(self):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), float(self.corner_radius), float(self.corner_radius))
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._top_bar.geometry().contains(event.position().toPoint()):
            if not isinstance(self.childAt(event.position().toPoint()), QPushButton):
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        super().mouseReleaseEvent(event)

    def update_theme(self, dark_mode: bool):
        self.theme = 'dark' if dark_mode else 'light'
        self._apply_styles()
        self.update()
        theme_value = self.settings.value("theme", "system_default")
        self.set_theme_combo_index(theme_value)
# ==========================================================
# MODIFIED: Main Application Window
# ==========================================================
# custom_title_bar.py

class CustomTitleBar(QWidget):
    """
    A custom title bar widget that provides macOS-style window controls
    and allows the frameless window to be dragged.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.drag_position = None

        self.setAutoFillBackground(True)
        self.setFixedHeight(35)

        self.maximize_timer = QTimer(self)
        self.maximize_timer.setSingleShot(True)
        self.maximize_timer.setInterval(300)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(8)

        # --- MODIFICATION 1: Create the label without initial text ---
        self.close_button = QPushButton()
        self.minimize_button = QPushButton()
        self.maximize_button = QPushButton()
        
        self.close_button.setObjectName("closeButton")
        self.minimize_button.setObjectName("minimizeButton")
        self.maximize_button.setObjectName("maximizeButton")
        
        for btn in [self.close_button, self.minimize_button, self.maximize_button]:
            btn.setFixedSize(12, 12)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Create the label empty. Its text will be set by retranslateUi.
        self.title_label = QLabel() 
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.close_button)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        self.close_button.clicked.connect(self.parent_window.close)
        self.minimize_button.clicked.connect(self.parent_window.showMinimized)
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)
        
        self.setLayout(layout)
        
        # --- MODIFICATION 3: Call retranslateUi to set initial text ---
        self.retranslateUi()
        self.update_theme(False)

    # --- NEW METHOD ---
    def retranslateUi(self):
        """
        Updates the translatable text for this custom title bar.
        This will be called by the MainWindow whenever the language changes.
        """
        title_text = QCoreApplication.translate("MainWindow", "OncoDock - Cancer Research Application Suite")
        self.title_label.setText(title_text)

    # --- No changes needed for the rest of the file ---
    def toggle_maximize_restore(self):
        if self.maximize_timer.isActive():
            return
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()
        self.maximize_timer.start()

    def update_theme(self, is_dark_mode: bool):
        bg_color = "#2E2E2E" if is_dark_mode else "#f0f0f0"
        text_color = "white" if is_dark_mode else "black"
        stylesheet = f"""
            CustomTitleBar {{ background-color: {bg_color}; }}
            QLabel {{ color: {text_color}; font-size: 14px; font-weight: bold; }}
            #closeButton {{ background-color: #FF5F57; border-radius: 6px; border: none; }}
            #closeButton:hover {{ background-color: #E0443E; }}
            #minimizeButton {{ background-color: #FFBD2E; border-radius: 6px; border: none; }}
            #minimizeButton:hover {{ background-color: #E0A328; }}
            #maximizeButton {{ background-color: #27C93F; border-radius: 6px; border: none; }}
            #maximizeButton:hover {{ background-color: #1AA62C; }}
        """
        self.setStyleSheet(stylesheet)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_position is not None and event.buttons() == Qt.MouseButton.LeftButton:
            if self.parent_window.isMaximized():
                self.toggle_maximize_restore()
                self.drag_position = QPoint(self.width() // 2, 15) 
                return
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_position = None
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize_restore()
            event.accept()

class MainWindow(QMainWindow):
    def __init__(self,language_manager: LanguageManager, parent=None):
        super().__init__()
        self.settings_window_instance = None 
        self.language_manager = language_manager
        # --- NEW: Make the window frameless ---
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.CustomizeWindowHint # Optional, but often used for cleaner layering
        )
        
        # Initial call to set the window title (will be updated by retranslateUi later)
        self.setWindowTitle(QCoreApplication.translate("MainWindow", "OncoDock - Cancer Research Application Suite"))

        self.setGeometry(50, 50, 1200, 750)
        self.center_window()
        
        settings_path = Path(__file__).parent / "settings.ini"
        self.settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
        self.is_dark_mode = False
        icon_path = Path(__file__).parent / "assets" / "OncoDock.ico" # Or .ico
        self.setWindowIcon(QIcon(str(icon_path)))
        # --- REMOVED THE REDUNDANT INSTANCE HERE ---
        # self.settings_window = SettingsWindow(self) 
        # self.settings_window.theme_changed.connect(self.on_theme_setting_changed)
        # self.settings_window.tooltips_changed.connect(self.on_tooltips_setting_changed)
        
        self.initUI()
        self.restore_state() 
        
        if QApplication.instance():
            QApplication.instance().aboutToQuit.connect(self.save_state)
        # Keep this variable to manage the single live instance
        
    def center_window(self):
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())
        
    def initUI(self):
        # --- NEW: Create a root structure for the frameless window ---
        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- NEW: Instantiate and add our custom title bar ---
        self.title_bar = CustomTitleBar(self)
        root_layout.addWidget(self.title_bar)

        # --- MODIFIED: The rest of your UI is placed in a "content_area" widget ---
        content_area = QWidget()
        main_layout = QVBoxLayout(content_area)
        main_layout.setContentsMargins(10, 10, 10, 10) # Your original margins
        main_layout.setSpacing(5)
        
        # This part is your original top bar layout
        top_bar_layout = QHBoxLayout()
        
        self.molecular_docking_button = QPushButton() # Text set in retranslateUi
        self.cancer_detection_button = QPushButton()  # Text set in retranslateUi

        self.buttons = [self.molecular_docking_button, self.cancer_detection_button]
        top_bar_layout.addWidget(self.molecular_docking_button)
        top_bar_layout.addWidget(self.cancer_detection_button)
        top_bar_layout.addStretch()
        
        self.toggle = GradientToggle(callback=self.changeTheme)
        top_bar_layout.addWidget(self.toggle)
        
        self.settings_button = QPushButton()
        self.settings_button.setFlat(True)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.setFixedSize(28, 28)
        self.settings_button.setIconSize(QSize(20, 20))
        self.settings_button.clicked.connect(self.open_settings)
        top_bar_layout.addWidget(self.settings_button)
        main_layout.addLayout(top_bar_layout)
        
        # Your original content stack remains the same
        self.content_stack = QStackedWidget()
        self.molecular_docking_widget = create_molecular_docking_tab()
        self.cancer_detection_widget = create_cancer_detection_tab()
        self.content_stack.addWidget(self.molecular_docking_widget)
        self.content_stack.addWidget(self.cancer_detection_widget)
        main_layout.addWidget(self.content_stack)

        self.molecular_docking_button.clicked.connect(lambda: self.switchContent(0))
        self.cancer_detection_button.clicked.connect(lambda: self.switchContent(1))

        # --- NEW: Add the content area below the title bar and set the central widget ---
        root_layout.addWidget(content_area)
        self.setCentralWidget(root_widget)
        
        # Set initial text/tooltips
        self.retranslateUi()

    def open_settings(self):
        """Creates and shows the settings window, and ensures ALL signals are connected."""
        if self.settings_window_instance is None:
            # 1. Create the ONE and ONLY instance of SettingsWindow
            self.settings_window_instance = SettingsWindow(parent=self)
            
            # 2. --- NOW CONNECT ALL THE SIGNALS TO THIS LIVE INSTANCE ---
            
            # THEME and TOOLTIPS were missing connections before
            self.settings_window_instance.theme_changed.connect(
                self.on_theme_setting_changed
            )
            self.settings_window_instance.tooltips_changed.connect(
                self.on_tooltips_setting_changed
            )
            
            # Language was already connected here, which is why it likely worked
            self.settings_window_instance.language_changed.connect(
                self.handle_language_change
            )
            
            # Clean up the reference when the window is closed
            self.settings_window_instance.finished.connect(
                lambda: setattr(self, 'settings_window_instance', None)
            )

        self.settings_window_instance.show()
        self.settings_window_instance.activateWindow()

    # --- NEW METHOD: Centralized re-translation logic ---
    def retranslateUi(self):
        """
        Updates ALL translatable texts in MainWindow in real time 
        after a language change.
        """
        # 1. Window Title (for the OS)
        self.setWindowTitle(QCoreApplication.translate("MainWindow", "OncoDock - Cancer Research Application Suite"))
        
        # --- ADD THIS LINE ---
        if self.title_bar:
            self.title_bar.retranslateUi()
        # ---------------------
        
        # 2. Main Tab Buttons
        self.molecular_docking_button.setText(
            QCoreApplication.translate("MainWindow", "Molecular Docking")
        )
        self.cancer_detection_button.setText(
            QCoreApplication.translate("MainWindow", "Cancer Detection")
        )

        # 3. Inner Tab Titles
        # ... (the rest of your function is already correct) ...
        if self.cancer_detection_widget:
            self.cancer_detection_widget.setTabText(0, QCoreApplication.translate("MainWindow", "Breast Cancer"))
            self.cancer_detection_widget.setTabText(1, QCoreApplication.translate("MainWindow", "Lung Cancer"))
            self.cancer_detection_widget.setTabText(2, QCoreApplication.translate("MainWindow", "Brain Tumor"))

        # 4. Settings Button Tooltip
        tooltips_enabled = self.settings.value("tooltips/SettingsWindow", True, type=bool)
        if tooltips_enabled:
            self.settings_button.setToolTip(QCoreApplication.translate("MainWindow", "Open Settings"))
        else:
            self.settings_button.setToolTip("")
                
        print("MainWindow texts retranslated successfully.")

    # 3. Add the new slot to handle the change
    def handle_language_change(self, language_name: str):
        """
        Called when the user selects a new language in the settings window.
        """
        # 1. Tell the manager to load and install the new language file
        success = self.language_manager.load_language(language_name)
        
        if not success:
            QMessageBox.warning(
                self,
                QCoreApplication.translate("MainWindow", "Error"),
                QCoreApplication.translate("MainWindow", 
                    "Could not load the selected language file. Please check the 'translations' folder."
                )
            )
            return
            
        # --- NEW: Call retranslateUi to update all texts immediately ---
        self.retranslateUi()
        
    def save_state(self):
        """Saves UI state (like splitters) to the settings file."""
        self.molecular_docking_widget.save_splitter_state(self.settings)
        self.settings.sync()
        print("Application state saved.")

    def restore_state(self):
        """Restores theme, tooltips, and other UI states on startup."""
        
        # --- Apply theme based on saved setting ---
        self.apply_theme()
        
        # --- MODIFIED: Load and apply individual tooltip settings ---
        viewers_tooltips = self.settings.value("tooltips/Detectors", True, type=bool)
        docking_tooltips = self.settings.value("tooltips/Docking", True, type=bool)
        settings_tooltips = self.settings.value("tooltips/SettingsWindow", True, type=bool)

        # Apply settings via the unified handler
        self.on_tooltips_setting_changed("tooltips/Detectors", viewers_tooltips)
        self.on_tooltips_setting_changed("tooltips/Docking", docking_tooltips)
        self.on_tooltips_setting_changed("tooltips/SettingsWindow", settings_tooltips)
        
        self.molecular_docking_widget.restore_splitter_state(self.settings) # NOTE: Placeholder method assumed
        print(f"Application state restored.")

    def switchContent(self, index):
        """Switches the view to the correct content widget and updates button style."""
        self.content_stack.setCurrentIndex(index)
        
        for i, button in enumerate(self.buttons):
            if i == index:
                if self.is_dark_mode:
                    button.setStyleSheet(DARK_MODE_ACTIVE_BUTTON_STYLESHEET)
                else:
                    button.setStyleSheet(LIGHT_MODE_ACTIVE_BUTTON_STYLESHEET)
            else:
                if self.is_dark_mode:
                    button.setStyleSheet(DARK_MODE_INACTIVE_BUTTON_STYLESHEET)
                else:
                    button.setStyleSheet(LIGHT_MODE_INACTIVE_BUTTON_STYLESHEET)

    # --- NEW: Slots to handle settings changes ---
    def on_theme_setting_changed(self, theme_value: str):
        """
        Called by the SettingsWindow dropdown.
        Saves the new theme value and applies it.
        """
        self.settings.setValue("theme", theme_value)
        self.apply_theme()

    def on_tooltips_setting_changed(self, key: str, enabled: bool):
        """Handles specific tooltip toggles from the SettingsWindow."""
        print(f"Tooltip setting changed: {key} to {enabled}")
        
        if key == "tooltips/Detectors":
            # Target all Viewer-related widgets
            viewer_widgets = self.findChildren(BreastCancerWidget) + \
                             self.findChildren(LungCancerWidget) + \
                             self.findChildren(BrainTumorWidget)
            for element in viewer_widgets:
                if hasattr(element, 'set_tooltips_enabled'):
                    element.set_tooltips_enabled(enabled)

        elif key == "tooltips/Docking":
            # Target Molecular Docking widget
            docker_widgets = self.findChildren(MoleculeViewerWidget) + \
                             self.findChildren(MolecularDockingWidget)
            for docker in docker_widgets:
                if hasattr(docker, 'set_tooltips_enabled'):
                    docker.set_tooltips_enabled(enabled)
        
        elif key == "tooltips/SettingsWindow":
            # Update the main application's settings button tooltip
            # --- MODIFIED: Use QCoreApplication.translate for the tooltip text ---
            self.settings_button.setToolTip(
                QCoreApplication.translate("MainWindow", "Open Settings") if enabled else ""
            )
            # The SettingsWindow handles its internal elements via its own internal method
            
        # In a real app, you might also have global widgets to update here.
        # For now, the main settings button is the only global one explicitly controlled.

    # --- NEW: Helper to check system theme ---
    def is_system_dark_mode(self) -> bool:
        """Checks if the system is in dark mode."""
        try:
            style_hints = QApplication.instance().styleHints()
            color_scheme = style_hints.colorScheme()
            return color_scheme == Qt.ColorScheme.Dark
        except Exception:
            return False # Default to light mode on error

    # --- MODIFIED: This is called by the toggle switch ---
    def changeTheme(self, dark_mode: bool):
        """
        Called ONLY by the GradientToggle.
        This OVERRIDES the theme setting to "light" or "dark".
        """
        theme_value = "dark" if dark_mode else "light"
        self.settings.setValue("theme", theme_value)
        self.apply_theme()

    # --- NEW: Central method to apply theme ---
    def apply_theme(self):
        """
        Reads the "theme" from settings, resolves it (handles "system_default"),
        and applies it to the entire application.
        """
        theme_value = self.settings.value("theme", "system_default")
        
        dark_mode = False
        if theme_value == "dark":
            dark_mode = True
        elif theme_value == "light":
            dark_mode = False
        elif theme_value == "system_default":
            dark_mode = self.is_system_dark_mode()
            
        print(f"Applying theme: {theme_value} (Resolved to dark_mode={dark_mode})")

        self.is_dark_mode = dark_mode
        global THEME
        
        if dark_mode:
            self.setStyleSheet(f"QMainWindow {{ border: 1px solid #444; }} {DARK_STYLE}")
            THEME = False
            
            bg_color = "#2E2E2E"
        else:
            self.setStyleSheet(f"QMainWindow {{ border: 1px solid #AAA; }} {LIGHT_STYLE}")
            THEME = True
            bg_color = "#f6f6f6"
        self.title_bar.update_theme(dark_mode)
        # Update Settings Icon Color
        icon_path = "assets/settings_dark.png" if dark_mode else "assets/settings_light.png"
        self.settings_button.setIcon(QIcon(icon_path))
        
        # Update the theme of the settings window itself (only if it's currently open)
        if self.settings_window_instance:
            self.settings_window_instance.update_theme(dark_mode)
        
        # Update the toggle's visual state
        self.toggle.set_initial_state(dark_mode)

        # ... (Rest of your theme logic) ...
        cancer_detection_tab_widget = self.content_stack.findChild(QTabWidget)
        if cancer_detection_tab_widget:
            breast_cancer_widget = cancer_detection_tab_widget.widget(0)
            lung_cancer_widget = cancer_detection_tab_widget.widget(1)
            brain_tumor_widget = cancer_detection_tab_widget.widget(2)
            if breast_cancer_widget:
                if dark_mode:
                    breast_cancer_widget.setStyleSheet(DARK_STYLE_BC)
                    lung_cancer_widget.setStyleSheet(DARK_STYLE_BC)
                    brain_tumor_widget.setStyleSheet(DARK_STYLE_BC)
                else:
                    breast_cancer_widget.setStyleSheet(LIGHT_STYLE_BC)
                    lung_cancer_widget.setStyleSheet(LIGHT_STYLE_BC)
                    brain_tumor_widget.setStyleSheet(LIGHT_STYLE_BC)
                    
        self.switchContent(self.content_stack.currentIndex())
        
        for viewer in self.findChildren(MoleculeViewerWidget):
            viewer.web_view.page().setBackgroundColor(QColor(bg_color))
            viewer.init_viewer()

    def closeEvent(self, event):
        self.save_state()
        super().closeEvent(event)

# ==========================================================
# Function to safely load the model into the global variable
# ==========================================================
# --- Main Execution Block ---
def main():
    app = QApplication(sys.argv)
    main_window = None
    lang_manager = LanguageManager(app)
        
    # --- NEW: Load initial language ---
    # Read from settings *before* creating any windows
    settings = QSettings("settings.ini", QSettings.Format.IniFormat)
    saved_language = settings.value("general/language", "English (US)")
    lang_manager.load_language(saved_language)
    icon_path = Path(__file__).parent / "assets" / "OncoDock.ico" # Or .ico
    app.setWindowIcon(QIcon(str(icon_path)))
    def show_main_window():
        nonlocal main_window
        print("Loading complete. Showing main window.")
        main_window = MainWindow(language_manager=lang_manager) # Ensure MainWindow is defined
        main_window.show()
        splash.close()

    splash = SplashScreen()
    splash.show()

    thread = QThread()
    worker = ModelLoaderWorker()
    worker.moveToThread(thread)

    # --- THE KEY CONNECTION ---
    # Connect the worker's progress signal to the splash screen's update slot
    worker.progress.connect(splash.update_progress)
    
    thread.started.connect(worker.run)
    worker.finished.connect(show_main_window)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    thread.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
