import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../app/theme/app_colors.dart';
import '../../../shared/widgets/avenzo_button.dart';
import '../../../shared/widgets/avenzo_text_field.dart';
import '../providers/pantry_provider.dart';

/// Modal bottom sheet for adding a new item manually to Digital Pantry
class AddPantryItemModal extends ConsumerStatefulWidget {
  const AddPantryItemModal({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => const AddPantryItemModal(),
    );
  }

  @override
  ConsumerState<AddPantryItemModal> createState() => _AddPantryItemModalState();
}

class _AddPantryItemModalState extends ConsumerState<AddPantryItemModal> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _quantityController = TextEditingController(text: '1.0');
  final _unitController = TextEditingController(text: 'units');
  final _barcodeController = TextEditingController();
  final _notesController = TextEditingController();

  String _storageLocation = 'pantry'; // pantry, fridge, freezer
  DateTime? _purchaseDate;
  DateTime? _expiryDate;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _unitController.dispose();
    _barcodeController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(BuildContext context, bool isExpiry) async {
    final now = DateTime.now();
    final initialDate = isExpiry ? (_expiryDate ?? now.add(const Duration(days: 7))) : (_purchaseDate ?? now);
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );
    if (picked != null) {
      setState(() {
        if (isExpiry) {
          _expiryDate = picked;
        } else {
          _purchaseDate = picked;
        }
      });
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final qty = double.tryParse(_quantityController.text.trim());
    if (qty == null || qty <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a valid quantity greater than zero.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final success = await ref.read(pantryNotifierProvider.notifier).addItem(
          customName: _nameController.text.trim(),
          barcode: _barcodeController.text.trim().isNotEmpty ? _barcodeController.text.trim() : null,
          quantity: qty,
          unit: _unitController.text.trim().isNotEmpty ? _unitController.text.trim() : 'units',
          storageLocation: _storageLocation,
          purchaseDate: _purchaseDate,
          expiryDate: _expiryDate,
          notes: _notesController.text.trim().isNotEmpty ? _notesController.text.trim() : null,
        );

    if (mounted) {
      setState(() => _isSubmitting = false);
      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Item added to pantry successfully!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to add item. Please try again.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        top: 20,
        left: 20,
        right: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Add Pantry Item',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              AvenzoTextField(
                controller: _nameController,
                label: 'Item / Product Name *',
                hint: 'e.g. Organic Milk, Whole Wheat Bread',
                prefixIcon: Icons.shopping_bag_outlined,
                validator: (val) {
                  if (val == null || val.trim().isEmpty) {
                    return 'Item name is required';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: AvenzoTextField(
                      controller: _quantityController,
                      label: 'Quantity *',
                      hint: '1.0',
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      prefixIcon: Icons.onetwothree_rounded,
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) return 'Required';
                        final d = double.tryParse(val);
                        if (d == null || d <= 0) return 'Must be > 0';
                        return null;
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: AvenzoTextField(
                      controller: _unitController,
                      label: 'Unit *',
                      hint: 'units, kg, liters',
                      prefixIcon: Icons.square_foot_rounded,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Text(
                'Storage Location',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildLocationOption('pantry', 'Pantry', Icons.kitchen_outlined),
                  const SizedBox(width: 8),
                  _buildLocationOption('fridge', 'Fridge', Icons.ac_unit_outlined),
                  const SizedBox(width: 8),
                  _buildLocationOption('freezer', 'Freezer', Icons.severe_cold_outlined),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Purchase Date',
                          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 6),
                        OutlinedButton.icon(
                          onPressed: () => _selectDate(context, false),
                          icon: const Icon(Icons.calendar_today, size: 16),
                          label: Text(
                            _purchaseDate == null
                                ? 'Select Date'
                                : DateFormat.yMMMd().format(_purchaseDate!),
                            style: const TextStyle(fontSize: 12),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Expiry Date',
                          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 6),
                        OutlinedButton.icon(
                          onPressed: () => _selectDate(context, true),
                          icon: const Icon(Icons.event, size: 16, color: AppColors.warning),
                          label: Text(
                            _expiryDate == null
                                ? 'Select Expiry'
                                : DateFormat.yMMMd().format(_expiryDate!),
                            style: TextStyle(
                              fontSize: 12,
                              color: _expiryDate != null ? AppColors.warning : null,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              AvenzoTextField(
                controller: _barcodeController,
                label: 'Barcode (Optional)',
                hint: 'e.g. 8901234567890',
                prefixIcon: Icons.qr_code_scanner_rounded,
              ),
              const SizedBox(height: 16),
              AvenzoTextField(
                controller: _notesController,
                label: 'Notes (Optional)',
                hint: 'e.g. Keep refrigerated after opening',
                prefixIcon: Icons.notes_rounded,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: AvenzoButton(
                  text: 'Add to Pantry',
                  icon: Icons.add_circle_outline,
                  isLoading: _isSubmitting,
                  onPressed: _submit,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLocationOption(String value, String label, IconData icon) {
    final isSelected = _storageLocation == value;
    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _storageLocation = value),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.primaryLight : AppColors.surfaceVariant,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected ? AppColors.primary : Colors.transparent,
              width: 1.5,
            ),
          ),
          child: Column(
            children: [
              Icon(
                icon,
                size: 20,
                color: isSelected ? AppColors.primary : AppColors.textSecondary,
              ),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? AppColors.primary : AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
