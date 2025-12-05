import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:mime/mime.dart';
import 'package:http_parser/http_parser.dart';
import '../models/scan_result.dart';

class ApiService {
  // Production Railway deployment - Backend v3.1.0
  static const String baseUrl = 'https://cancer-detector-backend-production.up.railway.app';

  // For local development
  // static const String baseUrl = 'http://localhost:8000';

  /// Scan a product image using the V3 endpoint (default)
  /// Uses /api/v3/scan with modular prompts and ingredient-focused analysis
  Future<ScanResult> scanImage(File imageFile) async {
    return scanImageV3(imageFile);
  }

  /// V3 endpoint: Modular prompts with 95% ingredient-focused scoring
  /// Accepts a File and uploads via multipart/form-data
  Future<ScanResult> scanImageV3(File imageFile) async {
    try {
      // Create multipart request
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/v3/scan'), // V3 endpoint
      );

      // Detect MIME type from file extension
      final mimeTypeString = lookupMimeType(imageFile.path) ?? 'image/jpeg';
      final mediaType = MediaType.parse(mimeTypeString);

      // Add image file with explicit contentType
      request.files.add(await http.MultipartFile.fromPath(
        'image',
        imageFile.path,
        contentType: mediaType,
      ));

      // Send request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return ScanResult.fromJsonV3(jsonData); // Use V3 parser
      } else if (response.statusCode == 400) {
        // Bad request - try to parse error message
        try {
          final jsonData = jsonDecode(response.body);
          // Check both 'detail' (FastAPI) and 'error' (backwards compatibility)
          final errorMsg = jsonData['detail'] ?? jsonData['error'] ?? 'Invalid request';
          return ScanResult.error(errorMsg);
        } catch (_) {
          return ScanResult.error('Invalid request: ${response.body}');
        }
      } else if (response.statusCode == 500) {
        return ScanResult.error('Server error. Please try again.');
      } else {
        return ScanResult.error('Unexpected error: ${response.statusCode}');
      }
    } on SocketException {
      return ScanResult.error('No internet connection. Please check your network.');
    } on http.ClientException {
      return ScanResult.error('Connection failed. Please try again.');
    } catch (e) {
      return ScanResult.error('Error: $e');
    }
  }

  /// V2 endpoint (kept as fallback): Original analysis endpoint
  /// Accepts a File and uploads via multipart/form-data
  Future<ScanResult> scanImageV2(File imageFile) async {
    try {
      // Create multipart request
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/v1/scan'), // V2 endpoint
      );

      // Detect MIME type from file extension
      final mimeTypeString = lookupMimeType(imageFile.path) ?? 'image/jpeg';
      final mediaType = MediaType.parse(mimeTypeString);

      // Add image file with explicit contentType
      request.files.add(await http.MultipartFile.fromPath(
        'image',
        imageFile.path,
        contentType: mediaType,
      ));

      // Send request
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(response.body);
        return ScanResult.fromJson(jsonData);
      } else if (response.statusCode == 400) {
        // Bad request - try to parse error message
        try {
          final jsonData = jsonDecode(response.body);
          // Check both 'detail' (FastAPI) and 'error' (backwards compatibility)
          final errorMsg = jsonData['detail'] ?? jsonData['error'] ?? 'Invalid request';
          return ScanResult.error(errorMsg);
        } catch (_) {
          return ScanResult.error('Invalid request: ${response.body}');
        }
      } else if (response.statusCode == 500) {
        return ScanResult.error('Server error. Please try again.');
      } else {
        return ScanResult.error('Unexpected error: ${response.statusCode}');
      }
    } on SocketException {
      return ScanResult.error('No internet connection. Please check your network.');
    } on http.ClientException {
      return ScanResult.error('Connection failed. Please try again.');
    } catch (e) {
      return ScanResult.error('Error: $e');
    }
  }

  /// Look up a single ingredient (updated endpoint)
  Future<Map<String, dynamic>?> lookupIngredient(String name) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/ingredient/${Uri.encodeComponent(name)}'),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Health check
  Future<bool> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        return json['status'] == 'healthy';
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  /// Get API version info
  Future<String?> getVersion() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        return json['version'];
      }
      return null;
    } catch (e) {
      return null;
    }
  }
}
