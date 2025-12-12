import 'dart:io';
import 'dart:typed_data';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:intl/intl.dart';
import '../models/deep_research_models.dart';

/// PDF Generation Service for Deep Research Reports
/// Creates professional PDF reports from DeepResearchResult data
class PdfService {
  // Brand colors
  static const PdfColor primaryPurple = PdfColor.fromInt(0xFF8b5cf6);
  static const PdfColor darkBackground = PdfColor.fromInt(0xFF0a0a0a);
  static const PdfColor cardBackground = PdfColor.fromInt(0xFF1a1a1a);
  static const PdfColor textPrimary = PdfColor.fromInt(0xFFFFFFFF);
  static const PdfColor textSecondary = PdfColor.fromInt(0xFFa1a1aa);
  static const PdfColor accentCyan = PdfColor.fromInt(0xFF06b6d4);

  /// Generate PDF from DeepResearchResult
  /// Uses built-in PDF fonts to avoid memory crashes from Google Fonts downloads
  Future<Uint8List> generatePdf(DeepResearchResult result) async {
    final pdf = pw.Document(
      theme: pw.ThemeData.withFont(
        // Use built-in Helvetica fonts to avoid memory-heavy Google Font downloads
        // This prevents "not enough memory" crashes on iOS devices
        base: pw.Font.helvetica(),
        bold: pw.Font.helveticaBold(),
        italic: pw.Font.helveticaOblique(),
        boldItalic: pw.Font.helveticaBoldOblique(),
      ),
    );

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(40),
        header: (context) => _buildHeader(result, context),
        footer: (context) => _buildFooter(context),
        build: (context) => _buildContent(result),
      ),
    );

    return pdf.save();
  }

  /// Build PDF header
  pw.Widget _buildHeader(DeepResearchResult result, pw.Context context) {
    if (context.pageNumber > 1) {
      return pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 20),
        child: pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            pw.Text(
              'TrueCancer Deep Research',
              style: pw.TextStyle(
                fontSize: 10,
                color: PdfColors.grey600,
              ),
            ),
            pw.Text(
              result.productName,
              style: pw.TextStyle(
                fontSize: 10,
                color: PdfColors.grey600,
                fontStyle: pw.FontStyle.italic,
              ),
            ),
          ],
        ),
      );
    }

    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 30),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          // Title bar
          pw.Container(
            padding: const pw.EdgeInsets.all(20),
            decoration: pw.BoxDecoration(
              color: primaryPurple,
              borderRadius: pw.BorderRadius.circular(8),
            ),
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Row(
                  children: [
                    pw.Text(
                      '🔬 ',
                      style: const pw.TextStyle(fontSize: 24),
                    ),
                    pw.Text(
                      'DEEP RESEARCH REPORT',
                      style: pw.TextStyle(
                        fontSize: 20,
                        fontWeight: pw.FontWeight.bold,
                        color: PdfColors.white,
                        letterSpacing: 1,
                      ),
                    ),
                  ],
                ),
                pw.SizedBox(height: 12),
                pw.Text(
                  result.productName,
                  style: pw.TextStyle(
                    fontSize: 16,
                    fontWeight: pw.FontWeight.bold,
                    color: PdfColors.white,
                  ),
                ),
                if (result.brand != null) ...[
                  pw.SizedBox(height: 4),
                  pw.Text(
                    'by ${result.brand}',
                    style: pw.TextStyle(
                      fontSize: 12,
                      color: PdfColors.white.shade(0.8),
                    ),
                  ),
                ],
                pw.SizedBox(height: 8),
                pw.Text(
                  'Generated: ${DateFormat('MMMM d, yyyy • h:mm a').format(result.generatedAt)}',
                  style: pw.TextStyle(
                    fontSize: 10,
                    color: PdfColors.white.shade(0.7),
                  ),
                ),
              ],
            ),
          ),
          pw.SizedBox(height: 10),
          // Disclaimer
          pw.Container(
            padding: const pw.EdgeInsets.all(12),
            decoration: pw.BoxDecoration(
              color: PdfColors.amber50,
              borderRadius: pw.BorderRadius.circular(4),
              border: pw.Border.all(color: PdfColors.amber200),
            ),
            child: pw.Text(
              'This report is for educational purposes only and does not constitute medical advice. '
              'Always consult healthcare professionals for health-related decisions.',
              style: pw.TextStyle(
                fontSize: 8,
                color: PdfColors.amber900,
                fontStyle: pw.FontStyle.italic,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Build PDF footer
  pw.Widget _buildFooter(pw.Context context) {
    return pw.Container(
      margin: const pw.EdgeInsets.only(top: 20),
      padding: const pw.EdgeInsets.only(top: 10),
      decoration: const pw.BoxDecoration(
        border: pw.Border(
          top: pw.BorderSide(color: PdfColors.grey300, width: 0.5),
        ),
      ),
      child: pw.Row(
        mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
        children: [
          pw.Text(
            'TrueCancer™ - AI-Powered Product Safety',
            style: pw.TextStyle(
              fontSize: 8,
              color: PdfColors.grey500,
            ),
          ),
          pw.Text(
            'Page ${context.pageNumber} of ${context.pagesCount}',
            style: pw.TextStyle(
              fontSize: 8,
              color: PdfColors.grey500,
            ),
          ),
        ],
      ),
    );
  }

  /// Build main content sections
  List<pw.Widget> _buildContent(DeepResearchResult result) {
    final List<pw.Widget> content = [];

    // Section icons mapping
    final sectionIcons = {
      'Corporate Ownership Investigation': '🏢',
      'Deep Ingredient Analysis': '🔍',
      'Supply Chain Transparency': '🚚',
      'Regulatory History': '⚖️',
      'Better Alternatives': '✨',
      'Actionable Recommendations': '📋',
      'Executive Summary': '📊',
    };

    // Add each report section
    for (final entry in result.report.entries) {
      final title = entry.key;
      final sectionContent = entry.value.trim();

      if (sectionContent.isEmpty) continue;

      final icon = sectionIcons.entries
          .firstWhere(
            (e) => title.toLowerCase().contains(e.key.toLowerCase().split(' ').first),
            orElse: () => const MapEntry('', '📄'),
          )
          .value;

      content.add(
        pw.Container(
          margin: const pw.EdgeInsets.only(bottom: 20),
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              // Section header
              pw.Container(
                padding: const pw.EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: pw.BoxDecoration(
                  color: PdfColors.grey100,
                  borderRadius: pw.BorderRadius.circular(4),
                ),
                child: pw.Row(
                  children: [
                    pw.Text(
                      '$icon ',
                      style: const pw.TextStyle(fontSize: 14),
                    ),
                    pw.Expanded(
                      child: pw.Text(
                        title.toUpperCase(),
                        style: pw.TextStyle(
                          fontSize: 12,
                          fontWeight: pw.FontWeight.bold,
                          color: PdfColors.grey800,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: 12),
              // Section content
              pw.Container(
                padding: const pw.EdgeInsets.all(16),
                decoration: pw.BoxDecoration(
                  border: pw.Border.all(color: PdfColors.grey200),
                  borderRadius: pw.BorderRadius.circular(4),
                ),
                child: pw.Text(
                  sectionContent,
                  style: pw.TextStyle(
                    fontSize: 10,
                    color: PdfColors.grey700,
                    lineSpacing: 4,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    // Add generation info at the end
    content.add(
      pw.Container(
        margin: const pw.EdgeInsets.only(top: 20),
        padding: const pw.EdgeInsets.all(16),
        decoration: pw.BoxDecoration(
          color: PdfColors.purple50,
          borderRadius: pw.BorderRadius.circular(4),
          border: pw.Border.all(color: PdfColors.purple100),
        ),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              'Report Information',
              style: pw.TextStyle(
                fontSize: 10,
                fontWeight: pw.FontWeight.bold,
                color: PdfColors.purple800,
              ),
            ),
            pw.SizedBox(height: 8),
            pw.Text(
              'Product: ${result.productName}',
              style: pw.TextStyle(fontSize: 9, color: PdfColors.purple700),
            ),
            if (result.brand != null)
              pw.Text(
                'Brand: ${result.brand}',
                style: pw.TextStyle(fontSize: 9, color: PdfColors.purple700),
              ),
            pw.Text(
              'Category: ${result.category}',
              style: pw.TextStyle(fontSize: 9, color: PdfColors.purple700),
            ),
            pw.Text(
              'Generated: ${DateFormat('yyyy-MM-dd HH:mm:ss').format(result.generatedAt)}',
              style: pw.TextStyle(fontSize: 9, color: PdfColors.purple700),
            ),
          ],
        ),
      ),
    );

    return content;
  }

  /// Save PDF to device and return file path
  Future<String> savePdf(Uint8List pdfBytes, String productName) async {
    final directory = await getApplicationDocumentsDirectory();
    final sanitizedName = productName
        .replaceAll(RegExp(r'[^\w\s-]'), '')
        .replaceAll(RegExp(r'\s+'), '_')
        .toLowerCase();
    final timestamp = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
    final fileName = 'truecancer_report_${sanitizedName}_$timestamp.pdf';
    final file = File('${directory.path}/$fileName');
    await file.writeAsBytes(pdfBytes);
    return file.path;
  }

  /// Share PDF via system share dialog
  Future<void> sharePdf(Uint8List pdfBytes, String productName) async {
    final filePath = await savePdf(pdfBytes, productName);
    await Share.shareXFiles(
      [XFile(filePath)],
      subject: 'TrueCancer Deep Research Report - $productName',
      text: 'Deep Research Report for $productName generated by TrueCancer.',
    );
  }

  /// Print PDF directly
  Future<void> printPdf(Uint8List pdfBytes, String productName) async {
    await Printing.layoutPdf(
      onLayout: (format) async => pdfBytes,
      name: 'TrueCancer_Report_$productName',
    );
  }

  /// Preview PDF in system viewer
  Future<void> previewPdf(Uint8List pdfBytes) async {
    await Printing.sharePdf(
      bytes: pdfBytes,
      filename: 'TrueCancer_Deep_Research_Report.pdf',
    );
  }
}
