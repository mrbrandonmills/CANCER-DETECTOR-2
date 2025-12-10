// Deep Research Models for Premium Feature

enum JobStatus {
  pending,
  processing,
  completed,
  failed
}

class DeepResearchRequest {
  final String productName;
  final String? brand;
  final String category;
  final List<String> ingredients;

  DeepResearchRequest({
    required this.productName,
    this.brand,
    required this.category,
    required this.ingredients,
  });

  Map<String, dynamic> toJson() => {
    'product_name': productName,
    'brand': brand,
    'category': category,
    'ingredients': ingredients,
  };
}

class DeepResearchJob {
  final String jobId;
  final JobStatus status;
  final int progress;
  final String? currentStep;
  final DateTime createdAt;
  final DateTime? completedAt;
  final DeepResearchResult? result;
  final String? error;

  DeepResearchJob({
    required this.jobId,
    required this.status,
    required this.progress,
    this.currentStep,
    required this.createdAt,
    this.completedAt,
    this.result,
    this.error,
  });

  factory DeepResearchJob.fromJson(Map<String, dynamic> json) {
    JobStatus parseStatus(String? value) {
      switch (value?.toLowerCase()) {
        case 'pending':
          return JobStatus.pending;
        case 'processing':
          return JobStatus.processing;
        case 'completed':
          return JobStatus.completed;
        case 'failed':
          return JobStatus.failed;
        default:
          return JobStatus.pending;
      }
    }

    return DeepResearchJob(
      jobId: json['job_id'] ?? json['jobId'] ?? '',
      status: parseStatus(json['status']),
      progress: json['progress'] ?? 0,
      currentStep: json['current_step'],
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'])
          : null,
      result: json['result'] != null
          ? DeepResearchResult.fromJson(json['result'])
          : null,
      error: json['error'],
    );
  }
}

class DeepResearchResult {
  final String productName;
  final String? brand;
  final String category;
  final Map<String, String> report;
  final String fullReport;
  final DateTime generatedAt;

  DeepResearchResult({
    required this.productName,
    this.brand,
    required this.category,
    required this.report,
    required this.fullReport,
    required this.generatedAt,
  });

  factory DeepResearchResult.fromJson(Map<String, dynamic> json) {
    return DeepResearchResult(
      productName: json['product_name'] ?? '',
      brand: json['brand'],
      category: json['category'] ?? '',
      report: Map<String, String>.from(json['report'] ?? {}),
      fullReport: json['full_report'] ?? '',
      generatedAt: json['generated_at'] != null
          ? DateTime.parse(json['generated_at'])
          : DateTime.now(),
    );
  }
}
