import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/scan_result_v4.dart';
import '../theme/app_colors.dart';
import 'deep_research_dialog.dart';

class ResultScreenV4 extends StatelessWidget {
  final ScanResultV4 result;

  const ResultScreenV4({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0a0a0a), // Pure black background
      body: CustomScrollView(
        physics: const BouncingScrollPhysics(),
        slivers: [
          // Sleek App Bar
          SliverAppBar(
            floating: true,
            backgroundColor: const Color(0xFF0a0a0a),
            elevation: 0,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
              onPressed: () => Navigator.pop(context),
            ),
            title: const Text(
              'Product Analysis',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.5,
              ),
            ),
          ),

          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 40),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                const SizedBox(height: 20),

                // Component 1: Overall Grade Display
                _buildOverallGrade()
                    .animate()
                    .scale(
                      duration: 600.ms,
                      curve: Curves.easeOutBack,
                    )
                    .fadeIn(duration: 400.ms),

                const SizedBox(height: 32),

                // Product Info
                _buildProductInfo()
                    .animate()
                    .fadeIn(delay: 100.ms, duration: 400.ms)
                    .slideY(begin: 0.1, duration: 400.ms),

                const SizedBox(height: 24),

                // Component 2: 4-Dimension Score Circles
                _buildDimensionScores()
                    .animate()
                    .fadeIn(delay: 200.ms, duration: 400.ms)
                    .slideY(begin: 0.1, duration: 400.ms),

                const SizedBox(height: 32),

                // Component 3: Ingredients List (Worst-First) - MOVED UP
                if (result.ingredientsGraded.isNotEmpty) ...[
                  _buildIngredientsList()
                      .animate()
                      .fadeIn(delay: 300.ms, duration: 400.ms),
                  const SizedBox(height: 24),
                ],

                // Component 4: Corporate Disclosure Card
                if (result.corporateDisclosure != null) ...[
                  _buildCorporateDisclosure()
                      .animate()
                      .fadeIn(delay: 350.ms, duration: 400.ms)
                      .slideY(begin: 0.1, duration: 400.ms),
                  const SizedBox(height: 24),
                ],

                // Component 5: Hidden Truths Expandable Cards - MOVED DOWN
                if (result.hiddenTruths.isNotEmpty) ...[
                  _buildHiddenTruths()
                      .animate()
                      .fadeIn(delay: 400.ms, duration: 400.ms)
                      .slideY(begin: 0.1, duration: 400.ms),
                  const SizedBox(height: 24),
                ],

                // Processing Alerts (if any)
                if (result.alerts.isNotEmpty) ...[
                  _buildAlerts()
                      .animate()
                      .fadeIn(delay: 450.ms, duration: 400.ms)
                      .slideY(begin: 0.1, duration: 400.ms),
                  const SizedBox(height: 32),
                ],

                // Component 6: Deep Research Button
                _buildDeepResearchButton(context)
                    .animate()
                    .fadeIn(delay: 500.ms, duration: 400.ms)
                    .scale(delay: 600.ms, duration: 300.ms, begin: const Offset(0.95, 0.95)),

                const SizedBox(height: 20),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  // Component 1: Overall Grade Display
  Widget _buildOverallGrade() {
    return Center(
      child: Container(
        width: 160,
        height: 160,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [
              result.gradeColor.withOpacity(0.9),
              result.gradeColor.withOpacity(0.7),
              result.gradeColor.withOpacity(0.5),
            ],
            stops: const [0.3, 0.7, 1.0],
          ),
          boxShadow: [
            BoxShadow(
              color: result.gradeColor.withOpacity(0.5),
              blurRadius: 40,
              spreadRadius: 5,
            ),
            BoxShadow(
              color: result.gradeColor.withOpacity(0.3),
              blurRadius: 60,
              spreadRadius: 10,
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              result.gradeEmoji,
              style: const TextStyle(fontSize: 36),
            ),
            const SizedBox(height: 4),
            Text(
              result.grade,
              style: const TextStyle(
                fontSize: 56,
                fontWeight: FontWeight.w900,
                color: Colors.white,
                height: 1,
                letterSpacing: -1,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '${result.score}/100',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Colors.white.withOpacity(0.9),
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProductInfo() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1a1a1a),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: Colors.white.withOpacity(0.1),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            result.productName ?? 'Unknown Product',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: Colors.white,
              letterSpacing: 0.3,
            ),
          ),
          if (result.brand != null) ...[
            const SizedBox(height: 6),
            Text(
              result.brand!,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w500,
                color: Colors.white.withOpacity(0.6),
                letterSpacing: 0.2,
              ),
            ),
          ],
        ],
      ),
    );
  }

  // Component 2: 4-Dimension Score Circles
  Widget _buildDimensionScores() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF1a1a1a),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: Colors.white.withOpacity(0.1),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'DIMENSION BREAKDOWN',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: Colors.white54,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildDimensionCircle(
                'Ingredients',
                result.dimensionScores.ingredientSafety,
                const Color(0xFF3b82f6),
              ).animate(delay: 100.ms).scale(duration: 400.ms, curve: Curves.easeOutBack),
              _buildDimensionCircle(
                'Processing',
                result.dimensionScores.processingLevel,
                const Color(0xFFa855f7),
              ).animate(delay: 200.ms).scale(duration: 400.ms, curve: Curves.easeOutBack),
              _buildDimensionCircle(
                'Corporate',
                result.dimensionScores.corporateEthics,
                const Color(0xFFf97316),
              ).animate(delay: 300.ms).scale(duration: 400.ms, curve: Curves.easeOutBack),
              _buildDimensionCircle(
                'Supply',
                result.dimensionScores.supplyChain,
                const Color(0xFF10b981),
              ).animate(delay: 400.ms).scale(duration: 400.ms, curve: Curves.easeOutBack),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDimensionCircle(String label, int score, Color color) {
    return SizedBox(
      width: 70,
      child: Column(
        children: [
          SizedBox(
            width: 70,
            height: 70,
            child: Stack(
              children: [
                // Background circle
                Container(
                  width: 70,
                  height: 70,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withOpacity(0.05),
                  ),
                ),
                // Progress circle
                SizedBox(
                  width: 70,
                  height: 70,
                  child: CircularProgressIndicator(
                    value: score / 100,
                    strokeWidth: 5,
                    backgroundColor: Colors.transparent,
                    valueColor: AlwaysStoppedAnimation<Color>(color),
                    strokeCap: StrokeCap.round,
                  ),
                ),
                // Center score
                Center(
                  child: Text(
                    '$score',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: color,
                      height: 1,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: Colors.white70,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }

  // Processing Alerts Section
  Widget _buildAlerts() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              '⚡',
              style: TextStyle(fontSize: 20),
            ),
            const SizedBox(width: 8),
            const Text(
              'PROCESSING ALERTS',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: Color(0xFFf97316),
                letterSpacing: 1.2,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        ...result.alerts.asMap().entries.map((entry) {
          final index = entry.key;
          final alert = entry.value;
          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFf97316).withOpacity(0.08),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: const Color(0xFFf97316).withOpacity(0.3),
                width: 2,
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(
                  Icons.info_outline,
                  color: Color(0xFFf97316),
                  size: 20,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    alert,
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.white.withOpacity(0.9),
                      height: 1.5,
                      letterSpacing: 0.1,
                    ),
                  ),
                ),
              ],
            ),
          ).animate(delay: (index * 50).ms).fadeIn(duration: 300.ms).slideX(begin: -0.1);
        }),
      ],
    );
  }

  // Component 3: Hidden Truths Expandable Cards
  Widget _buildHiddenTruths() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              '🚨',
              style: TextStyle(fontSize: 20),
            ),
            const SizedBox(width: 8),
            const Text(
              'HIDDEN TRUTHS',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: Color(0xFFef4444),
                letterSpacing: 1.2,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        ...result.hiddenTruths.asMap().entries.map((entry) {
          final index = entry.key;
          final truth = entry.value;
          return _buildHiddenTruthCard(truth, index);
        }),
      ],
    );
  }

  Widget _buildHiddenTruthCard(String truth, int index) {
    // Split truth into title and details (first line vs rest)
    final lines = truth.split('\n');
    final title = lines.first;
    final details = lines.length > 1 ? lines.sublist(1).join('\n').trim() : '';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFFef4444).withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFFef4444).withOpacity(0.3),
          width: 2,
        ),
      ),
      child: Theme(
        data: ThemeData(
          dividerColor: Colors.transparent,
          splashColor: const Color(0xFFef4444).withOpacity(0.1),
        ),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          title: Text(
            title,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: Color(0xFFef4444),
              letterSpacing: 0.2,
            ),
          ),
          iconColor: const Color(0xFFef4444),
          collapsedIconColor: const Color(0xFFef4444).withOpacity(0.7),
          children: [
            if (details.isNotEmpty)
              Text(
                details,
                style: TextStyle(
                  fontSize: 13,
                  height: 1.6,
                  color: Colors.white.withOpacity(0.8),
                  letterSpacing: 0.1,
                ),
              )
            else
              Text(
                truth,
                style: TextStyle(
                  fontSize: 13,
                  height: 1.6,
                  color: Colors.white.withOpacity(0.8),
                  letterSpacing: 0.1,
                ),
              ),
          ],
        ),
      ),
    ).animate(delay: (index * 50).ms).fadeIn(duration: 300.ms).slideX(begin: -0.1);
  }

  // Component 4: Corporate Disclosure Card
  Widget _buildCorporateDisclosure() {
    final disclosure = result.corporateDisclosure!;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1a1a1a),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: const Color(0xFFf97316).withOpacity(0.3),
          width: 2,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                '📍',
                style: TextStyle(fontSize: 24),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Text(
                  'CORPORATE OWNERSHIP',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFFf97316),
                    letterSpacing: 1.2,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          RichText(
            text: TextSpan(
              style: const TextStyle(
                fontSize: 14,
                color: Colors.white,
                height: 1.5,
              ),
              children: [
                TextSpan(
                  text: disclosure.brand,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                const TextSpan(text: ' → owned by '),
                TextSpan(
                  text: disclosure.parentCompany,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    color: Color(0xFFf97316),
                  ),
                ),
              ],
            ),
          ),
          if (disclosure.issues.isNotEmpty) ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFFef4444).withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: const Color(0xFFef4444).withOpacity(0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '⚠️ PARENT COMPANY ISSUES:',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFFef4444),
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 10),
                  ...disclosure.issues.map((issue) => Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '•',
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.7),
                                fontSize: 16,
                                height: 1.4,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                issue,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.white.withOpacity(0.8),
                                  height: 1.5,
                                  letterSpacing: 0.1,
                                ),
                              ),
                            ),
                          ],
                        ),
                      )),
                ],
              ),
            ),
          ],
          if (disclosure.notableBrands.isNotEmpty) ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF3b82f6).withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: const Color(0xFF3b82f6).withOpacity(0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '💡 DID YOU KNOW?',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF3b82f6),
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 10),
                  RichText(
                    text: TextSpan(
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.white.withOpacity(0.8),
                        height: 1.6,
                        letterSpacing: 0.1,
                      ),
                      children: [
                        TextSpan(
                          text: disclosure.parentCompany,
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        const TextSpan(text: ' also makes: '),
                        TextSpan(
                          text: disclosure.notableBrands.join(', '),
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF3b82f6),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  // Component 6: Ingredients List (Worst-First)
  Widget _buildIngredientsList() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'INGREDIENTS (sorted by concern)',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w800,
            color: Colors.white60,
            letterSpacing: 1.2,
          ),
        ),
        const SizedBox(height: 16),
        ...result.ingredientsGraded.asMap().entries.map((entry) {
          final index = entry.key;
          final ingredient = entry.value;
          return _buildIngredientItem(ingredient, index);
        }),
      ],
    );
  }

  Widget _buildIngredientItem(IngredientGraded ingredient, int index) {
    // Use centralized color system from AppColors
    final gradeColor = AppColors.getGradeColor(ingredient.grade);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1a1a1a),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: gradeColor.withOpacity(0.4),
          width: 2,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: gradeColor,
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: gradeColor.withOpacity(0.3),
                  blurRadius: 8,
                  spreadRadius: 1,
                ),
              ],
            ),
            child: Text(
              ingredient.grade,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w900,
                color: Colors.white,
                letterSpacing: 0.5,
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  ingredient.name,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                    letterSpacing: 0.2,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  ingredient.reason,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white.withOpacity(0.7),
                    height: 1.5,
                    letterSpacing: 0.1,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    ).animate(delay: (index * 50).ms).fadeIn(duration: 300.ms).slideX(begin: -0.1);
  }

  // Component 5: Deep Research Button
  Widget _buildDeepResearchButton(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 62,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFF3b82f6),
            Color(0xFF8b5cf6),
          ],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        ),
        borderRadius: BorderRadius.circular(31),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF3b82f6).withOpacity(0.4),
            blurRadius: 20,
            spreadRadius: 2,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _startDeepResearch(context),
          borderRadius: BorderRadius.circular(31),
          splashColor: Colors.white.withOpacity(0.2),
          highlightColor: Colors.white.withOpacity(0.1),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  '🔬',
                  style: TextStyle(fontSize: 28),
                ),
                const SizedBox(width: 14),
                const Text(
                  'DEEP RESEARCH',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'Premium',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _startDeepResearch(BuildContext context) async {
    // Extract ingredients from the result
    final List<String> ingredients = result.ingredientsGraded
        .map((ingredient) => ingredient.name)
        .toList();

    // Determine category from product data
    String category = 'food'; // Default category
    final productNameLower = result.productName?.toLowerCase() ?? '';

    if (productNameLower.contains('drink') || productNameLower.contains('beverage') || productNameLower.contains('water')) {
      category = 'water';
    } else if (productNameLower.contains('cosmetic') || productNameLower.contains('lotion') || productNameLower.contains('cream')) {
      category = 'cosmetics';
    } else if (productNameLower.contains('clean') || productNameLower.contains('detergent') || productNameLower.contains('soap')) {
      category = 'cleaning';
    } else if (productNameLower.contains('supplement') || productNameLower.contains('vitamin')) {
      category = 'supplements';
    } else if (productNameLower.contains('cook') || productNameLower.contains('pan') || productNameLower.contains('pot')) {
      category = 'cookware';
    }

    // Show the deep research dialog
    await DeepResearchDialog.show(
      context: context,
      productName: result.productName ?? 'Unknown Product',
      brand: result.brand,
      category: category,
      ingredients: ingredients,
    );
  }
}
