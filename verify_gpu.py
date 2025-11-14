#!/usr/bin/env python3
"""
GPU Verification Script for UltraWealth
Verifies that NVIDIA GPU is accessible and configured correctly for TensorFlow
"""

import sys

def check_nvidia_smi():
    """Check if nvidia-smi is available"""
    import subprocess
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ NVIDIA GPU detected")
            print(result.stdout)
            return True
        else:
            print("✗ nvidia-smi failed")
            return False
    except FileNotFoundError:
        print("✗ nvidia-smi not found - NVIDIA drivers may not be installed")
        return False

def check_tensorflow_gpu():
    """Check if TensorFlow can access the GPU"""
    try:
        import tensorflow as tf
        print(f"\n✓ TensorFlow version: {tf.__version__}")
        
        # List physical devices
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"✓ TensorFlow detected {len(gpus)} GPU(s):")
            for gpu in gpus:
                print(f"  - {gpu.name}")
            
            # Test GPU computation
            print("\nTesting GPU computation...")
            with tf.device('/GPU:0'):
                a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
                b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
                c = tf.matmul(a, b)
                print(f"✓ GPU computation successful: \n{c.numpy()}")
            
            return True
        else:
            print("✗ No GPUs detected by TensorFlow")
            print("\nTensorFlow build info:")
            print(f"  CUDA available: {tf.test.is_built_with_cuda()}")
            print(f"  GPU available: {tf.test.is_gpu_available()}")
            return False
            
    except ImportError:
        print("✗ TensorFlow not installed")
        return False
    except Exception as e:
        print(f"✗ Error testing TensorFlow GPU: {e}")
        return False

def check_cuda_version():
    """Check CUDA version"""
    import subprocess
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n✓ CUDA Compiler:")
            print(result.stdout)
            return True
        else:
            print("\n⚠ CUDA compiler (nvcc) not found in PATH")
            return False
    except FileNotFoundError:
        print("\n⚠ CUDA compiler (nvcc) not found")
        return False

def main():
    print("=" * 60)
    print("UltraWealth GPU Verification")
    print("=" * 60)
    print()
    
    checks = {
        "NVIDIA Driver": check_nvidia_smi(),
        "TensorFlow GPU": check_tensorflow_gpu(),
        "CUDA Compiler": check_cuda_version()
    }
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    for check_name, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check_name}: {status}")
    
    print()
    
    if all(checks.values()):
        print("🎉 All checks passed! GPU is ready for UltraWealth.")
        return 0
    else:
        print("⚠ Some checks failed. Please review the output above.")
        print("\nNext steps:")
        if not checks["NVIDIA Driver"]:
            print("  1. Install NVIDIA drivers: https://www.nvidia.com/download/index.aspx")
        if not checks["CUDA Compiler"]:
            print("  2. Install CUDA Toolkit: https://developer.nvidia.com/cuda-downloads")
        if not checks["TensorFlow GPU"]:
            print("  3. Install TensorFlow with GPU support: pip install tensorflow[and-cuda]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
