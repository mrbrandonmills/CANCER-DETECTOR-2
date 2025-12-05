import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../services/scan_history_service.dart';
import '../models/scan_result.dart';
import 'result_screen.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan History'),
        actions: [
          Consumer<ScanHistoryService>(
            builder: (context, service, _) {
              if (service.history.isEmpty) return const SizedBox.shrink();
              return IconButton(
                icon: const Icon(Icons.delete_outline),
                onPressed: () => _confirmClearHistory(context, service),
              );
            },
          ),
        ],
      ),
      body: Consumer<ScanHistoryService>(
        builder: (context, historyService, child) {
          if (historyService.history.isEmpty) {
            return _buildEmptyState(context);
          }
          
          return CustomScrollView(
            slivers: [
              // Stats header
              SliverToBoxAdapter(
                child: _buildStatsHeader(context, historyService),
              ),
              
              // History list
              SliverPadding(
                padding: const EdgeInsets.all(16),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final scan = historyService.history[index];
                      return _buildHistoryItem(context, scan, index);
                    },
                    childCount: historyService.history.length,
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
  
  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.history,
            size: 80,
            color: Theme.of(context).colorScheme.outline,
          ),
          const SizedBox(height: 16),
          Text(
            'No Scans Yet',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            'Scan products to build your history\nand track your overall cancer score.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.camera_alt),
            label: const Text('Scan Your First Product'),
          ),
        ],
      ),
    );
  }
  
  Widget _buildStatsHeader(BuildContext context, ScanHistoryService service) {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _getScoreColor(service.overallScoreColor).withOpacity(0.8),
            _getScoreColor(service.overallScoreColor),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _statItem(
                context,
                '${service.overallScore.round()}',
                'Overall\nScore',
                isLarge: true,
              ),
              _statItem(
                context,
                '${service.totalScans}',
                'Products\nScanned',
              ),
              _statItem(
                context,
                '${service.carcinogensFound}',
                'Carcinogens\nFound',
              ),
            ],
          ),
          if (service.worstScan != null) ...[
            const Divider(color: Colors.white30, height: 32),
            Row(
              children: [
                const Icon(Icons.warning_amber, color: Colors.white70, size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Worst: ${service.worstScan!.productName} (${_getDisplayScore(service.worstScan!)})',
                    style: const TextStyle(color: Colors.white70, fontSize: 13),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    ).animate().fadeIn().slideY(begin: -0.2);
  }
  
  Widget _statItem(BuildContext context, String value, String label, {bool isLarge = false}) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            color: Colors.white,
            fontSize: isLarge ? 36 : 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: Colors.white.withOpacity(0.8),
            fontSize: 11,
          ),
        ),
      ],
    );
  }
  
  Widget _buildHistoryItem(BuildContext context, ScanResult scan, int index) {
    final dateFormat = DateFormat('MMM d, yyyy • h:mm a');
    final gradeColor = scan.gradeColor;
    final displayText = scan.displayGrade;
    final flaggedCount = scan.flaggedIngredients?.length ?? 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: gradeColor.withOpacity(0.3),
        ),
      ),
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ResultScreen(result: scan),
            ),
          );
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Grade circle
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: gradeColor.withOpacity(0.1),
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: gradeColor,
                    width: 3,
                  ),
                ),
                child: Center(
                  child: Text(
                    displayText,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: gradeColor,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),

              // Product info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      scan.productName ?? 'Unknown Product',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      dateFormat.format(scan.scannedAt),
                      style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
                      ),
                    ),
                    if (flaggedCount > 0) ...[
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.red.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          '⚠️ $flaggedCount flagged ingredient${flaggedCount > 1 ? 's' : ''}',
                          style: const TextStyle(
                            fontSize: 11,
                            color: Colors.red,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),

              // Arrow
              Icon(
                Icons.arrow_forward_ios,
                size: 16,
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.3),
              ),
            ],
          ),
        ),
      ),
    ).animate().fadeIn(delay: (50 * index).ms).slideX(begin: 0.1);
  }
  
  void _confirmClearHistory(BuildContext context, ScanHistoryService service) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear History?'),
        content: const Text(
          'This will delete all scan history and reset your overall score to 100. This cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              service.clearHistory();
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('History cleared')),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
  }
  
  Color _getScoreColor(String colorName) {
    switch (colorName) {
      case 'green':
        return const Color(0xFF4CAF50);
      case 'yellow':
        return const Color(0xFFFFC107);
      case 'orange':
        return const Color(0xFFFF9800);
      case 'red':
        return const Color(0xFFF44336);
      default:
        return const Color(0xFF4CAF50);
    }
  }

  String _getDisplayScore(ScanResult scan) {
    // Show grade if available, otherwise show score/100
    if (scan.grade != null) {
      return scan.grade!;
    }
    // For backwards compatibility with old data that doesn't have grade
    final score = scan.overallScore ?? 0;
    return '$score/100';
  }
}
