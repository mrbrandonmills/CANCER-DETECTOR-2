import 'package:flutter/material.dart';

// V4 Data Models for Enhanced Cancer Detection Results

class ScanResultV4 {
  final bool success;
  final String? productName;
  final String? brand;
  final int score; // 0-100 (overall_score from API)
  final String grade; // F, D, C, B, A, A+ (overall_grade from API)
  final DimensionScores dimensionScores;
  final List<String> alerts; // V4: Processing alerts
  final List<String> hiddenTruths;
  final CorporateDisclosure? corporateDisclosure;
  final List<IngredientGraded> ingredientsGraded;
  final String? reportId;
  final DateTime scannedAt;

  ScanResultV4({
    required this.success,
    this.productName,
    this.brand,
    required this.score,
    required this.grade,
    required this.dimensionScores,
    required this.alerts,
    required this.hiddenTruths,
    this.corporateDisclosure,
    required this.ingredientsGraded,
    this.reportId,
    DateTime? scannedAt,
  }) : scannedAt = scannedAt ?? DateTime.now();

  factory ScanResultV4.fromJson(Map<String, dynamic> json) {
    return ScanResultV4(
      success: json['success'] as bool? ?? true,
      productName: json['product_name'] as String?,
      brand: json['brand'] as String?,
      score: json['overall_score'] as int? ?? 0, // V4 API uses "overall_score"
      grade: json['overall_grade'] as String? ?? 'F', // V4 API uses "overall_grade"
      dimensionScores: DimensionScores.fromJson(json['dimension_scores'] ?? {}),
      alerts: json['alerts'] != null
          ? List<String>.from(json['alerts'])
          : [],
      hiddenTruths: json['hidden_truths'] != null
          ? List<String>.from(json['hidden_truths'])
          : [],
      corporateDisclosure: json['corporate_disclosure'] != null
          ? CorporateDisclosure.fromJson(json['corporate_disclosure'])
          : null,
      ingredientsGraded: json['ingredients_graded'] != null
          ? (json['ingredients_graded'] as List)
              .map((item) => IngredientGraded.fromJson(item))
              .toList()
          : [],
      reportId: json['report_id'] as String?,
      scannedAt: json['scanned_at'] != null
          ? DateTime.parse(json['scanned_at'])
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'product_name': productName,
      'brand': brand,
      'overall_score': score, // Map back to API format
      'overall_grade': grade, // Map back to API format
      'dimension_scores': dimensionScores.toJson(),
      'alerts': alerts,
      'hidden_truths': hiddenTruths,
      'corporate_disclosure': corporateDisclosure?.toJson(),
      'ingredients_graded': ingredientsGraded.map((i) => i.toJson()).toList(),
      'report_id': reportId,
      'scanned_at': scannedAt.toIso8601String(),
    };
  }

  // Get color based on grade (V4 colors)
  Color get gradeColor {
    switch (grade) {
      case 'F':
        return const Color(0xFFef4444); // Bright Red
      case 'D':
        return const Color(0xFFf97316); // Orange
      case 'C':
        return const Color(0xFFfacc15); // Yellow
      case 'B':
        return const Color(0xFF4ade80); // Light Green
      case 'A':
        return const Color(0xFF22c55e); // Green
      case 'A+':
        return const Color(0xFF22c55e); // Vibrant Green
      default:
        return Colors.grey;
    }
  }

  String get gradeEmoji {
    switch (grade) {
      case 'A+':
        return '🌟';
      case 'A':
        return '✅';
      case 'B':
        return '👍';
      case 'C':
        return '⚠️';
      case 'D':
        return '🟠';
      case 'F':
        return '🚨';
      default:
        return '❓';
    }
  }
}

class DimensionScores {
  final int ingredientSafety;
  final int processingLevel;
  final int corporateEthics;
  final int supplyChain;

  DimensionScores({
    required this.ingredientSafety,
    required this.processingLevel,
    required this.corporateEthics,
    required this.supplyChain,
  });

  factory DimensionScores.fromJson(Map<String, dynamic> json) {
    return DimensionScores(
      ingredientSafety: json['ingredient_safety'] as int? ?? 0,
      processingLevel: json['processing_level'] as int? ?? 0,
      corporateEthics: json['corporate_ethics'] as int? ?? 0,
      supplyChain: json['supply_chain'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'ingredient_safety': ingredientSafety,
      'processing_level': processingLevel,
      'corporate_ethics': corporateEthics,
      'supply_chain': supplyChain,
    };
  }
}

class CorporateDisclosure {
  final String brand;
  final String parentCompany;
  final List<String> issues;
  final List<String> notableBrands;
  final int penalty; // V4: Score penalty for corporate issues

  CorporateDisclosure({
    required this.brand,
    required this.parentCompany,
    required this.issues,
    required this.notableBrands,
    required this.penalty,
  });

  factory CorporateDisclosure.fromJson(Map<String, dynamic> json) {
    return CorporateDisclosure(
      brand: json['brand'] as String? ?? '',
      parentCompany: json['parent_company'] as String? ?? '',
      issues: json['issues'] != null
          ? List<String>.from(json['issues'])
          : [],
      notableBrands: json['notable_brands'] != null
          ? List<String>.from(json['notable_brands'])
          : [],
      penalty: json['penalty'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'brand': brand,
      'parent_company': parentCompany,
      'issues': issues,
      'notable_brands': notableBrands,
      'penalty': penalty,
    };
  }
}

class IngredientGraded {
  final String name;
  final String grade; // F, D, C, B, A, A+
  final String color; // Hex color code (e.g., "#ef4444")
  final String reason;
  final int hazardScore; // 0-100
  final String? hiddenTruth; // V4: Optional hidden truth about this ingredient

  IngredientGraded({
    required this.name,
    required this.grade,
    required this.color,
    required this.reason,
    required this.hazardScore,
    this.hiddenTruth,
  });

  factory IngredientGraded.fromJson(Map<String, dynamic> json) {
    return IngredientGraded(
      name: json['name'] as String? ?? '',
      grade: json['grade'] as String? ?? 'F',
      color: json['color'] as String? ?? '#ef4444',
      reason: json['reason'] as String? ?? '',
      hazardScore: json['hazard_score'] as int? ?? 0,
      hiddenTruth: json['hidden_truth'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'grade': grade,
      'color': color,
      'reason': reason,
      'hazard_score': hazardScore,
      'hidden_truth': hiddenTruth,
    };
  }

  Color get gradeColor {
    try {
      // Convert hex string to Color (e.g., "#ef4444" -> Color(0xFFef4444))
      final hexColor = color.replaceFirst('#', '');
      return Color(int.parse('FF$hexColor', radix: 16));
    } catch (e) {
      return Colors.grey;
    }
  }
}
