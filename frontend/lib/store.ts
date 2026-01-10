import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, Quote } from "./api";

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      setAuth: (token, user) =>
        set({
          token,
          user,
          isAuthenticated: true,
        }),
      logout: () =>
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

interface CartItem {
  quote: Quote;
}

interface CartState {
  items: CartItem[];
  addItem: (quote: Quote) => void;
  removeItem: (quoteId: string) => void;
  clearCart: () => void;
  getTotalPrice: () => number;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (quote) =>
        set((state) => {
          // Don't add duplicates
          if (state.items.some((item) => item.quote.id === quote.id)) {
            return state;
          }
          return { items: [...state.items, { quote }] };
        }),
      removeItem: (quoteId) =>
        set((state) => ({
          items: state.items.filter((item) => item.quote.id !== quoteId),
        })),
      clearCart: () => set({ items: [] }),
      getTotalPrice: () =>
        get().items.reduce((total, item) => total + item.quote.total_price, 0),
    }),
    {
      name: "cart-storage",
    }
  )
);
