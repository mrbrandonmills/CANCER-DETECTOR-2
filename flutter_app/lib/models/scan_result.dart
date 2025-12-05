import 'package:flutter/material.dart';

class ScanResult {
  final bool success;
  final String? productName;
  final String? brand;
  final String? productType; // consumable | container | cookware | baby_item | other
  final List<String>? ingredients;
  final String? ingredientsSource; // from_label | from_knowledge
  final List<MaterialAnalysis>? materials;
  final ConditionData? condition;
  final int? safetyScore; // 0-100
  final int? conditionScore; // 0-100
  final int? overallScore; // 0-100
  final String? grade; // A+ | A | A- | B+ | B | B- | C+ | C | C- | D+ | D | D- | F
  final List<FlaggedIngredient>? flaggedIngredients;
  final List<String>? safeIngredients;
  final String? recommendation;
  final List<CareTip>? careTips;
  final SaferAlternative? saferAlternative;
  final String? confidence; // high | medium | low
  final String? analysisType; // ingredient | material
  final String? personalizedNotes;
  final String? reportId;
  final String? timestamp;
  final String? error;
  final DateTime scannedAt;

  // V3: Enhanced ingredients structure
  final IngredientsData? ingredientsData;

  // V3: Positive attributes with bonuses
  final List<PositiveAttribute>? positiveAttributes;

  // V3: Enhanced condition with weight percentage
  final ConditionDataV3? conditionV3;

  // V3: Expiration tracking
  final ExpirationData? expiration;

  ScanResult({
    required this.success,
    this.productName,
    this.brand,
    this.productType,
    this.ingredients,
    this.ingredientsSource,
    this.materials,
    this.condition,
    this.safetyScore,
    this.conditionScore,
    this.overallScore,
    this.grade,
    this.flaggedIngredients,
    this.safeIngredients,
    this.recommendation,
    this.careTips,
    this.saferAlternative,
    this.confidence,
    this.analysisType,
    this.personalizedNotes,
    this.reportId,
    this.timestamp,
    this.error,
    DateTime? scannedAt,
    this.ingredientsData,
    this.positiveAttributes,
    this.conditionV3,
    this.expiration,
  }) : scannedAt = scannedAt ?? DateTime.now();

  factory ScanResult.fromJson(Map<String, dynamic> json) {
    return ScanResult(
      success: json['success'] ?? true, // Default to true if not explicitly false
      productName: json['product_name'],
      brand: json['brand'],
      productType: json['product_type'],
      ingredients: json['ingredients'] != null
          ? List<String>.from(json['ingredients'])
          : null,
      ingredientsSource: json['ingredients_source'],
      materials: json['materials'] != null
          ? (json['materials'] as List)
              .map((m) => MaterialAnalysis.fromJson(m))
              .toList()
          : null,
      condition: json['condition'] != null
          ? ConditionData.fromJson(json['condition'])
          : null,
      safetyScore: json['safety_score'],
      conditionScore: json['condition_score'],
      overallScore: json['overall_score'],
      grade: json['grade'],
      flaggedIngredients: json['flagged_ingredients'] != null
          ? (json['flagged_ingredients'] as List)
              .map((i) => FlaggedIngredient.fromJson(i))
              .toList()
          : null,
      safeIngredients: json['safe_ingredients'] != null
          ? List<String>.from(json['safe_ingredients'])
          : null,
      recommendation: json['recommendation'],
      careTips: json['care_tips'] != null
          ? (json['care_tips'] as List)
              .map((t) => CareTip.fromJson(t))
              .toList()
          : null,
      saferAlternative: json['safer_alternative'] != null
          ? SaferAlternative.fromJson(json['safer_alternative'])
          : null,
      confidence: json['confidence'],
      analysisType: json['analysis_type'],
      personalizedNotes: json['personalized_notes'],
      reportId: json['report_id'],
      timestamp: json['timestamp'],
      error: json['error'],
    );
  }

  factory ScanResult.error(String message) {
    return ScanResult(
      success: false,
      error: message,
    );
  }

  factory ScanResult.fromJsonV3(Map<String, dynamic> json) {
    return ScanResult(
      success: json['success'] as bool? ?? false,
      productName: json['product_name'] as String?,
      brand: json['brand'] as String?,
      productType: json['product_type'] as String?,

      // V3: Parse enhanced ingredients
      ingredientsData: json['ingredients'] != null
          ? IngredientsData.fromJson(json['ingredients'])
          : null,

      // V3: Parse positive attributes
      positiveAttributes: json['positive_attributes'] != null
          ? (json['positive_attributes'] as List)
              .map((item) => PositiveAttribute.fromJson(item))
              .toList()
          : null,

      // V3: Parse enhanced condition
      conditionV3: json['condition'] != null
          ? ConditionDataV3.fromJson(json['condition'])
          : null,

      // V3: Parse expiration
      expiration: json['expiration'] != null
          ? ExpirationData.fromJson(json['expiration'])
          : null,

      safetyScore: json['safety_score'] as int?,
      conditionScore: json['condition_score'] as int?,
      overallScore: json['overall_score'] as int?,
      grade: json['grade'] as String?,

      // Safer alternative (V3 compatible)
      saferAlternative: json['safer_alternative'] != null
          ? SaferAlternative.fromJson(json['safer_alternative'])
          : null,

      confidence: json['confidence'] as String?,
      analysisType: json['analysis_type'] as String?,
      reportId: json['report_id'] as String?,
      timestamp: json['timestamp'] as String?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'product_name': productName,
      'brand': brand,
      'product_type': productType,
      'ingredients': ingredients,
      'ingredients_source': ingredientsSource,
      'materials': materials?.map((m) => m.toJson()).toList(),
      'condition': condition?.toJson(),
      'safety_score': safetyScore,
      'condition_score': conditionScore,
      'overall_score': overallScore,
      'grade': grade,
      'flagged_ingredients': flaggedIngredients?.map((i) => i.toJson()).toList(),
      'safe_ingredients': safeIngredients,
      'recommendation': recommendation,
      'care_tips': careTips?.map((t) => t.toJson()).toList(),
      'safer_alternative': saferAlternative?.toJson(),
      'confidence': confidence,
      'analysis_type': analysisType,
      'personalized_notes': personalizedNotes,
      'report_id': reportId,
      'timestamp': timestamp,
      'error': error,
      'scanned_at': scannedAt.toIso8601String(),
    };
  }

  // Get color based on grade
  Color get gradeColor {
    if (grade == null) return Colors.grey;

    final gradeLetter = grade![0]; // First letter (A, B, C, D, F)
    switch (gradeLetter) {
      case 'A':
        return const Color(0xFF10b981); // Green
      case 'B':
        return const Color(0xFF06b6d4); // Cyan
      case 'C':
        return const Color(0xFFfbbf24); // Yellow
      case 'D':
        return const Color(0xFFf97316); // Orange
      case 'F':
        return const Color(0xFFef4444); // Red
      default:
        return Colors.grey;
    }
  }

  String get gradeEmoji {
    if (grade == null) return '❓';
    final gradeLetter = grade![0];
    switch (gradeLetter) {
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

  String get displayGrade {
    return grade ?? '--';
  }

  String get productTypeBadge {
    switch (productType) {
      case 'consumable':
        return 'Food/Drink';
      case 'container':
        return 'Container';
      case 'cookware':
        return 'Cookware';
      case 'baby_item':
        return 'Baby Item';
      case 'other':
        return 'Other';
      default:
        return 'Unknown';
    }
  }

  IconData get productTypeIcon {
    switch (productType) {
      case 'consumable':
        return Icons.restaurant;
      case 'container':
        return Icons.inventory_2;
      case 'cookware':
        return Icons.restaurant;
      case 'baby_item':
        return Icons.child_care;
      case 'other':
        return Icons.category;
      default:
        return Icons.help_outline;
    }
  }
}

class MaterialAnalysis {
  final String component;
  final String material;
  final int score;
  final List<String> concerns;

  MaterialAnalysis({
    required this.component,
    required this.material,
    required this.score,
    required this.concerns,
  });

  factory MaterialAnalysis.fromJson(Map<String, dynamic> json) {
    return MaterialAnalysis(
      component: json['component'] ?? '',
      material: json['material'] ?? '',
      score: json['score'] ?? 0,
      concerns: List<String>.from(json['concerns'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'component': component,
      'material': material,
      'score': score,
      'concerns': concerns,
    };
  }

  Color get scoreColor {
    if (score >= 80) return const Color(0xFF10b981); // Green
    if (score >= 60) return const Color(0xFF06b6d4); // Cyan
    if (score >= 40) return const Color(0xFFfbbf24); // Yellow
    if (score >= 20) return const Color(0xFFf97316); // Orange
    return const Color(0xFFef4444); // Red
  }
}

class ConditionData {
  final String overall; // new | good | fair | worn | damaged
  final List<String> observations;
  final String? estimatedAge;
  final List<String> concerns;

  ConditionData({
    required this.overall,
    required this.observations,
    this.estimatedAge,
    required this.concerns,
  });

  factory ConditionData.fromJson(Map<String, dynamic> json) {
    return ConditionData(
      overall: json['overall'] ?? 'unknown',
      observations: List<String>.from(json['observations'] ?? []),
      estimatedAge: json['estimated_age'],
      concerns: List<String>.from(json['concerns'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'overall': overall,
      'observations': observations,
      'estimated_age': estimatedAge,
      'concerns': concerns,
    };
  }

  Color get conditionColor {
    switch (overall) {
      case 'new':
        return const Color(0xFF10b981); // Green
      case 'good':
        return const Color(0xFF06b6d4); // Cyan
      case 'fair':
        return const Color(0xFFfbbf24); // Yellow
      case 'worn':
        return const Color(0xFFf97316); // Orange
      case 'damaged':
        return const Color(0xFFef4444); // Red
      default:
        return Colors.grey;
    }
  }

  String get conditionLabel {
    return overall.toUpperCase();
  }
}

class FlaggedIngredient {
  final String ingredient;
  final int hazardScore;
  final String category;
  final List<String> concerns;

  FlaggedIngredient({
    required this.ingredient,
    required this.hazardScore,
    required this.category,
    required this.concerns,
  });

  factory FlaggedIngredient.fromJson(Map<String, dynamic> json) {
    return FlaggedIngredient(
      ingredient: json['ingredient'] ?? '',
      hazardScore: json['hazard_score'] ?? 0,
      category: json['category'] ?? '',
      concerns: List<String>.from(json['concerns'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'ingredient': ingredient,
      'hazard_score': hazardScore,
      'category': category,
      'concerns': concerns,
    };
  }

  Color get hazardColor {
    if (hazardScore >= 80) return const Color(0xFFef4444); // Red - Critical
    if (hazardScore >= 60) return const Color(0xFFf97316); // Orange - High
    if (hazardScore >= 40) return const Color(0xFFfbbf24); // Yellow - Moderate
    return const Color(0xFF06b6d4); // Cyan - Low
  }

  String get hazardLevel {
    if (hazardScore >= 80) return 'CRITICAL';
    if (hazardScore >= 60) return 'HIGH';
    if (hazardScore >= 40) return 'MODERATE';
    return 'LOW';
  }
}

class CareTip {
  final String icon;
  final String tip;
  final String desc;

  CareTip({
    required this.icon,
    required this.tip,
    required this.desc,
  });

  factory CareTip.fromJson(Map<String, dynamic> json) {
    return CareTip(
      icon: json['icon'] ?? '💡',
      tip: json['tip'] ?? '',
      desc: json['desc'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'icon': icon,
      'tip': tip,
      'desc': desc,
    };
  }
}

class SaferAlternative {
  final String name;
  final String reason;
  final String grade;
  final int score;

  SaferAlternative({
    required this.name,
    required this.reason,
    required this.grade,
    required this.score,
  });

  factory SaferAlternative.fromJson(Map<String, dynamic> json) {
    return SaferAlternative(
      name: json['name'] ?? json['suggestion'] ?? '',
      reason: json['reason'] ?? json['why'] ?? '',
      grade: json['grade'] ?? '',
      score: json['score'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'reason': reason,
      'grade': grade,
      'score': score,
    };
  }
}

// V3 Data Models

class IngredientsData {
  final List<IngredientAnalysis> analysis;
  final double averageHazardScore;
  final int totalCount;

  IngredientsData({
    required this.analysis,
    required this.averageHazardScore,
    required this.totalCount,
  });

  factory IngredientsData.fromJson(Map<String, dynamic> json) {
    return IngredientsData(
      analysis: (json['analysis'] as List)
          .map((item) => IngredientAnalysis.fromJson(item))
          .toList(),
      averageHazardScore: (json['average_hazard_score'] as num).toDouble(),
      totalCount: json['total_count'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'analysis': analysis.map((item) => item.toJson()).toList(),
      'average_hazard_score': averageHazardScore,
      'total_count': totalCount,
    };
  }
}

class IngredientAnalysis {
  final String name;
  final int hazardScore;
  final String category;
  final List<String> concerns;
  final bool isSafe;
  final String? source; // 'claude' or 'database'

  IngredientAnalysis({
    required this.name,
    required this.hazardScore,
    required this.category,
    required this.concerns,
    required this.isSafe,
    this.source,
  });

  factory IngredientAnalysis.fromJson(Map<String, dynamic> json) {
    return IngredientAnalysis(
      name: json['name'] as String,
      hazardScore: json['hazard_score'] as int,
      category: json['category'] as String,
      concerns: List<String>.from(json['concerns'] ?? []),
      isSafe: json['is_safe'] as bool,
      source: json['source'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'hazard_score': hazardScore,
      'category': category,
      'concerns': concerns,
      'is_safe': isSafe,
      'source': source,
    };
  }

  Color get hazardColor {
    if (hazardScore >= 7) return const Color(0xFFef4444); // Red
    if (hazardScore >= 4) return const Color(0xFFf97316); // Orange
    return const Color(0xFF10b981); // Green
  }

  String get hazardLevel {
    if (hazardScore >= 7) return 'HIGH';
    if (hazardScore >= 4) return 'MODERATE';
    return 'SAFE';
  }
}

class PositiveAttribute {
  final String claim;
  final int bonusPoints;
  final bool verified;

  PositiveAttribute({
    required this.claim,
    required this.bonusPoints,
    required this.verified,
  });

  factory PositiveAttribute.fromJson(Map<String, dynamic> json) {
    return PositiveAttribute(
      claim: json['claim'] as String,
      bonusPoints: json['bonus_points'] as int,
      verified: json['verified'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'claim': claim,
      'bonus_points': bonusPoints,
      'verified': verified,
    };
  }
}

class ConditionDataV3 {
  final String rating; // new|good|fair|worn|damaged
  final int score;
  final int weightPercentage; // 5 or 15
  final List<String> concerns;

  ConditionDataV3({
    required this.rating,
    required this.score,
    required this.weightPercentage,
    required this.concerns,
  });

  factory ConditionDataV3.fromJson(Map<String, dynamic> json) {
    return ConditionDataV3(
      rating: json['rating'] as String,
      score: json['score'] as int,
      weightPercentage: json['weight_percentage'] as int,
      concerns: List<String>.from(json['concerns'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'rating': rating,
      'score': score,
      'weight_percentage': weightPercentage,
      'concerns': concerns,
    };
  }

  Color get conditionColor {
    switch (rating) {
      case 'new':
        return const Color(0xFF10b981); // Green
      case 'good':
        return const Color(0xFF06b6d4); // Cyan
      case 'fair':
        return const Color(0xFFfbbf24); // Yellow
      case 'worn':
        return const Color(0xFFf97316); // Orange
      case 'damaged':
        return const Color(0xFFef4444); // Red
      default:
        return Colors.grey;
    }
  }

  String get conditionLabel {
    return rating.toUpperCase();
  }
}

class ExpirationData {
  final String status; // fresh|expires_soon|expired|not_applicable
  final bool dateVisible;
  final String? notes;

  ExpirationData({
    required this.status,
    required this.dateVisible,
    this.notes,
  });

  factory ExpirationData.fromJson(Map<String, dynamic> json) {
    return ExpirationData(
      status: json['status'] as String,
      dateVisible: json['date_visible'] as bool,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'date_visible': dateVisible,
      'notes': notes,
    };
  }

  Color get statusColor {
    switch (status) {
      case 'fresh':
        return const Color(0xFF10b981); // Green
      case 'expires_soon':
        return const Color(0xFFfbbf24); // Yellow
      case 'expired':
        return const Color(0xFFef4444); // Red
      default:
        return Colors.grey;
    }
  }

  String get statusLabel {
    switch (status) {
      case 'fresh':
        return 'FRESH';
      case 'expires_soon':
        return 'EXPIRES SOON';
      case 'expired':
        return 'EXPIRED';
      default:
        return 'N/A';
    }
  }
}
