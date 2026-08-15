/**
 * AVENZO Business Web — Supplier Types
 */

export interface Supplier {
  id: string;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  country?: string;
  is_active: boolean;
}
