import 'package:flutter/material.dart';
import '../models/scan_result_v4.dart';
import 'result_screen_v4.dart';

/// Demo page to showcase the V4 Result Screen with sample data
class ResultScreenV4Demo extends StatelessWidget {
  const ResultScreenV4Demo({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0a0a0a),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0a0a0a),
        title: const Text(
          'V4 Result Screen Demo',
          style: TextStyle(color: Colors.white),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildDemoButton(
              context,
              'Good Product (Grade A)',
              _getGoodProductSample(),
              const Color(0xFF22c55e),
            ),
            const SizedBox(height: 20),
            _buildDemoButton(
              context,
              'Moderate Product (Grade C)',
              _getModerateProductSample(),
              const Color(0xFFfacc15),
            ),
            const SizedBox(height: 20),
            _buildDemoButton(
              context,
              'Poor Product (Grade F)',
              _getPoorProductSample(),
              const Color(0xFFef4444),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDemoButton(BuildContext context, String label, ScanResultV4 result, Color color) {
    return ElevatedButton(
      onPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ResultScreenV4(result: result),
          ),
        );
      },
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  // Sample: Good Product (Grade A)
  ScanResultV4 _getGoodProductSample() {
    return ScanResultV4(
      success: true,
      productName: 'Organic Almond Butter',
      brand: 'Nature\'s Best',
      score: 88,
      grade: 'A',
      dimensionScores: DimensionScores(
        ingredientSafety: 95,
        processingLevel: 85,
        corporateEthics: 82,
        supplyChain: 90,
      ),
      alerts: [
        'Minimally processed - Cold-pressed without heat treatment',
      ],
      hiddenTruths: [
        'Contains palm oil\nWhile organic, palm oil production can contribute to deforestation. Look for RSPO-certified sources.',
      ],
      corporateDisclosure: CorporateDisclosure(
        brand: 'Nature\'s Best',
        parentCompany: 'Healthy Foods Corporation',
        penalty: 5,
        issues: [
          'Lawsuit settled in 2022 for mislabeling non-GMO products',
        ],
        notableBrands: [
          'Green Valley Snacks',
          'Pure Harvest Grains',
          'Mountain Spring Water',
        ],
      ),
      ingredientsGraded: [
        IngredientGraded(
          name: 'Palm Oil',
          grade: 'C',
          color: '#facc15',
          reason: 'Organic but may contribute to deforestation concerns',
          hazardScore: 30,
        ),
        IngredientGraded(
          name: 'Organic Almonds',
          grade: 'A+',
          color: '#22c55e',
          reason: 'Excellent source of healthy fats and protein',
          hazardScore: 5,
        ),
        IngredientGraded(
          name: 'Sea Salt',
          grade: 'A',
          color: '#22c55e',
          reason: 'Natural mineral source, use in moderation',
          hazardScore: 10,
        ),
      ],
    );
  }

  // Sample: Moderate Product (Grade C)
  ScanResultV4 _getModerateProductSample() {
    return ScanResultV4(
      success: true,
      productName: 'Crunchy Protein Bar',
      brand: 'FitLife',
      score: 62,
      grade: 'C',
      dimensionScores: DimensionScores(
        ingredientSafety: 55,
        processingLevel: 60,
        corporateEthics: 70,
        supplyChain: 65,
      ),
      alerts: [
        'Highly processed - Uses industrial extraction methods',
        'Multiple synthetic additives detected',
      ],
      hiddenTruths: [
        'High fructose corn syrup detected\nDespite "natural" marketing claims, this product contains HFCS which has been linked to metabolic issues.',
        'Artificial sweeteners present\nSucralose and acesulfame potassium may affect gut microbiome health.',
        'Ultra-processed ingredients\nThis product undergoes extensive processing that removes natural nutrients.',
      ],
      corporateDisclosure: CorporateDisclosure(
        brand: 'FitLife',
        parentCompany: 'MegaFood Industries',
        penalty: 15,
        issues: [
          'FDA warning in 2020 for misleading health claims',
          'Multiple recalls for undeclared allergens',
          'Labor practices investigation ongoing in 2023',
        ],
        notableBrands: [
          'QuickMeal Shakes',
          'EnergyCrunch Bars',
          'ProteinPro Powder',
          'SlimFast Alternatives',
        ],
      ),
      ingredientsGraded: [
        IngredientGraded(
          name: 'Sucralose',
          grade: 'D',
          color: '#f97316',
          reason: 'Artificial sweetener that may disrupt gut bacteria and insulin response',
          hazardScore: 65,
        ),
        IngredientGraded(
          name: 'High Fructose Corn Syrup',
          grade: 'D',
          color: '#f97316',
          reason: 'Linked to obesity, diabetes, and metabolic syndrome',
          hazardScore: 70,
        ),
        IngredientGraded(
          name: 'Soy Protein Isolate',
          grade: 'C',
          color: '#facc15',
          reason: 'Highly processed, may contain hexane residue from extraction',
          hazardScore: 40,
        ),
        IngredientGraded(
          name: 'Natural Flavors',
          grade: 'C',
          color: '#facc15',
          reason: 'Vague term that can hide proprietary chemical mixtures',
          hazardScore: 35,
        ),
        IngredientGraded(
          name: 'Whey Protein',
          grade: 'B',
          color: '#4ade80',
          reason: 'Good protein source but check for hormones and antibiotics',
          hazardScore: 20,
        ),
      ],
    );
  }

  // Sample: Poor Product (Grade F)
  ScanResultV4 _getPoorProductSample() {
    return ScanResultV4(
      success: true,
      productName: 'Extreme Energy Drink',
      brand: 'MaxBoost',
      score: 22,
      grade: 'F',
      dimensionScores: DimensionScores(
        ingredientSafety: 15,
        processingLevel: 20,
        corporateEthics: 30,
        supplyChain: 25,
      ),
      alerts: [
        'Ultra-processed - Chemically synthesized ingredients',
        'WARNING: Extreme caffeine content (300mg per serving)',
        'Contains banned substances in some countries',
      ],
      hiddenTruths: [
        'Dangerous caffeine levels\nContains 300mg caffeine per serving - equivalent to 3 cups of coffee. Can cause heart palpitations, anxiety, and sleep disorders.',
        'Banned ingredients in Europe\nContains additives that are prohibited in EU countries due to health concerns.',
        'Multiple hospitalizations reported\nFDA received 92 adverse event reports including 5 deaths linked to this product class.',
        'Undisclosed synthetic stimulants\nMay contain synephrine and other compounds that act like ephedrine.',
        'False marketing claims\n"Natural energy" claim contradicted by ingredient list showing 15+ artificial additives.',
      ],
      corporateDisclosure: CorporateDisclosure(
        brand: 'MaxBoost',
        parentCompany: 'Global Energy Drinks Inc.',
        penalty: 25,
        issues: [
          'Class action lawsuit for false advertising (ongoing)',
          'FDA warning letters for unapproved drug claims',
          'Multiple product recalls in 2023',
          'Investigation for targeting minors in marketing',
          'Environmental violations at 3 manufacturing plants',
        ],
        notableBrands: [
          'TurboShot Energy',
          'NitroFuel Drinks',
          'PowerSurge Shots',
          'UltraVolt Energy',
          'MegaCharge Beverages',
        ],
      ),
      ingredientsGraded: [
        IngredientGraded(
          name: 'Sodium Benzoate + Vitamin C',
          grade: 'F',
          color: '#ef4444',
          reason: 'Creates benzene (a known carcinogen) when combined. Banned combination in many countries.',
          hazardScore: 95,
        ),
        IngredientGraded(
          name: 'Excessive Caffeine',
          grade: 'F',
          color: '#ef4444',
          reason: '300mg per serving can cause cardiac arrest, especially with exercise',
          hazardScore: 90,
        ),
        IngredientGraded(
          name: 'Taurine (Synthetic)',
          grade: 'D',
          color: '#f97316',
          reason: 'Synthetic version with unknown long-term effects, especially when combined with stimulants',
          hazardScore: 65,
        ),
        IngredientGraded(
          name: 'Artificial Colors (Red 40, Yellow 5)',
          grade: 'D',
          color: '#f97316',
          reason: 'Linked to hyperactivity in children and potential carcinogenic effects',
          hazardScore: 60,
        ),
        IngredientGraded(
          name: 'Guarana Extract',
          grade: 'D',
          color: '#f97316',
          reason: 'Additional caffeine source not counted in label - total caffeine actually 450mg+',
          hazardScore: 70,
        ),
        IngredientGraded(
          name: 'Aspartame',
          grade: 'D',
          color: '#f97316',
          reason: 'Controversial sweetener with concerns about neurological effects',
          hazardScore: 55,
        ),
        IngredientGraded(
          name: 'Acesulfame Potassium',
          grade: 'C',
          color: '#facc15',
          reason: 'Artificial sweetener with limited long-term safety data',
          hazardScore: 45,
        ),
      ],
    );
  }
}
