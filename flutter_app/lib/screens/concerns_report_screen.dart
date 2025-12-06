import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../services/scan_history_service.dart';
import '../models/scan_result.dart';
import 'result_screen.dart';

class ConcernsReportScreen extends StatelessWidget {
  const ConcernsReportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0f172a),
      appBar: AppBar(
        title: const Text('Carcinogens & Concerns'),
        backgroundColor: const Color(0xFF1e293b),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Consumer<ScanHistoryService>(
        builder: (context, historyService, child) {
          // Filter scans with grade D or worse (score <= 49)
          final concernScans = historyService.scans.where((scan) {
            // Check if scan has a gradeValue or safetyScore
            final score = scan.gradeValue ?? scan.safetyScore ?? 100;
            return score <= 49; // D grade or worse
          }).toList();

          if (concernScans.isEmpty) {
            return _buildEmptyState(context);
          }

          return CustomScrollView(
            slivers: [
              SliverPadding(
                padding: const EdgeInsets.all(20),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    // Header Stats
                    _buildHeaderStats(context, concernScans.length)
                        .animate()
                        .fadeIn(duration: 500.ms)
                        .slideY(begin: -0.2),

                    const SizedBox(height: 24),

                    // Info Card
                    _buildInfoCard(context)
                        .animate()
                        .fadeIn(delay: 200.ms)
                        .slideY(begin: 0.1),

                    const SizedBox(height: 24),

                    // Section Title
                    const Text(
                      'Products of Concern',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ).animate().fadeIn(delay: 300.ms),

                    const SizedBox(height: 16),
                  ]),
                ),
              ),

              // List of concern items
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final scan = concernScans[index];
                      return _buildConcernCard(context, scan, index)
                          .animate(delay: ((index + 4) * 100).ms)
                          .fadeIn(duration: 300.ms)
                          .slideX(begin: -0.1);
                    },
                    childCount: concernScans.length,
                  ),
                ),
              ),

              const SliverPadding(padding: EdgeInsets.only(bottom: 40)),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF10b981).withOpacity(0.1),
              ),
              child: const Icon(
                Icons.check_circle_outline,
                size: 80,
                color: Color(0xFF10b981),
              ),
            ).animate().scale(duration: 500.ms),
            const SizedBox(height: 32),
            const Text(
              'No Concerns Found!',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ).animate(delay: 200.ms).fadeIn(),
            const SizedBox(height: 12),
            Text(
              'All your scanned products are rated C or better.\nKeep up the healthy choices!',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.white.withOpacity(0.7),
                height: 1.5,
              ),
            ).animate(delay: 300.ms).fadeIn(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderStats(BuildContext context, int concernCount) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFFef4444),
            Color(0xFFf97316),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFef4444).withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          const Icon(
            Icons.warning_amber_rounded,
            size: 48,
            color: Colors.white,
          ),
          const SizedBox(height: 12),
          Text(
            '$concernCount',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 56,
              fontWeight: FontWeight.bold,
              height: 1,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            concernCount == 1 ? 'Product of Concern' : 'Products of Concern',
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Grade D or worse (Score ≤ 49)',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1e293b),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Colors.white.withOpacity(0.1),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF3b82f6).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.info_outline,
                  color: Color(0xFF3b82f6),
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              const Text(
                'About This Report',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            'This report shows all products you\'ve scanned that received a grade of D or worse (score ≤ 49).\n\nThese items contain ingredients or materials that may pose health concerns and should be avoided or limited.',
            style: TextStyle(
              color: Colors.white.withOpacity(0.8),
              fontSize: 14,
              height: 1.6,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildGradeLegend('F', const Color(0xFFef4444), '0-29'),
              const SizedBox(width: 12),
              _buildGradeLegend('D', const Color(0xFFf97316), '30-49'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildGradeLegend(String grade, Color color, String range) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Center(
              child: Text(
                grade,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            range,
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConcernCard(BuildContext context, ScanResult scan, int index) {
    final score = scan.gradeValue ?? scan.safetyScore ?? 0;
    final grade = scan.grade ?? _getGradeFromScore(score);
    final gradeColor = _getGradeColor(grade);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ResultScreen(result: scan),
            ),
          ),
          borderRadius: BorderRadius.circular(16),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF1e293b),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: gradeColor.withOpacity(0.3),
                width: 2,
              ),
            ),
            child: Row(
              children: [
                // Grade Badge
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: gradeColor,
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: [
                      BoxShadow(
                        color: gradeColor.withOpacity(0.3),
                        blurRadius: 8,
                        spreadRadius: 1,
                      ),
                    ],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        grade,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        '$score',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.9),
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),

                // Product Info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        scan.productName ?? 'Unknown Product',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (scan.brand != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          scan.brand!,
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.6),
                            fontSize: 13,
                          ),
                        ),
                      ],
                      const SizedBox(height: 8),
                      Text(
                        _getConcernSummary(scan),
                        style: TextStyle(
                          color: gradeColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),

                // Arrow
                Icon(
                  Icons.arrow_forward_ios,
                  size: 16,
                  color: Colors.white.withOpacity(0.3),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _getGradeFromScore(int score) {
    if (score >= 95) return 'A+';
    if (score >= 85) return 'A';
    if (score >= 70) return 'B';
    if (score >= 50) return 'C';
    if (score >= 30) return 'D';
    return 'F';
  }

  Color _getGradeColor(String grade) {
    switch (grade) {
      case 'F':
        return const Color(0xFFef4444);
      case 'D':
        return const Color(0xFFf97316);
      default:
        return const Color(0xFFfbbf24);
    }
  }

  String _getConcernSummary(ScanResult scan) {
    final flaggedCount = scan.flaggedIngredients?.length ?? 0;
    if (flaggedCount > 0) {
      return '$flaggedCount flagged ingredient${flaggedCount > 1 ? 's' : ''}';
    }
    return 'Contains concerning materials';
  }
}
