import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/utils/validators.dart';
import '../../../shared/widgets/avenzo_button.dart';
import '../../../shared/widgets/avenzo_text_field.dart';
import '../../../shared/widgets/error_banner.dart';
import '../providers/auth_provider.dart';

/// Consumer Registration Screen
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleRegister() {
    if (_formKey.currentState?.validate() ?? false) {
      ref.read(authNotifierProvider.notifier).register(
            email: _emailController.text.trim(),
            password: _passwordController.text,
            firstName: _firstNameController.text.trim(),
            lastName: _lastNameController.text.trim(),
            phone: _phoneController.text.trim(),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final isLoading = authState is AuthLoading;

    String? errorMessage;
    if (authState is Unauthenticated && authState.errorMessage != null) {
      errorMessage = authState.errorMessage;
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Create Account'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Join Avenzo Consumer',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Track products, reduce household waste, and receive smart expiry alerts.',
                  style: TextStyle(
                    fontSize: 14,
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 24),

                if (errorMessage != null) ...[
                  ErrorBanner(message: errorMessage),
                  const SizedBox(height: 16),
                ],

                Row(
                  children: [
                    Expanded(
                      child: AvenzoTextField(
                        controller: _firstNameController,
                        label: 'First Name',
                        hint: 'Aakash',
                        validator: (val) => Validators.required(val, 'First name'),
                        enabled: !isLoading,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: AvenzoTextField(
                        controller: _lastNameController,
                        label: 'Last Name',
                        hint: 'Desai',
                        validator: (val) => Validators.required(val, 'Last name'),
                        enabled: !isLoading,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                AvenzoTextField(
                  controller: _emailController,
                  label: 'Email Address',
                  hint: 'consumer@example.com',
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email_outlined,
                  validator: Validators.email,
                  enabled: !isLoading,
                ),
                const SizedBox(height: 16),

                AvenzoTextField(
                  controller: _phoneController,
                  label: 'Phone Number (Optional)',
                  hint: '+91 9876543210',
                  keyboardType: TextInputType.phone,
                  prefixIcon: Icons.phone_outlined,
                  validator: Validators.phone,
                  enabled: !isLoading,
                ),
                const SizedBox(height: 16),

                AvenzoTextField(
                  controller: _passwordController,
                  label: 'Password',
                  hint: 'At least 6 characters',
                  isPassword: true,
                  prefixIcon: Icons.lock_outline,
                  validator: Validators.password,
                  enabled: !isLoading,
                ),
                const SizedBox(height: 32),

                AvenzoButton(
                  text: 'Register Account',
                  isLoading: isLoading,
                  onPressed: _handleRegister,
                ),
                const SizedBox(height: 16),

                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text(
                      'Already have an account? ',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 14,
                      ),
                    ),
                    GestureDetector(
                      onTap: isLoading ? null : () => context.pop(),
                      child: const Text(
                        'Sign In',
                        style: TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
