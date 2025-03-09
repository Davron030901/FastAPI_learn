export interface Plate {
  id: number;
  plate_number: string;
  description: string;
  deadline: string;
  is_active: boolean;
  highest_bid?: number;
}

export interface Bid {
  id: number;
  amount: number;
  plate_id: number;
  user_id: number;
  created_at: string;
}

export interface User {
  username: string;
  is_admin: boolean;
}