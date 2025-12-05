// Basic Flutter widget test for Cancer Detector app

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:cancer_detector/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const CancerDetectorApp());

    // Verify the app loads without crashing
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
