import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class ManualEntryScreen extends StatefulWidget {
  const ManualEntryScreen({super.key});

  @override
  State<ManualEntryScreen> createState() => _ManualEntryScreenState();
}

class _ManualEntryScreenState extends State<ManualEntryScreen> {
  final _productNameController = TextEditingController();
  final _ingredientsController = TextEditingController();
  final _singleIngredientController = TextEditingController();
  final List<String> _ingredients = [];
  bool _isLoading = false;
  bool _isLookingUp = false;
  
  @override
  void dispose() {
    _productNameController.dispose();
    _ingredientsController.dispose();
    _singleIngredientController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manual Entry'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Product Name
            Text(
              'Product Name',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _productNameController,
              decoration: InputDecoration(
                hintText: 'e.g., Clorox Disinfecting Wipes',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                prefixIcon: const Icon(Icons.inventory_2),
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Ingredient Lookup
            Text(
              'Quick Ingredient Lookup',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _singleIngredientController,
                    decoration: InputDecoration(
                      hintText: 'Look up single ingredient',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      prefixIcon: const Icon(Icons.search),
                    ),
                    onSubmitted: (_) => _lookupIngredient(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _isLookingUp ? null : _lookupIngredient,
                  icon: _isLookingUp 
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.search),
                ),
              ],
            ),
            
            const SizedBox(height: 24),
            
            // Ingredients List
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Ingredients (${_ingredients.length})',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                TextButton.icon(
                  onPressed: _showBulkEntryDialog,
                  icon: const Icon(Icons.paste, size: 18),
                  label: const Text('Paste List'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            
            // Add ingredient field
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _ingredientsController,
                    decoration: InputDecoration(
                      hintText: 'Add ingredient',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onSubmitted: (_) => _addIngredient(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _addIngredient,
                  icon: const Icon(Icons.add),
                ),
              ],
            ),
            
            const SizedBox(height: 12),
            
            // Ingredients chips
            if (_ingredients.isNotEmpty)
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _ingredients.asMap().entries.map((entry) {
                  return Chip(
                    label: Text(entry.value),
                    deleteIcon: const Icon(Icons.close, size: 18),
                    onDeleted: () => _removeIngredient(entry.key),
                  );
                }).toList(),
              )
            else
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    'No ingredients added yet.\nAdd ingredients to calculate toxicity score.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ),
              ),
            
            const SizedBox(height: 32),
            
            // Analyze Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _ingredients.isEmpty || _isLoading ? null : _analyze,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  foregroundColor: Colors.white,
                ),
                child: _isLoading
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text(
                        'Analyze Ingredients',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Tip
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.lightbulb_outline, color: Colors.blue),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Tip: Copy the ingredient list from the product label and use "Paste List" for faster entry.',
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.blue.shade700,
                      ),
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
  
  void _addIngredient() {
    final text = _ingredientsController.text.trim();
    if (text.isNotEmpty) {
      setState(() {
        _ingredients.add(text);
        _ingredientsController.clear();
      });
    }
  }
  
  void _removeIngredient(int index) {
    setState(() {
      _ingredients.removeAt(index);
    });
  }
  
  void _showBulkEntryDialog() {
    final controller = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Paste Ingredients'),
        content: TextField(
          controller: controller,
          maxLines: 8,
          decoration: const InputDecoration(
            hintText: 'Paste ingredient list here...\n\nSeparate with commas or new lines',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final text = controller.text;
              // Split by commas, newlines, or semicolons
              final ingredients = text
                  .split(RegExp(r'[,;\n]'))
                  .map((s) => s.trim())
                  .where((s) => s.isNotEmpty)
                  .toList();
              
              setState(() {
                _ingredients.addAll(ingredients);
              });
              Navigator.pop(context);
            },
            child: const Text('Add All'),
          ),
        ],
      ),
    );
  }
  
  Future<void> _lookupIngredient() async {
    final name = _singleIngredientController.text.trim();
    if (name.isEmpty) return;
    
    setState(() {
      _isLookingUp = true;
    });
    
    try {
      final apiService = context.read<ApiService>();
      final result = await apiService.lookupIngredient(name);
      
      if (!mounted) return;
      
      if (result != null) {
        _showIngredientInfo(result);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ingredient not found in database')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLookingUp = false;
        });
      }
    }
  }
  
  void _showIngredientInfo(Map<String, dynamic> info) {
    final concernLevel = info['concern_level'] ?? 'unknown';
    final toxicityScore = info['toxicity_score'] ?? 0;
    final isCarcinogen = info['is_carcinogen'] ?? false;
    
    Color getColor() {
      switch (concernLevel) {
        case 'critical': return Colors.red;
        case 'high': return Colors.orange;
        case 'moderate': return Colors.amber;
        case 'low': return Colors.green;
        default: return Colors.grey;
      }
    }
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: getColor(),
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(child: Text(info['name'] ?? 'Unknown')),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _infoRow('Toxicity Score', '$toxicityScore/10'),
            _infoRow('Concern Level', concernLevel.toString().toUpperCase()),
            if (isCarcinogen)
              Container(
                margin: const EdgeInsets.only(top: 12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.warning, color: Colors.red),
                    SizedBox(width: 8),
                    Text(
                      'Known/Suspected Carcinogen',
                      style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
            if (info['notes'] != null) ...[
              const SizedBox(height: 12),
              Text(info['notes'], style: const TextStyle(fontSize: 13)),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _ingredients.add(info['name']);
              });
              Navigator.pop(context);
              _singleIngredientController.clear();
            },
            child: const Text('Add to List'),
          ),
        ],
      ),
    );
  }
  
  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
  
  Future<void> _analyze() async {
    if (_ingredients.isEmpty) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // Manual entry is no longer supported in API v3.1.0
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Manual entry is not supported. Please use the camera to scan products.'),
          backgroundColor: Colors.orange,
          duration: Duration(seconds: 4),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
}
