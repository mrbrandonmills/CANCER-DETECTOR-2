import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:mime/mime.dart';
import 'package:http_parser/http_parser.dart';
import '../models/scan_result.dart';
import '../models/scan_result_v4.dart';
import '../models/deep_research_models.dart';

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

  /// V4 endpoint: Multi-dimensional TrueCancer scoring with corporate disclosure
  /// Returns ScanResultV4 with dimension_scores, ingredients_graded, alerts, and hidden_truths
  Future<ScanResultV4> scanImageV4(File imageFile) async {
    try {
      // Create multipart request
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/v4/scan'), // V4 endpoint
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
        return ScanResultV4.fromJson(jsonData);
      } else if (response.statusCode == 400) {
        // Bad request - return error state
        try {
          final jsonData = jsonDecode(response.body);
          final errorMsg = jsonData['detail'] ?? jsonData['error'] ?? 'Invalid request';
          // Return error state V4 result
          return ScanResultV4(
            success: false,
            score: 0,
            grade: 'F',
            dimensionScores: DimensionScores(
              ingredientSafety: 0,
              processingLevel: 0,
              corporateEthics: 0,
              supplyChain: 0,
            ),
            ingredientsGraded: [],
            alerts: [errorMsg],
            hiddenTruths: [],
          );
        } catch (_) {
          throw Exception('Invalid request: ${response.body}');
        }
      } else if (response.statusCode == 500) {
        throw Exception('Server error. Please try again.');
      } else {
        throw Exception('Unexpected error: ${response.statusCode}');
      }
    } on SocketException {
      throw Exception('No internet connection. Please check your network.');
    } on http.ClientException {
      throw Exception('Connection failed. Please try again.');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  /// Start a deep research job for comprehensive product investigation
  Future<String> startDeepResearch({
    required String productName,
    String? brand,
    required String category,
    required List<String> ingredients,
  }) async {
    try {
      final request = {
        'product_name': productName,
        'brand': brand,
        'category': category,
        'ingredients': ingredients,
      };

      final response = await http.post(
        Uri.parse('$baseUrl/api/v4/deep-research'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(request),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['job_id'] as String;
      } else if (response.statusCode == 400) {
        final data = jsonDecode(response.body);
        throw Exception(data['detail'] ?? 'Invalid request');
      } else {
        throw Exception('Failed to start deep research: ${response.statusCode}');
      }
    } on SocketException {
      throw Exception('No internet connection');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  /// Get the status of a deep research job
  Future<DeepResearchJob> getJobStatus(String jobId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v4/job/$jobId'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return DeepResearchJob.fromJson(data);
      } else if (response.statusCode == 404) {
        throw Exception('Job not found');
      } else {
        throw Exception('Failed to get job status: ${response.statusCode}');
      }
    } on SocketException {
      throw Exception('No internet connection');
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  /// Download PDF from server for a completed deep research job
  /// Server-side PDF generation eliminates iOS memory crashes from client-side dart_pdf
  Future<List<int>> downloadDeepResearchPdf(String jobId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v4/deep-research/$jobId/pdf'),
      ).timeout(const Duration(seconds: 60)); // PDF generation may take time

      if (response.statusCode == 200) {
        return response.bodyBytes;
      } else if (response.statusCode == 404) {
        throw Exception('Job not found');
      } else if (response.statusCode == 400) {
        final data = jsonDecode(response.body);
        throw Exception(data['detail'] ?? 'Job not completed');
      } else {
        throw Exception('Failed to download PDF: ${response.statusCode}');
      }
    } on SocketException {
      throw Exception('No internet connection');
    } catch (e) {
      throw Exception('Error downloading PDF: $e');
    }
  }
}
