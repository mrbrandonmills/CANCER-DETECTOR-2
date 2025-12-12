import 'dart:io';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/scan_history_service.dart';
import 'result_screen.dart';
import 'result_screen_v4.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> with SingleTickerProviderStateMixin {
  final ImagePicker _picker = ImagePicker();
  bool _isProcessing = false;
  String? _statusMessage;
  late AnimationController _dotAnimationController;

  // Toggle between V3 and V4 API (set to true to use V4)
  bool _useV4Api = true;

  @override
  void initState() {
    super.initState();
    // Initialize loading dots animation
    _dotAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat();
    // Auto-open camera when screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) => _takePhoto());
  }

  @override
  void dispose() {
    _dotAnimationController.dispose();
    super.dispose();
  }

  Future<void> _takePhoto() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.rear,
        imageQuality: 85,
        maxWidth: 1920,
        maxHeight: 1920,
      );

      if (photo != null) {
        await _processPhoto(File(photo.path));
      } else {
        // User cancelled - go back
        if (mounted) Navigator.pop(context);
      }
    } catch (e) {
      _showError('Camera error: $e');
    }
  }

  Future<void> _pickFromGallery() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
        maxWidth: 1920,
        maxHeight: 1920,
      );

      if (photo != null) {
        await _processPhoto(File(photo.path));
      }
    } catch (e) {
      _showError('Gallery error: $e');
    }
  }

  Future<void> _processPhoto(File imageFile) async {
    setState(() {
      _isProcessing = true;
      _statusMessage = 'Claude AI is analyzing your product...';
    });

    try {
      final apiService = context.read<ApiService>();

      // Update status
      setState(() {
        _statusMessage = 'Reading label and identifying ingredients...';
      });

      if (_useV4Api) {
        // Use V4 API endpoint
        await _processPhotoV4(imageFile, apiService);
      } else {
        // Use V3 API endpoint (legacy)
        await _processPhotoV3(imageFile, apiService);
      }
    } catch (e) {
      _showError('Error: $e');

      // Go back after showing error
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) Navigator.pop(context);
      });
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _statusMessage = null;
        });
      }
    }
  }

  /// Process photo using V4 API
  Future<void> _processPhotoV4(File imageFile, ApiService apiService) async {
    try {
      setState(() {
        _statusMessage = 'Analyzing with TrueCancer V4 system...';
      });

      // Call V4 endpoint
      final resultV4 = await apiService.scanImageV4(imageFile);

      if (!mounted) return;

      // Save to history (convert V4 result to V3 format for compatibility)
      context.read<ScanHistoryService>().addScan(resultV4.toScanResult());

      // Navigate to V4 result screen
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => ResultScreenV4(
            result: resultV4,
          ),
        ),
      );
    } catch (e) {
      _showError('V4 API Error: $e');

      // Go back after showing error
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) Navigator.pop(context);
      });
    }
  }

  /// Process photo using V3 API (legacy)
  Future<void> _processPhotoV3(File imageFile, ApiService apiService) async {
    try {
      // Send to backend v3.1.0 for processing
      final result = await apiService.scanImage(imageFile);

      if (!mounted) return;

      if (result.success) {
        // Save to history
        context.read<ScanHistoryService>().addScan(result);

        // Navigate to result screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => ResultScreen(result: result),
          ),
        );
      } else {
        _showError(result.error ?? 'Could not analyze product. Please try again.');

        // Go back after showing error
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) Navigator.pop(context);
        });
      }
    } catch (e) {
      _showError('V3 API Error: $e');

      // Go back after showing error
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) Navigator.pop(context);
      });
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
        action: SnackBarAction(
          label: 'Retry',
          textColor: Colors.white,
          onPressed: _takePhoto,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0f172a), // Dark theme
      appBar: AppBar(
        title: const Text('Scan Product'),
        backgroundColor: const Color(0xFF1e293b),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isProcessing) {
      return _buildProcessingState();
    }

    return _buildInitialState();
  }

  Widget _buildProcessingState() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            const Color(0xFF1e293b),
            const Color(0xFF0f172a),
          ],
        ),
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Premium pulsing gradient circle
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Color(0xFF06B6D4), // Cyan
                    Color(0xFF8B5CF6), // Purple
                  ],
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF06B6D4).withOpacity(0.5),
                    blurRadius: 30,
                    spreadRadius: 0,
                  ),
                ],
              ),
              child: const Center(
                child: Icon(
                  Icons.search_rounded,
                  color: Colors.white,
                  size: 48,
                ),
              ),
            ),
            const SizedBox(height: 32),

            // Status text
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 40),
              child: Column(
                children: [
                  Text(
                    _statusMessage ?? 'Analyzing Product...',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Researching ingredients & safety data',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 40),

            // Loading dots animation
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildLoadingDot(0),
                const SizedBox(width: 12),
                _buildLoadingDot(1),
                const SizedBox(width: 12),
                _buildLoadingDot(2),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoadingDot(int index) {
    return AnimatedBuilder(
      animation: _dotAnimationController,
      builder: (context, child) {
        // Each dot has a delay offset (0ms, 200ms, 400ms)
        final delay = index * 0.2;
        final animValue = (_dotAnimationController.value + delay) % 1.0;

        // Smooth fade in/out using sine wave
        final scale = 0.5 + (0.5 * (1 + sin(animValue * 2 * 3.14159)) / 2);
        final opacity = 0.3 + (0.7 * scale);

        return Transform.scale(
          scale: scale,
          child: Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFF8b5cf6).withOpacity(opacity),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF8b5cf6).withOpacity(opacity * 0.5),
                  blurRadius: 8,
                  spreadRadius: 2,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildInitialState() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            const Color(0xFF1e293b),
            const Color(0xFF0f172a),
          ],
        ),
      ),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Camera icon with gradient
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFF8b5cf6),
                      const Color(0xFF06b6d4),
                    ],
                  ),
                ),
                child: const Center(
                  child: Icon(
                    Icons.camera_alt,
                    size: 60,
                    color: Colors.white,
                  ),
                ),
              ),
              const SizedBox(height: 32),

              const Text(
                'Ready to Scan',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 12),

              Text(
                'Take a photo of the product label',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.white.withOpacity(0.7),
                ),
              ),
              const SizedBox(height: 48),

              // Action buttons
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _takePhoto,
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Take Photo'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF8b5cf6),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _pickFromGallery,
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Choose from Gallery'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFF06b6d4),
                    side: const BorderSide(color: Color(0xFF06b6d4)),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
