import 'package:local_auth/local_auth.dart';
import 'package:local_auth/error_codes.dart' as auth_error;
import 'package:flutter/services.dart';

class BiometricAuthService {
  final LocalAuthentication _localAuth = LocalAuthentication();

  /// Check if biometrics are available on this device
  Future<bool> canCheckBiometrics() async {
    try {
      return await _localAuth.canCheckBiometrics;
    } on PlatformException {
      return false;
    }
  }

  /// Get available biometric types (Face ID, Touch ID, etc.)
  Future<List<BiometricType>> getAvailableBiometrics() async {
    try {
      return await _localAuth.getAvailableBiometrics();
    } on PlatformException {
      return <BiometricType>[];
    }
  }

  /// Authenticate with biometrics
  Future<bool> authenticate({
    String reason = 'Please authenticate to access Cancer Detector',
  }) async {
    try {
      final bool canAuthenticate = await canCheckBiometrics();

      if (!canAuthenticate) {
        // No biometrics available - allow access anyway
        // (You could require a PIN here instead)
        return true;
      }

      final bool authenticated = await _localAuth.authenticate(
        localizedReason: reason,
        options: const AuthenticationOptions(
          stickyAuth: true, // Show auth dialog even if app goes to background
          biometricOnly: false, // Allow device PIN as fallback
          useErrorDialogs: true,
        ),
      );

      return authenticated;

    } on PlatformException catch (e) {
      // Handle specific errors
      if (e.code == auth_error.notAvailable) {
        // Biometrics not available - allow access
        return true;
      } else if (e.code == auth_error.notEnrolled) {
        // No biometrics enrolled - allow access
        return true;
      } else if (e.code == auth_error.lockedOut ||
                 e.code == auth_error.permanentlyLockedOut) {
        // Too many failed attempts
        return false;
      }

      // Other errors - deny access for security
      return false;
    }
  }

  /// Check if Face ID is available
  Future<bool> isFaceIDAvailable() async {
    final biometrics = await getAvailableBiometrics();
    return biometrics.contains(BiometricType.face);
  }

  /// Check if Touch ID is available
  Future<bool> isTouchIDAvailable() async {
    final biometrics = await getAvailableBiometrics();
    return biometrics.contains(BiometricType.fingerprint);
  }

  /// Get human-readable name of available biometric
  Future<String> getBiometricTypeName() async {
    final biometrics = await getAvailableBiometrics();

    if (biometrics.contains(BiometricType.face)) {
      return 'Face ID';
    } else if (biometrics.contains(BiometricType.fingerprint)) {
      return 'Touch ID';
    } else if (biometrics.contains(BiometricType.iris)) {
      return 'Iris Scan';
    } else {
      return 'Biometric';
    }
  }
}
