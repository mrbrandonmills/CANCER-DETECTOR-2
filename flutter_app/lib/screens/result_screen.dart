import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/scan_result.dart';

class ResultScreen extends StatelessWidget {
  final ScanResult result;

  const ResultScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0f172a), // Dark theme
      body: CustomScrollView(
        slivers: [
          // App Bar with gradient
          SliverAppBar(
            expandedHeight: 280,
            pinned: true,
            backgroundColor: const Color(0xFF1e293b),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back, color: Colors.white),
              onPressed: () => Navigator.pop(context),
            ),
            flexibleSpace: FlexibleSpaceBar(
              background: _buildGradeHeader(context),
            ),
          ),

          SliverPadding(
            padding: const EdgeInsets.all(20),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // Product Info
                _buildProductInfo(context)
                    .animate()
                    .fadeIn(delay: 100.ms)
                    .slideY(begin: 0.2),

                const SizedBox(height: 20),

                // V3 PRIORITY #1: Ingredients Section (moved to top)
                _buildAnalysisSection(context)
                    .animate()
                    .fadeIn(delay: 150.ms),

                const SizedBox(height: 20),

                // V3 PRIORITY #2: Positive Attributes Section (NEW)
                if (result.positiveAttributes != null && result.positiveAttributes!.isNotEmpty) ...[
                  _buildPositiveAttributesSection(context)
                      .animate()
                      .fadeIn(delay: 200.ms)
                      .slideY(begin: 0.2),
                  const SizedBox(height: 20),
                ],

                // V3 PRIORITY #3: Expiration Status Section (NEW)
                if (result.expiration != null && result.expiration!.status != 'not_applicable') ...[
                  _buildExpirationSection(context)
                      .animate()
                      .fadeIn(delay: 250.ms)
                      .slideY(begin: 0.2),
                  const SizedBox(height: 20),
                ],

                // Personalized Notes (if present)
                if (result.personalizedNotes != null) ...[
                  _buildPersonalizedNotes(context)
                      .animate()
                      .fadeIn(delay: 300.ms)
                      .slideY(begin: 0.2),
                  const SizedBox(height: 20),
                ],

                // Recommendation Card
                if (result.recommendation != null)
                  _buildRecommendationCard(context)
                      .animate()
                      .fadeIn(delay: 350.ms)
                      .slideY(begin: 0.2),

                const SizedBox(height: 20),

                // Care Tips (if present)
                if (result.careTips != null && result.careTips!.isNotEmpty) ...[
                  _buildCareTipsSection(context)
                      .animate()
                      .fadeIn(delay: 400.ms),
                  const SizedBox(height: 20),
                ],

                // V3 PRIORITY #4: Condition Assessment (moved to bottom, before safer alternative)
                if (result.conditionV3 != null) ...[
                  _buildConditionCardV3(context)
                      .animate()
                      .fadeIn(delay: 450.ms)
                      .slideY(begin: 0.2),
                  const SizedBox(height: 20),
                ] else if (result.condition != null) ...[
                  _buildConditionCard(context)
                      .animate()
                      .fadeIn(delay: 450.ms)
                      .slideY(begin: 0.2),
                  const SizedBox(height: 20),
                ],

                // Safer Alternative (bottom)
                if (result.saferAlternative != null) ...[
                  _buildSaferAlternative(context)
                      .animate()
                      .fadeIn(delay: 500.ms)
                      .shake(delay: 600.ms),
                  const SizedBox(height: 20),
                ],

                // Action Buttons
                _buildActionButtons(context)
                    .animate()
                    .fadeIn(delay: 550.ms),

                const SizedBox(height: 40),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGradeHeader(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            result.gradeColor.withOpacity(0.3),
            const Color(0xFF1e293b),
          ],
        ),
      ),
      child: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(height: 40),

            // Grade Circle
            _buildGradeCircle(),

            const SizedBox(height: 16),

            // Product Type Badge
            if (result.productType != null)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: result.gradeColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: result.gradeColor.withOpacity(0.5),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      result.productTypeIcon,
                      size: 16,
                      color: result.gradeColor,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      result.productTypeBadge,
                      style: TextStyle(
                        color: result.gradeColor,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildGradeCircle() {
    return Container(
      width: 140,
      height: 140,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            result.gradeColor,
            result.gradeColor.withOpacity(0.6),
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: result.gradeColor.withOpacity(0.4),
            blurRadius: 30,
            spreadRadius: 5,
          ),
        ],
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              result.gradeEmoji,
              style: const TextStyle(fontSize: 40),
            ),
            const SizedBox(height: 4),
            Text(
              result.displayGrade,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 36,
                fontWeight: FontWeight.bold,
                height: 1,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProductInfo(BuildContext context) {
    return _buildGlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            result.productName ?? 'Unknown Product',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          if (result.brand != null) ...[
            const SizedBox(height: 6),
            Text(
              result.brand!,
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 16,
              ),
            ),
          ],
          const SizedBox(height: 12),

          // Score indicators
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              if (result.safetyScore != null)
                _buildScoreChip('Safety', result.safetyScore!),
              if (result.conditionScore != null)
                _buildScoreChip('Condition', result.conditionScore!),
              if (result.overallScore != null)
                _buildScoreChip('Overall', result.overallScore!),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildScoreChip(String label, int score) {
    final color = _getScoreColor(score);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            '$score',
            style: TextStyle(
              color: color,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPersonalizedNotes(BuildContext context) {
    return _buildGlassCard(
      color: const Color(0xFF8b5cf6).withOpacity(0.1),
      borderColor: const Color(0xFF8b5cf6).withOpacity(0.3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF8b5cf6).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.lightbulb,
                  color: Color(0xFF8b5cf6),
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              const Text(
                'Personalized Insight',
                style: TextStyle(
                  color: Color(0xFF8b5cf6),
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            result.personalizedNotes!,
            style: const TextStyle(
              fontSize: 15,
              height: 1.5,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendationCard(BuildContext context) {
    return _buildGlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _getRecommendationIcon(),
                color: result.gradeColor,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                'Recommendation',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: result.gradeColor,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            result.recommendation!,
            style: const TextStyle(
              fontSize: 15,
              height: 1.5,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConditionCard(BuildContext context) {
    final condition = result.condition!;
    return _buildGlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Condition Assessment',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  fontSize: 16,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: condition.conditionColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: condition.conditionColor),
                ),
                child: Text(
                  condition.conditionLabel,
                  style: TextStyle(
                    color: condition.conditionColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Observations
          if (condition.observations.isNotEmpty) ...[
            ...condition.observations.map((obs) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.check_circle, size: 16, color: Color(0xFF06b6d4)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          obs,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white.withOpacity(0.9),
                          ),
                        ),
                      ),
                    ],
                  ),
                )),
          ],

          // Concerns
          if (condition.concerns.isNotEmpty) ...[
            const SizedBox(height: 8),
            ...condition.concerns.map((concern) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.warning_amber, size: 16, color: Color(0xFFfbbf24)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          concern,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white.withOpacity(0.9),
                          ),
                        ),
                      ),
                    ],
                  ),
                )),
          ],

          // Estimated Age
          if (condition.estimatedAge != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.access_time, size: 16, color: Color(0xFF8b5cf6)),
                  const SizedBox(width: 8),
                  Text(
                    'Estimated age: ${condition.estimatedAge}',
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.white.withOpacity(0.8),
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

  Widget _buildAnalysisSection(BuildContext context) {
    if (result.analysisType == 'material' && result.materials != null) {
      return _buildMaterialsAnalysis(context);
    } else {
      return _buildIngredientsAnalysis(context);
    }
  }

  Widget _buildIngredientsAnalysis(BuildContext context) {
    // V3: Use enhanced ingredients data if available
    if (result.ingredientsData != null) {
      return _buildIngredientsAnalysisV3(context);
    }

    // V2: Fallback to old format
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Ingredient Analysis',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 16),

        // Flagged Ingredients
        if (result.flaggedIngredients != null && result.flaggedIngredients!.isNotEmpty) ...[
          const Text(
            'Flagged Ingredients',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: Color(0xFFef4444),
            ),
          ),
          const SizedBox(height: 12),
          ...result.flaggedIngredients!.asMap().entries.map((entry) {
            final index = entry.key;
            return _buildFlaggedIngredientTile(entry.value, index);
          }),
          const SizedBox(height: 20),
        ],

        // Safe Ingredients
        if (result.safeIngredients != null && result.safeIngredients!.isNotEmpty) ...[
          const Text(
            'Safe Ingredients',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: Color(0xFF10b981),
            ),
          ),
          const SizedBox(height: 12),
          _buildGlassCard(
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: result.safeIngredients!.map((ingredient) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10b981).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: const Color(0xFF10b981).withOpacity(0.3),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.check, size: 14, color: Color(0xFF10b981)),
                      const SizedBox(width: 4),
                      Text(
                        ingredient,
                        style: const TextStyle(
                          fontSize: 13,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildIngredientsAnalysisV3(BuildContext context) {
    final ingredientsData = result.ingredientsData!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Ingredient Analysis',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF8b5cf6).withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF8b5cf6).withOpacity(0.5)),
              ),
              child: Text(
                '${ingredientsData.totalCount} ingredients',
                style: const TextStyle(
                  color: Color(0xFF8b5cf6),
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // All ingredients with individual hazard scores
        ...ingredientsData.analysis.asMap().entries.map((entry) {
          final index = entry.key;
          final ingredient = entry.value;
          return _buildIngredientTileV3(ingredient, index);
        }),
      ],
    );
  }

  Widget _buildIngredientTileV3(IngredientAnalysis ingredient, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: _buildGlassCard(
        borderColor: ingredient.hazardColor.withOpacity(0.5),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    ingredient.name,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      fontSize: 15,
                    ),
                  ),
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Source badge (Claude vs Database)
                    if (ingredient.source != null) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: ingredient.source == 'database'
                              ? const Color(0xFF06b6d4).withOpacity(0.2)
                              : const Color(0xFF8b5cf6).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: ingredient.source == 'database'
                                ? const Color(0xFF06b6d4).withOpacity(0.5)
                                : const Color(0xFF8b5cf6).withOpacity(0.5),
                          ),
                        ),
                        child: Text(
                          ingredient.source == 'database' ? 'DB' : 'AI',
                          style: TextStyle(
                            color: ingredient.source == 'database'
                                ? const Color(0xFF06b6d4)
                                : const Color(0xFF8b5cf6),
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                    ],
                    // Hazard score badge
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: ingredient.hazardColor,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '${ingredient.hazardScore}',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 4),
                          Text(
                            ingredient.hazardLevel,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Category
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                ingredient.category,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.white.withOpacity(0.7),
                ),
              ),
            ),
            // Concerns (if any)
            if (ingredient.concerns.isNotEmpty) ...[
              const SizedBox(height: 10),
              ...ingredient.concerns.map((concern) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.warning_amber,
                          size: 14,
                          color: ingredient.hazardColor,
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            concern,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.white.withOpacity(0.8),
                            ),
                          ),
                        ),
                      ],
                    ),
                  )),
            ],
          ],
        ),
      ),
    ).animate().fadeIn(delay: (100 * index).ms).slideX(begin: 0.1);
  }

  Widget _buildFlaggedIngredientTile(FlaggedIngredient ingredient, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: _buildGlassCard(
        borderColor: ingredient.hazardColor.withOpacity(0.5),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    ingredient.ingredient,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      fontSize: 15,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: ingredient.hazardColor,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    ingredient.hazardLevel,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                ingredient.category,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.white.withOpacity(0.7),
                ),
              ),
            ),
            if (ingredient.concerns.isNotEmpty) ...[
              const SizedBox(height: 10),
              ...ingredient.concerns.map((concern) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.warning_amber,
                          size: 14,
                          color: ingredient.hazardColor,
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            concern,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.white.withOpacity(0.8),
                            ),
                          ),
                        ),
                      ],
                    ),
                  )),
            ],
          ],
        ),
      ),
    ).animate().fadeIn(delay: (100 * index).ms).slideX(begin: 0.1);
  }

  Widget _buildMaterialsAnalysis(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Material Analysis',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 16),
        ...result.materials!.asMap().entries.map((entry) {
          final index = entry.key;
          final material = entry.value;
          return _buildMaterialTile(material, index);
        }),
      ],
    );
  }

  Widget _buildMaterialTile(MaterialAnalysis material, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: _buildGlassCard(
        borderColor: material.scoreColor.withOpacity(0.5),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        material.component,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        material.material,
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.white.withOpacity(0.7),
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  width: 50,
                  height: 50,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: material.scoreColor.withOpacity(0.2),
                    border: Border.all(
                      color: material.scoreColor,
                      width: 2,
                    ),
                  ),
                  child: Center(
                    child: Text(
                      '${material.score}',
                      style: TextStyle(
                        color: material.scoreColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),
                ),
              ],
            ),
            if (material.concerns.isNotEmpty) ...[
              const SizedBox(height: 12),
              ...material.concerns.map((concern) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.info_outline,
                          size: 14,
                          color: material.scoreColor,
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            concern,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.white.withOpacity(0.8),
                            ),
                          ),
                        ),
                      ],
                    ),
                  )),
            ],
          ],
        ),
      ),
    ).animate().fadeIn(delay: (100 * index).ms).slideX(begin: 0.1);
  }

  Widget _buildCareTipsSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Care Tips',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        const SizedBox(height: 16),
        ...result.careTips!.asMap().entries.map((entry) {
          final index = entry.key;
          final tip = entry.value;
          return _buildCareTipCard(tip, index);
        }),
      ],
    );
  }

  Widget _buildCareTipCard(CareTip tip, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: _buildGlassCard(
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: const Color(0xFF8b5cf6).withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Center(
                child: Text(
                  tip.icon,
                  style: const TextStyle(fontSize: 24),
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    tip.tip,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    tip.desc,
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.white.withOpacity(0.7),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(delay: (100 * index).ms).slideX(begin: 0.1);
  }

  Widget _buildPositiveAttributesSection(BuildContext context) {
    return _buildGlassCard(
      color: const Color(0xFF10b981).withOpacity(0.1),
      borderColor: const Color(0xFF10b981).withOpacity(0.3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF10b981).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.add_circle,
                  color: Color(0xFF10b981),
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              const Text(
                'Positive Attributes',
                style: TextStyle(
                  color: Color(0xFF10b981),
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: result.positiveAttributes!.map((attribute) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFF10b981).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: const Color(0xFF10b981).withOpacity(0.5),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (attribute.verified)
                      const Icon(
                        Icons.verified,
                        size: 16,
                        color: Color(0xFF10b981),
                      ),
                    if (attribute.verified) const SizedBox(width: 4),
                    Text(
                      attribute.claim,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF10b981),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '+${attribute.bonusPoints}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildExpirationSection(BuildContext context) {
    final expiration = result.expiration!;
    return _buildGlassCard(
      color: expiration.statusColor.withOpacity(0.1),
      borderColor: expiration.statusColor.withOpacity(0.3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.calendar_today,
                    color: expiration.statusColor,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Expiration Status',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: expiration.statusColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: expiration.statusColor),
                ),
                child: Text(
                  expiration.statusLabel,
                  style: TextStyle(
                    color: expiration.statusColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          if (expiration.notes != null) ...[
            const SizedBox(height: 12),
            Text(
              expiration.notes!,
              style: TextStyle(
                fontSize: 14,
                color: Colors.white.withOpacity(0.8),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildConditionCardV3(BuildContext context) {
    final condition = result.conditionV3!;
    return _buildGlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Text(
                    'Condition Assessment',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF8b5cf6).withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: const Color(0xFF8b5cf6).withOpacity(0.5),
                      ),
                    ),
                    child: Text(
                      '${condition.weightPercentage}% weight',
                      style: const TextStyle(
                        color: Color(0xFF8b5cf6),
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: condition.conditionColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: condition.conditionColor),
                ),
                child: Text(
                  condition.conditionLabel,
                  style: TextStyle(
                    color: condition.conditionColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Concerns
          if (condition.concerns.isNotEmpty) ...[
            ...condition.concerns.map((concern) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.warning_amber,
                        size: 16,
                        color: condition.conditionColor,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          concern,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white.withOpacity(0.9),
                          ),
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _buildSaferAlternative(BuildContext context) {
    final alt = result.saferAlternative!;
    return _buildGlassCard(
      color: const Color(0xFF10b981).withOpacity(0.1),
      borderColor: const Color(0xFF10b981).withOpacity(0.5),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF10b981).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.recommend,
                  color: Color(0xFF10b981),
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              const Text(
                'Safer Alternative',
                style: TextStyle(
                  color: Color(0xFF10b981),
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  alt.name,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFF10b981).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF10b981)),
                ),
                child: Text(
                  alt.grade,
                  style: const TextStyle(
                    color: Color(0xFF10b981),
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            alt.reason,
            style: TextStyle(
              fontSize: 14,
              color: Colors.white.withOpacity(0.8),
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.camera_alt),
            label: const Text('Scan Another Product'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              backgroundColor: const Color(0xFF8b5cf6),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => _shareResult(context),
            icon: const Icon(Icons.share),
            label: const Text('Share Results'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              foregroundColor: const Color(0xFF06b6d4),
              side: const BorderSide(color: Color(0xFF06b6d4)),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _shareResult(BuildContext context) {
    // TODO: Implement share functionality
    // final text = '''
    // Product Safety Report
    //
    // Product: ${result.productName}
    // Grade: ${result.grade}
    // Safety Score: ${result.safetyScore}/100
    //
    // ${result.recommendation ?? ''}
    //
    // Scanned with Cancer Detector App
    // ''';

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Share feature coming soon!'),
        backgroundColor: Color(0xFF06b6d4),
      ),
    );
  }

  // Helper: Glass morphism card
  Widget _buildGlassCard({
    required Widget child,
    Color? color,
    Color? borderColor,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color ?? Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: borderColor ?? Colors.white.withOpacity(0.1),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: child,
    );
  }

  Color _getScoreColor(int score) {
    if (score >= 80) return const Color(0xFF10b981); // Green
    if (score >= 60) return const Color(0xFF06b6d4); // Cyan
    if (score >= 40) return const Color(0xFFfbbf24); // Yellow
    if (score >= 20) return const Color(0xFFf97316); // Orange
    return const Color(0xFFef4444); // Red
  }

  IconData _getRecommendationIcon() {
    if (result.grade == null) return Icons.info;
    final gradeLetter = result.grade![0];
    switch (gradeLetter) {
      case 'A':
        return Icons.check_circle;
      case 'B':
        return Icons.thumb_up;
      case 'C':
        return Icons.info;
      case 'D':
        return Icons.warning;
      case 'F':
        return Icons.dangerous;
      default:
        return Icons.info;
    }
  }
}
