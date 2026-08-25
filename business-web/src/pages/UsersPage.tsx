/**
 * AVENZO Business Web — User Management Page (ADMIN Only)
 * CRUD interface for business staff accounts and role assignments.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getUsersApi, createUserApi, deleteUserApi } from '../api/users.api';
import { User, RegisterRequest, getRoleDisplayLabel } from '../types/auth';
import { useAuth } from '../context/AuthContext';
import { Users, UserPlus, Trash2, Shield, Search, CheckCircle2, XCircle } from 'lucide-react';

export const UsersPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState<RegisterRequest>({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    user_type: 'business',
  });
  const [errorMessage, setErrorMessage] = useState('');

  const { data: usersRes, isLoading, isError } = useQuery({
    queryKey: ['usersList'],
    queryFn: () => getUsersApi(),
  });

  const createUserMutation = useMutation({
    mutationFn: (data: RegisterRequest) => createUserApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['usersList'] });
        setIsModalOpen(false);
        setFormData({
          email: '',
          password: '',
          first_name: '',
          last_name: '',
          user_type: 'business',
        });
        setErrorMessage('');
      } else {
        setErrorMessage(res.error?.message || 'Failed to create user.');
      }
    },
    onError: (err: Error) => {
      setErrorMessage(err.message || 'An error occurred while creating user.');
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: (id: string) => deleteUserApi(id),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['usersList'] });
      } else {
        alert(res.error?.message || 'Failed to delete user.');
      }
    },
  });

  const users = usersRes?.data || [];
  const filteredUsers = users.filter(
    (u) =>
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.last_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDelete = (userToDelete: User) => {
    if (userToDelete.id === currentUser?.id) {
      alert('You cannot delete your own active administrator account.');
      return;
    }
    if (window.confirm(`Are you sure you want to remove user account '${userToDelete.email}'?`)) {
      deleteUserMutation.mutate(userToDelete.id);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.email || !formData.password || !formData.first_name || !formData.last_name) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }
    createUserMutation.mutate(formData);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
            User Account Administration
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: '0.25rem 0 0' }}>
            Manage system access, business staff profiles, and administrative permissions.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.625rem 1.25rem',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            borderRadius: '0.375rem',
            border: 'none',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <UserPlus size={18} />
          Create Staff User
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          backgroundColor: '#ffffff',
          padding: '0.75rem 1rem',
          borderRadius: '0.5rem',
          border: '1px solid #e2e8f0',
        }}
      >
        <Search size={18} color="#94a3b8" />
        <input
          type="text"
          placeholder="Search users by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            border: 'none',
            outline: 'none',
            width: '100%',
            fontSize: '0.875rem',
            color: '#0f172a',
          }}
        />
      </div>

      {/* Users Table */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '0.5rem',
          border: '1px solid #e2e8f0',
          overflow: 'hidden',
        }}
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>Loading user directory...</div>
        ) : isError ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#ef4444' }}>
            Failed to load users list. Please verify your admin credentials.
          </div>
        ) : filteredUsers.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
            <Users size={36} style={{ margin: '0 auto 0.5rem', opacity: 0.5 }} />
            <p>No matching user accounts found.</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>User Profile</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Email Address</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Assigned Role</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Account Type</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: '#0f172a' }}>
                    {u.first_name} {u.last_name}
                    {u.id === currentUser?.id && (
                      <span
                        style={{
                          fontSize: '0.7rem',
                          marginLeft: '0.5rem',
                          padding: '0.125rem 0.375rem',
                          borderRadius: '0.25rem',
                          backgroundColor: '#dbeafe',
                          color: '#1e40af',
                        }}
                      >
                        (You)
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.875rem 1rem', color: '#475569' }}>{u.email}</td>
                  <td style={{ padding: '0.875rem 1rem' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.25rem',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: u.role?.name === 'ADMIN' ? '#fee2e2' : u.role?.name === 'BUSINESS_MANAGER' ? '#dbeafe' : '#f1f5f9',
                        color: u.role?.name === 'ADMIN' ? '#991b1b' : u.role?.name === 'BUSINESS_MANAGER' ? '#1e40af' : '#334155',
                      }}
                    >
                      <Shield size={12} />
                      {getRoleDisplayLabel(u.role?.name)}
                    </span>
                  </td>
                  <td style={{ padding: '0.875rem 1rem', color: '#64748b', textTransform: 'capitalize' }}>
                    {u.user_type}
                  </td>
                  <td style={{ padding: '0.875rem 1rem' }}>
                    {u.is_active ? (
                      <span style={{ color: '#16a34a', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        <CheckCircle2 size={14} /> Active
                      </span>
                    ) : (
                      <span style={{ color: '#dc2626', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        <XCircle size={14} /> Inactive
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                    {u.id !== currentUser?.id && (
                      <button
                        onClick={() => handleDelete(u)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#ef4444',
                          cursor: 'pointer',
                          padding: '0.25rem',
                        }}
                        title="Delete User"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create User Modal */}
      {isModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '0.5rem',
              padding: '2rem',
              width: '100%',
              maxWidth: '28rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            }}
          >
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 1rem', color: '#0f172a' }}>
              Create Business Staff Account
            </h3>

            {errorMessage && (
              <div
                style={{
                  padding: '0.75rem',
                  borderRadius: '0.375rem',
                  backgroundColor: '#fef2f2',
                  color: '#991b1b',
                  fontSize: '0.875rem',
                  marginBottom: '1rem',
                }}
              >
                {errorMessage}
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  First Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '0.375rem',
                    border: '1px solid #cbd5e1',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  Last Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '0.375rem',
                    border: '1px solid #cbd5e1',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '0.375rem',
                    border: '1px solid #cbd5e1',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '0.375rem',
                    border: '1px solid #cbd5e1',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '0.375rem',
                    border: '1px solid #cbd5e1',
                    backgroundColor: '#ffffff',
                    color: '#475569',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createUserMutation.isPending}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '0.375rem',
                    border: 'none',
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {createUserMutation.isPending ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
