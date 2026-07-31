#!/usr/bin/env python3
"""
Filtres audio complets pour Toth :
1. Filtre de bruit avec sox
2. VAD simple avec seuil d'amplitude  
3. Normalisation audio automatique
4. Détection de silence pour arrêt auto
"""

import os
import subprocess
import tempfile
import numpy as np
from scipy.io import wavfile

def apply_audio_filters(input_wav, output_wav):
    """Applique les 4 filtres audio d'un coup"""
    
    # 1. Filtre de bruit avec sox (réduction de bruit)
    temp1 = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp1.close()
    
    # Commande sox pour réduire le bruit
    cmd_noise = [
        'sox', input_wav, temp1.name,
        'noisered', '/tmp/noise_profile.prof', '0.21',  # Réduction agressive
        'bandpass', '300', '3400',  # Filtre passe-bande vocal
        'norm'  # Normalisation douce
    ]
    
    try:
        subprocess.run(cmd_noise, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # Fallback sans filtre si sox échoue
        os.system(f'cp {input_wav} {temp1.name}')
    
    # 2. VAD + Détection de silence
    if has_speech(temp1.name):
        # 3. Normalisation audio
        normalized_file = normalize_audio(temp1.name)
        
        # 4. Copie vers output final
        os.system(f'cp {normalized_file} {output_wav}')
        os.remove(normalized_file)
        return True
    else:
        # Aucune parole détectée
        os.remove(temp1.name)
        return False

def has_speech(wav_file, threshold=0.02):
    """Détection simple de parole par seuil d'amplitude"""
    try:
        rate, data = wavfile.read(wav_file)
        if data.dtype != np.int16:
            data = data.astype(np.int16)
        
        # Calcul RMS (Root Mean Square)
        rms = np.sqrt(np.mean(data**2)) / 32768.0  # Normalisation 16-bit
        return rms > threshold
    except:
        return True  # Fallback: assume speech if error

def normalize_audio(input_wav, target_dB=-3.0):
    """Normalisation audio à un niveau cible"""
    temp_out = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_out.close()
    
    cmd_norm = [
        'sox', input_wav, temp_out.name,
        'norm', str(target_dB),  # Niveau cible
        'dither'  # Réduction de bruit de quantification
    ]
    
    try:
        subprocess.run(cmd_norm, check=True, capture_output=True)
        return temp_out.name
    except:
        # Fallback: copie simple
        os.system(f'cp {input_wav} {temp_out.name}')
        return temp_out.name

def create_noise_profile(reference_wav):
    """Crée un profil de bruit pour sox"""
    cmd_profile = [
        'sox', reference_wav, '-n', 'noiseprof', '/tmp/noise_profile.prof'
    ]
    subprocess.run(cmd_profile, capture_output=True)

if __name__ == "__main__":
    # Exemple d'utilisation
    import sys
    if len(sys.argv) == 3:
        apply_audio_filters(sys.argv[1], sys.argv[2])
        print(f"Filtres appliqués: {sys.argv[1]} -> {sys.argv[2]}")
    else:
        print("Usage: audio_filters.py input.wav output.wav")