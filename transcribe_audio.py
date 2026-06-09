#!/usr/bin/env python3
"""
Transcribe audio files from Product_Owner/Audio_Files/ directory.
Uses SpeechRecognition with offline recognition (PocketSphinx fallback).
"""

import os
import pathlib
from pathlib import Path

# Audio files to transcribe
FILES = [
    "Product_Owner/Audio_Files/WhatsApp Audio 2026-03-22 at 16.07.19.wav",
    "Product_Owner/Audio_Files/WhatsApp Audio 2026-03-22 at 16.07.19aaa.wav",
]

OUT_DIR = Path("Product_Owner/Audio_Files/transcripts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    import speech_recognition as sr
    print("Using SpeechRecognition library")
    
    recognizer = sr.Recognizer()
    
    for wav_file in FILES:
        wav_path = Path(wav_file)
        if not wav_path.exists():
            print(f"ERROR: File not found: {wav_file}")
            continue
        
        print(f"\nTranscribing: {wav_file}")
        try:
            with sr.AudioFile(wav_file) as source:
                audio_data = recognizer.record(source)
                
                # Try online recognition first (Google API - free, no key needed)
                try:
                    text = recognizer.recognize_google(audio_data)
                except sr.UnknownValueError:
                    print(f"  Google: Could not understand audio, trying offline...")
                    # Fallback to offline recognition if available
                    try:
                        text = recognizer.recognize_sphinx(audio_data)
                    except Exception as e:
                        print(f"  Offline recognition failed: {e}")
                        text = "[Transcription failed - audio not recognized]"
                except sr.RequestError as e:
                    print(f"  Google API error: {e}")
                    text = "[Transcription failed - API error]"
            
            # Save transcription
            out_file = OUT_DIR / (wav_path.stem + ".txt")
            out_file.write_text(text, encoding="utf-8")
            print(f"  ✓ Saved: {out_file}")
            print(f"  Text preview: {text[:100]}...")
            
        except Exception as e:
            print(f"  ERROR processing {wav_file}: {e}")

except ImportError:
    print("ERROR: SpeechRecognition not installed")
    print("Install with: python -m pip install SpeechRecognition")
except Exception as e:
    print(f"FATAL ERROR: {e}")
