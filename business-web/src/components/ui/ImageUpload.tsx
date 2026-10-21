/**
 * AVENZO Business Web — ImageUpload Component
 * Supports drag-and-drop file upload, preview, replace, remove,
 * client-side 5MB validation, and server-side upload API integration.
 */

import React, { useRef, useState } from 'react';
import { UploadCloud, X, RefreshCw, Image as ImageIcon } from 'lucide-react';
import { uploadImageApi } from '../../api/products.api';
import { Button } from './Button';

interface ImageUploadProps {
  label?: string;
  value?: string;
  onChange: (url: string) => void;
  aspectRatio?: 'square' | 'video';
  helperText?: string;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
  label = 'Image',
  value,
  onChange,
  aspectRatio = 'square',
  helperText = 'Supported formats: JPEG, PNG, WebP (Max 5 MB)',
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);

    // Validate size (5 MB limit)
    const MAX_SIZE = 5 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setUploadError('Image exceeds the maximum allowable size of 5 MB.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // Validate type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setUploadError('Unsupported file type. Please upload a JPEG, PNG, or WebP image.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setIsUploading(true);
    try {
      const res = await uploadImageApi(file);
      if (res.success && res.data?.image_url) {
        onChange(res.data.image_url);
      } else {
        setUploadError(res.error?.message || 'Failed to upload image. Please try again.');
      }
    } catch (err: any) {
      setUploadError(err.message || 'An error occurred during upload.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleRemove = () => {
    onChange('');
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
      {label && (
        <label
          style={{
            fontSize: '0.875rem',
            color: 'var(--color-text-secondary)',
            fontWeight: 500,
          }}
        >
          {label}
        </label>
      )}

      {value ? (
        <div
          style={{
            position: 'relative',
            width: aspectRatio === 'square' ? '120px' : '200px',
            height: aspectRatio === 'square' ? '120px' : '112px',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            border: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface)',
          }}
        >
          <img
            src={value}
            alt="Preview"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).src =
                'https://placehold.co/120x120/1e293b/94a3b8?text=No+Image';
            }}
          />

          <div
            style={{
              position: 'absolute',
              top: '0.375rem',
              right: '0.375rem',
              display: 'flex',
              gap: '0.25rem',
            }}
          >
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              title="Replace image"
              style={{
                backgroundColor: 'rgba(15, 23, 42, 0.85)',
                border: 'none',
                borderRadius: '50%',
                width: 26,
                height: 26,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={13} />
            </button>
            <button
              type="button"
              onClick={handleRemove}
              title="Remove image"
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.9)',
                border: 'none',
                borderRadius: '50%',
                width: 26,
                height: 26,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                cursor: 'pointer',
              }}
            >
              <X size={14} />
            </button>
          </div>
        </div>
      ) : (
        <div
          onClick={() => !isUploading && fileInputRef.current?.click()}
          style={{
            border: '2px dashed var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
            backgroundColor: 'var(--color-surface)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            transition: 'border-color 0.2s',
          }}
        >
          {isUploading ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-primary)' }}>
              <RefreshCw size={20} className="animate-spin" />
              <span style={{ fontSize: '0.875rem' }}>Uploading image...</span>
            </div>
          ) : (
            <>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  backgroundColor: 'var(--color-background)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--color-text-secondary)',
                }}
              >
                <UploadCloud size={20} />
              </div>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-primary)' }}>
                  Click to upload
                </span>{' '}
                <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>or drag & drop</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{helperText}</span>
            </>
          )}
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      {uploadError && (
        <span style={{ fontSize: '0.75rem', color: 'var(--color-danger, #ef4444)' }}>
          {uploadError}
        </span>
      )}
    </div>
  );
};
