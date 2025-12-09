import 'package:flutter/material.dart';

/// Premium dark theme color palette for TrueCancer
/// Inspired by luxury health-tech aesthetic (Apple Health meets luxury brands)
class AppColors {
  // Primary dark theme
  static const background = Color(0xFF0A0A0F);        // Near black
  static const surfaceCard = Color(0xFF16161F);       // Elevated surface
  static const surfaceCardHover = Color(0xFF1E1E2A);  // Hover state

  // Accent gradient (premium teal/cyan + purple)
  static const accentPrimary = Color(0xFF06B6D4);     // Cyan
  static const accentSecondary = Color(0xFF8B5CF6);   // Purple
  static const accentGlow = Color(0xFF06B6D4);        // For glows/shadows

  // Text hierarchy
  static const textPrimary = Color(0xFFFAFAFA);       // White
  static const textSecondary = Color(0xFFA1A1AA);     // Muted
  static const textTertiary = Color(0xFF52525B);      // Very muted

  // Grade colors (safety rating system)
  static const gradeA = Color(0xFF22C55E);            // Green
  static const gradeB = Color(0xFF84CC16);            // Lime
  static const gradeC = Color(0xFFFACC15);            // Yellow
  static const gradeD = Color(0xFFF97316);            // Orange
  static const gradeF = Color(0xFFEF4444);            // Red

  /// Get color for a specific grade letter
  static Color getGradeColor(String grade) {
    switch (grade.toUpperCase()) {
      case 'F':
        return gradeF;
      case 'D':
        return gradeD;
      case 'C':
        return gradeC;
      case 'B':
        return gradeB;
      case 'A':
      case 'A+':
        return gradeA;
      default:
        return textSecondary; // Gray for unknown grades
    }
  }

  /// Premium gradient for scan button and hero elements
  static const LinearGradient accentGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [accentPrimary, accentSecondary],
  );
}
