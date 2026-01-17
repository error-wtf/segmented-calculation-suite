#!/usr/bin/env python3
"""
SSZ Calculation Suite - Colab Launcher

This script launches the app with share=True for Google Colab.
"""

import os
import sys

# Ensure we're in the right directory
if os.path.exists('segcalc'):
    sys.path.insert(0, '.')
elif os.path.exists('segmented-calculation-suite'):
    os.chdir('segmented-calculation-suite')
    sys.path.insert(0, '.')

# Import and run the app with share=True
if __name__ == "__main__":
    print("="*60)
    print("🚀 SSZ Calculation Suite - Colab Launcher")
    print("="*60)
    print("")
    print("Starting app with PUBLIC SHAREABLE LINK...")
    print("Look for: https://xxxxx.gradio.live")
    print("")
    print("="*60)
    
    # Import the app module
    from app import app
    
    # Launch with share=True
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True
    )
