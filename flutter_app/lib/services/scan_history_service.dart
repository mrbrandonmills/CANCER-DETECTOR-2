import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';
import '../models/scan_result.dart';

class ScanHistoryService extends ChangeNotifier {
  List<ScanResult> _history = [];
  double _overallScore = 100.0;
  
  List<ScanResult> get history => _history;
  double get overallScore => _overallScore;
  int get totalScans => _history.length;
  
  String get overallScoreColor {
    if (_overallScore >= 80) return 'green';
    if (_overallScore >= 60) return 'yellow';
    if (_overallScore >= 40) return 'orange';
    return 'red';
  }
  
  ScanHistoryService() {
    _loadHistory();
  }
  
  Future<void> _loadHistory() async {
    try {
      final box = Hive.box('scan_history');
      final historyJson = box.get('history', defaultValue: '[]');
      final List<dynamic> decoded = jsonDecode(historyJson);
      
      _history = decoded.map((item) => ScanResult.fromJson(item)).toList();
      _calculateOverallScore();
      notifyListeners();
    } catch (e) {
      print('Error loading history: $e');
    }
  }
  
  Future<void> _saveHistory() async {
    try {
      final box = Hive.box('scan_history');
      final historyJson = jsonEncode(_history.map((s) => s.toJson()).toList());
      await box.put('history', historyJson);
    } catch (e) {
      print('Error saving history: $e');
    }
  }
  
  Future<void> addScan(ScanResult result) async {
    if (result.success && result.overallScore != null) {
      _history.insert(0, result); // Add to beginning
      _calculateOverallScore();
      await _saveHistory();
      notifyListeners();
    }
  }
  
  void _calculateOverallScore() {
    if (_history.isEmpty) {
      _overallScore = 100.0;
      return;
    }

    // Calculate weighted average (recent scans weighted more)
    double totalWeight = 0;
    double weightedSum = 0;

    for (int i = 0; i < _history.length; i++) {
      final scan = _history[i];
      if (scan.overallScore != null) {
        // More recent = higher weight (1.0 for most recent, decreasing)
        double weight = 1.0 / (i + 1);
        weightedSum += scan.overallScore! * weight;
        totalWeight += weight;
      }
    }

    if (totalWeight > 0) {
      _overallScore = weightedSum / totalWeight;
    } else {
      _overallScore = 100.0;
    }
  }
  
  Future<void> clearHistory() async {
    _history.clear();
    _overallScore = 100.0;
    await _saveHistory();
    notifyListeners();
  }
  
  ScanResult? get worstScan {
    if (_history.isEmpty) return null;
    return _history.reduce((a, b) {
      if (a.overallScore == null) return b;
      if (b.overallScore == null) return a;
      return a.overallScore! < b.overallScore! ? a : b;
    });
  }

  ScanResult? get bestScan {
    if (_history.isEmpty) return null;
    return _history.reduce((a, b) {
      if (a.overallScore == null) return b;
      if (b.overallScore == null) return a;
      return a.overallScore! > b.overallScore! ? a : b;
    });
  }
  
  int get carcinogensFound {
    int count = 0;
    for (final scan in _history) {
      count += scan.flaggedIngredients?.length ?? 0;
    }
    return count;
  }
}
