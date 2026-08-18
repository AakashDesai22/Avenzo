import 'package:equatable/equatable.dart';

/// Role model matching FastAPI RoleRead schema.
class RoleModel extends Equatable {
  final String id;
  final String name;
  final String? description;

  const RoleModel({
    required this.id,
    required this.name,
    this.description,
  });

  factory RoleModel.fromJson(Map<String, dynamic> json) {
    return RoleModel(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
    };
  }

  @override
  List<Object?> get props => [id, name, description];
}

/// User model matching FastAPI UserRead schema.
class UserModel extends Equatable {
  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final String? phone;
  final String roleId;
  final RoleModel? role;
  final String userType;
  final bool isActive;
  final DateTime? lastLoginAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  const UserModel({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    this.phone,
    required this.roleId,
    this.role,
    required this.userType,
    required this.isActive,
    this.lastLoginAt,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Check if the user is a Consumer
  bool get isConsumer =>
      userType.toLowerCase() == 'consumer' ||
      (role != null && role!.name.toUpperCase() == 'CONSUMER');

  /// Display full name
  String get fullName => '$firstName $lastName'.trim();

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      email: json['email'] as String,
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      phone: json['phone'] as String?,
      roleId: json['role_id'] as String? ?? '',
      role: json['role'] != null ? RoleModel.fromJson(json['role'] as Map<String, dynamic>) : null,
      userType: json['user_type'] as String? ?? 'consumer',
      isActive: json['is_active'] as bool? ?? true,
      lastLoginAt: json['last_login_at'] != null ? DateTime.parse(json['last_login_at'] as String) : null,
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at'] as String) : DateTime.now(),
      updatedAt: json['updated_at'] != null ? DateTime.parse(json['updated_at'] as String) : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'first_name': firstName,
      'last_name': lastName,
      'phone': phone,
      'role_id': roleId,
      'role': role?.toJson(),
      'user_type': userType,
      'is_active': isActive,
      'last_login_at': lastLoginAt?.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  @override
  List<Object?> get props => [
        id,
        email,
        firstName,
        lastName,
        phone,
        roleId,
        role,
        userType,
        isActive,
      ];
}
