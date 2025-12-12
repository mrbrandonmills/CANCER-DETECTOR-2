import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/deep_research_models.dart';
import '../services/api_service.dart';
import '../services/pdf_service.dart';
import '../theme/app_colors.dart';
import 'dart:async';


class DeepResearchScreen extends StatefulWidget {
  final String productName;
  final String? brand;
  final String category;
  final List<String> ingredients;

  const DeepResearchScreen({
    super.key,
    required this.productName,
    this.brand,
    required this.category,
    required this.ingredients,
  });

  @override
  State<DeepResearchScreen> createState() => _DeepResearchScreenState();
}

class _DeepResearchScreenState extends State<DeepResearchScreen> {
  final ApiService _apiService = ApiService();
  final PdfService _pdfService = PdfService();
  DeepResearchJob? _currentJob;
  Timer? _pollTimer;
  String? _errorMessage;
  bool _isGeneratingPdf = false;

  @override
  void initState() {
    super.initState();
    _startDeepResearch();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _startDeepResearch() async {
    try {
      final jobId = await _apiService.startDeepResearch(
        productName: widget.productName,
        brand: widget.brand,
        category: widget.category,
        ingredients: widget.ingredients,
      );

      _startPolling(jobId);
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to start deep research: ${e.toString()}';
      });
    }
  }

  void _startPolling(String jobId) {
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      try {
        final job = await _apiService.getJobStatus(jobId);

        setState(() {
          _currentJob = job;
        });

        if (job.status == JobStatus.completed || job.status == JobStatus.failed) {
          timer.cancel();
          if (job.status == JobStatus.failed) {
            setState(() {
              _errorMessage = job.error ?? 'Research failed';
            });
          }
        }
      } catch (e) {
        debugPrint('Polling error: $e');
      }
    });
  }

  /// Generate and share PDF report
  Future<void> _sharePdfReport() async {
    if (_currentJob?.result == null) return;

    setState(() {
      _isGeneratingPdf = true;
    });

    try {
      final result = _currentJob!.result!;
      final pdfBytes = await _pdfService.generatePdf(result);
      await _pdfService.sharePdf(pdfBytes, result.productName);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to generate PDF: ${e.toString()}'),
            backgroundColor: AppColors.gradeF,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isGeneratingPdf = false;
        });
      }
    }
  }

  /// Print PDF report directly
  Future<void> _printPdfReport() async {
    if (_currentJob?.result == null) return;

    setState(() {
      _isGeneratingPdf = true;
    });

    try {
      final result = _currentJob!.result!;
      final pdfBytes = await _pdfService.generatePdf(result);
      await _pdfService.printPdf(pdfBytes, result.productName);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to print PDF: ${e.toString()}'),
            backgroundColor: AppColors.gradeF,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isGeneratingPdf = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () {
            _pollTimer?.cancel();
            Navigator.pop(context);
          },
        ),
        title: const Text(
          'Deep Research',
          style: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
        actions: [
          // Show PDF actions only when research is complete
          if (_currentJob?.status == JobStatus.completed && _currentJob?.result != null) ...[
            IconButton(
              icon: _isGeneratingPdf
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Icon(Icons.share, color: Colors.white, size: 22),
              onPressed: _isGeneratingPdf ? null : _sharePdfReport,
              tooltip: 'Share PDF Report',
            ),
            IconButton(
              icon: const Icon(Icons.print, color: Colors.white, size: 22),
              onPressed: _isGeneratingPdf ? null : _printPdfReport,
              tooltip: 'Print Report',
            ),
          ],
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_errorMessage != null) {
      return _buildErrorState();
    }

    if (_currentJob?.status == JobStatus.completed && _currentJob?.result != null) {
      return _buildCompletedState();
    }

    return _buildLoadingState();
  }

  Widget _buildLoadingState() {
    final progress = _currentJob?.progress ?? 0;
    final currentStep = _currentJob?.currentStep ?? 'Initializing...';

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                gradient: AppColors.accentGradient,
                shape: BoxShape.circle,
              ),
              child: const Center(
                child: Text(
                  '🔬',
                  style: TextStyle(fontSize: 60),
                ),
              ),
            )
            .animate(onPlay: (controller) => controller.repeat())
            .shimmer(duration: 2000.ms, color: Colors.white.withOpacity(0.3))
            .animate()
            .scale(duration: 600.ms, curve: Curves.elasticOut),

            const SizedBox(height: 40),

            Text(
              'Conducting Deep Research',
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 24,
                fontWeight: FontWeight.w700,
              ),
            ).animate().fadeIn(duration: 600.ms),

            const SizedBox(height: 12),

            Text(
              currentStep,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 16,
              ),
              textAlign: TextAlign.center,
            ).animate().fadeIn(duration: 600.ms, delay: 200.ms),

            const SizedBox(height: 40),

            SizedBox(
              width: 250,
              child: Column(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: LinearProgressIndicator(
                      value: progress / 100,
                      minHeight: 8,
                      backgroundColor: AppColors.surfaceCard,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        AppColors.accentPrimary,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '$progress%',
                    style: const TextStyle(
                      color: AppColors.textTertiary,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ).animate().fadeIn(duration: 600.ms, delay: 400.ms),

            const SizedBox(height: 60),

            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surfaceCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppColors.accentPrimary.withOpacity(0.2),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.info_outline,
                    color: AppColors.accentPrimary,
                    size: 20,
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    'This typically takes 30-60 seconds',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ).animate().fadeIn(duration: 600.ms, delay: 600.ms),
          ],
        ),
      ),
    );
  }

  Widget _buildCompletedState() {
    final result = _currentJob!.result!;

    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.all(20),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _buildResultHeader(result),
              const SizedBox(height: 24),

              ...result.report.entries.map((entry) =>
                _buildReportSection(entry.key, entry.value)
              ),

              const SizedBox(height: 20),

              // PDF Export Buttons
              _buildPdfExportSection(),

              const SizedBox(height: 40),
            ]),
          ),
        ),
      ],
    );
  }

  /// Build PDF export action buttons
  Widget _buildPdfExportSection() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.accentPrimary.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.picture_as_pdf,
                color: AppColors.accentPrimary,
                size: 24,
              ),
              const SizedBox(width: 12),
              const Text(
                'EXPORT REPORT',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildExportButton(
                  icon: Icons.share,
                  label: 'Share PDF',
                  onPressed: _isGeneratingPdf ? null : _sharePdfReport,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildExportButton(
                  icon: Icons.print,
                  label: 'Print',
                  onPressed: _isGeneratingPdf ? null : _printPdfReport,
                ),
              ),
            ],
          ),
          if (_isGeneratingPdf) ...[
            const SizedBox(height: 16),
            Center(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        AppColors.accentPrimary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    'Generating PDF...',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    ).animate().fadeIn(duration: 600.ms, delay: 300.ms).slideY(
      begin: 0.1,
      duration: 600.ms,
      curve: Curves.easeOutQuart,
    );
  }

  Widget _buildExportButton({
    required IconData icon,
    required String label,
    VoidCallback? onPressed,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
          decoration: BoxDecoration(
            gradient: onPressed != null
                ? AppColors.accentGradient
                : null,
            color: onPressed == null
                ? AppColors.surfaceCardHover.withOpacity(0.5)
                : null,
            borderRadius: BorderRadius.circular(12),
            boxShadow: onPressed != null
                ? [
                    BoxShadow(
                      color: AppColors.accentGlow.withOpacity(0.2),
                      blurRadius: 12,
                      spreadRadius: 1,
                    ),
                  ]
                : null,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                color: Colors.white,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildResultHeader(DeepResearchResult result) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: AppColors.accentGradient,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: AppColors.accentGlow.withOpacity(0.3),
            blurRadius: 20,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '🔬 Deep Research Complete',
            style: TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            result.productName,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w500,
            ),
          ),
          if (result.brand != null) ...[
            const SizedBox(height: 4),
            Text(
              'by ${result.brand}',
              style: TextStyle(
                color: Colors.white.withOpacity(0.8),
                fontSize: 14,
              ),
            ),
          ],
          const SizedBox(height: 8),
          Text(
            'Generated ${_formatDateTime(result.generatedAt)}',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 12,
            ),
          ),
        ],
      ),
    ).animate().fadeIn(duration: 600.ms).scale(
      duration: 600.ms,
      curve: Curves.elasticOut,
    );
  }

  Widget _buildReportSection(String title, String content) {
    final cleanContent = content.trim();
    if (cleanContent.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.surfaceCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppColors.surfaceCardHover.withOpacity(0.3),
          ),
        ),
        child: ExpansionTile(
          initiallyExpanded: true,
          tilePadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          childrenPadding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
          title: Text(
            title,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
          iconColor: AppColors.accentPrimary,
          collapsedIconColor: AppColors.textSecondary,
          children: [
            Container(
              width: double.infinity,
              child: Text(
                cleanContent,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 14,
                  height: 1.6,
                ),
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(duration: 600.ms).slideY(
      begin: 0.1,
      duration: 600.ms,
      curve: Curves.easeOutQuart,
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppColors.gradeF.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.error_outline,
                color: AppColors.gradeF,
                size: 40,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Research Failed',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              _errorMessage ?? 'An unexpected error occurred',
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _errorMessage = null;
                  _currentJob = null;
                });
                _startDeepResearch();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.accentPrimary,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                'Try Again',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inMinutes < 1) {
      return 'just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes} minutes ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours} hours ago';
    } else {
      return '${difference.inDays} days ago';
    }
  }
}
